"""Data retention / cleanup script.

Run periodically (e.g., daily cron) to purge expired records:
  python scripts/cleanup.py

Configure via env vars:
  DATA_RETENTION_VIOLATIONS_DAYS=90
  DATA_RETENTION_SCORES_DAYS=90
  DATA_RETENTION_FRAMES_DAYS=30
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config.settings import settings
from shared.models.database import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

VIOLATIONS_DAYS = int(os.getenv("DATA_RETENTION_VIOLATIONS_DAYS", "90"))
SCORES_DAYS = int(os.getenv("DATA_RETENTION_SCORES_DAYS", "90"))
FRAMES_DAYS = int(os.getenv("DATA_RETENTION_FRAMES_DAYS", "30"))


def cleanup_violations(db) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=VIOLATIONS_DAYS)
    from shared.models.violations import Violation

    result = db.query(Violation).filter(Violation.timestamp < cutoff).delete()
    db.commit()
    logger.info("Purged %d violations older than %d days", result, VIOLATIONS_DAYS)
    return result


def cleanup_scores(db) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SCORES_DAYS)
    try:
        from shared.models.congestion import CongestionScore

        result = db.query(CongestionScore).filter(CongestionScore.timestamp < cutoff).delete()
        db.commit()
        logger.info("Purged %d congestion scores older than %d days", result, SCORES_DAYS)
        return result
    except ImportError:
        logger.warning("CongestionScore model not available, skipping")
        return 0


def cleanup_logs(db) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SCORES_DAYS)
    try:
        from shared.models.enforcement import EnforcementLog

        result = db.query(EnforcementLog).filter(EnforcementLog.timestamp < cutoff).delete()
        db.commit()
        logger.info("Purged %d enforcement logs older than %d days", result, SCORES_DAYS)
        return result
    except ImportError:
        logger.warning("EnforcementLog model not available, skipping")
        return 0


def main():
    logger.info(
        "Starting data cleanup (violations>%dd, scores>%dd, frames>%dd)",
        VIOLATIONS_DAYS, SCORES_DAYS, FRAMES_DAYS,
    )
    db = get_session()
    try:
        total = 0
        total += cleanup_violations(db)
        total += cleanup_scores(db)
        total += cleanup_logs(db)
        logger.info("Cleanup complete — %d total records purged", total)
    except Exception:
        logger.exception("Cleanup failed")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
