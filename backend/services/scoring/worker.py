import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from shared.config.settings import settings
from shared.kafka.consumer import create_consumer
from shared.kafka.producer import producer
from shared.kafka.topics import KAFKA_TOPICS
from services.scoring.ml_model.engine import get_scoring_engine

logger = logging.getLogger("scoring-worker")

SCORING_INTERVAL_SECONDS = 60
SCORING_WINDOW_MINUTES = 15
CAMERA_CACHE_TTL = 300


class ScoringWorker:
    def __init__(self):
        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._running = False
        self._camera_zone_cache: dict[str, str] = {}
        self._last_cache_refresh = 0.0

    def start(self):
        self._running = True
        threading.Thread(target=self._consume_loop, daemon=True, name="scoring-consume").start()
        threading.Thread(target=self._compute_loop, daemon=True, name="scoring-compute").start()
        logger.info("Scoring worker started")

    def stop(self):
        self._running = False

    def _refresh_camera_cache(self):
        now = time.time()
        if now - self._last_cache_refresh < CAMERA_CACHE_TTL:
            return
        from shared.models.database import get_session
        from shared.models.cameras import Camera
        db = get_session()
        try:
            cameras = db.query(Camera).all()
            self._camera_zone_cache = {str(c.id): str(c.zone_id) for c in cameras}
            self._last_cache_refresh = now
            logger.info("Refreshed camera→zone cache: %d cameras", len(cameras))
        except Exception:
            logger.warning("Failed to refresh camera cache")
        finally:
            db.close()

    def _consume_loop(self):
        consumer = create_consumer(KAFKA_TOPICS["violations_raw"], "scoring-group")
        try:
            for msg in consumer:
                if not self._running:
                    break
                with self._lock:
                    self._buffer.append(msg.value)
        except Exception:
            logger.exception("Consumer error")
        finally:
            consumer.close()

    def _compute_loop(self):
        while self._running:
            time.sleep(SCORING_INTERVAL_SECONDS)
            try:
                self._refresh_camera_cache()
                self._compute_scores()
            except Exception:
                logger.exception("Score computation failed")

    def _compute_scores(self):
        with self._lock:
            batch = self._buffer[:]
            self._buffer.clear()

        if not batch:
            return

        cutoff = datetime.now(timezone.utc).timestamp() - SCORING_WINDOW_MINUTES * 60
        recent = [v for v in batch if self._get_ts(v) >= cutoff]

        zone_counts: dict[str, list[float]] = defaultdict(list)
        unresolved = []
        for v in recent:
            zone_id = self._resolve_zone(v)
            if zone_id:
                zone_counts[zone_id].append(v.get("confidence", 0.5))
            else:
                unresolved.append(v)

        if unresolved:
            self._batch_resolve_zones(unresolved, zone_counts)

        if not zone_counts:
            return

        max_count = max(len(c) for c in zone_counts.values()) or 1
        now = datetime.now(timezone.utc)
        engine = get_scoring_engine()
        from shared.models.database import get_session
        from shared.models.congestion_scores import CongestionScore

        db = get_session()
        try:
            for zone_id, confs in zone_counts.items():
                violation_count = len(confs)
                zone_data = {
                    "violation_count": violation_count,
                    "max_zone_count": max_count,
                    "lat": 0.0,
                    "lon": 0.0,
                    "n_unique_devices": max(1, violation_count),
                    "pct_approved": 0.5,
                    "pct_weekend": 0.3,
                    "mode_hour": 14,
                    "hour_std": 3.0,
                }
                impact_score = engine.predict_impact(zone_data)
                speed_drop = round(sum(confs) / len(confs) * 20, 2) if confs else 0.0

                score = CongestionScore(
                    id=uuid.uuid4(),
                    zone_id=uuid.UUID(zone_id),
                    timestamp=now,
                    impact_score=impact_score,
                    violation_count=violation_count,
                    speed_drop_percent=speed_drop,
                    traffic_density=impact_score / 100,
                    weather_factor=1.0,
                )
                db.add(score)

                event = {
                    "zone_id": zone_id,
                    "timestamp": now.isoformat(),
                    "impact_score": impact_score,
                    "violation_count": violation_count,
                    "speed_drop_percent": speed_drop,
                }
                producer.send(KAFKA_TOPICS["zones_scored"], key=zone_id, value=event)

            db.commit()
            logger.info("Scored %d zones (%d violations)", len(zone_counts), len(recent))
        except Exception:
            db.rollback()
            logger.exception("Failed to persist congestion scores")
            raise
        finally:
            db.close()

    def _get_ts(self, v: dict) -> float:
        ts = v.get("timestamp")
        if isinstance(ts, (int, float)):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts).timestamp()
            except ValueError:
                pass
        return time.time()

    def _resolve_zone(self, v: dict) -> str | None:
        camera_id = v.get("camera_id")
        if camera_id and camera_id in self._camera_zone_cache:
            return self._camera_zone_cache[camera_id]
        zone_id = v.get("zone_id")
        if zone_id:
            return zone_id
        return None

    def _batch_resolve_zones(self, violations: list[dict], zone_counts: dict[str, list[float]]):
        from shared.models.database import get_session
        from shared.models.zones import Zone
        from geoalchemy2.functions import ST_Within
        from geoalchemy2 import WKTElement

        db = get_session()
        try:
            all_zones = db.query(Zone).all()
            zone_polys = [(str(z.id), z.boundary) for z in all_zones]
            for v in violations:
                lat = v.get("latitude")
                lon = v.get("longitude")
                if not lat or not lon:
                    continue
                point = WKTElement(f"POINT({lon} {lat})", srid=4326)
                for zid, boundary in zone_polys:
                    if db.query(ST_Within(point, boundary)).scalar():
                        zone_counts[zid].append(v.get("confidence", 0.5))
                        break
        except Exception:
            logger.warning("Batch zone resolution failed for %d violations", len(violations))
        finally:
            db.close()


_worker: ScoringWorker | None = None


def start_worker():
    global _worker
    _worker = ScoringWorker()
    _worker.start()


def stop_worker():
    global _worker
    if _worker:
        _worker.stop()
