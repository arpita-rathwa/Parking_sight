import json
import os
import signal
import sys

import lightgbm as lgb
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer

_model_path = os.path.join(os.path.dirname(__file__), "..", "model", "model.txt")
try:
    model = lgb.Booster(model_file=_model_path)
except Exception as e:
    raise RuntimeError(f"Failed to load model from {_model_path}: {e}")

FEATURE_COLS = [
    "raw_count", "centroid_lat", "centroid_lon", "police_station",
    "junction_name", "n_unique_devices", "n_unique_vehicles",
    "pct_approved", "pct_weekend", "mode_hour", "hour_std"
]

TOPIC_RAW    = "parking.violations.raw"
TOPIC_SCORED = "parking.hotspots.scored"

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: str(k).encode("utf-8") if k else None,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

consumer = KafkaConsumer(
    TOPIC_RAW,
    bootstrap_servers="localhost:9092",
    group_id="hotspot-scorer",
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
)

def publish_violation(event: dict):
    future = producer.send(TOPIC_RAW, key=event.get("cluster_id"), value=event)
    future.get(timeout=10)

def consume_and_score():
    print(f"Listening on '{TOPIC_RAW}'... (Ctrl+C to stop)")
    try:
        for msg in consumer:
            raw = msg.value
            row = pd.DataFrame([raw])
            row["police_station"] = row["police_station"].astype("category")
            row["junction_name"]  = row["junction_name"].astype("category")
            score = float(model.predict(row[FEATURE_COLS])[0])
            tier  = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")
            result = {**raw, "impact_score": round(score, 4), "priority_tier": tier}
            producer.send(TOPIC_SCORED, key=raw["cluster_id"], value=result)
            print(f"Scored cluster {raw['cluster_id']}: {score:.2f} ({tier})")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.close()

def handle_sigterm(signum, frame):
    consumer.close()
    producer.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    consume_and_score()