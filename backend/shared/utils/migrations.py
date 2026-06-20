import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger("parksight.migrations")

ALEMBIC_CFG_PATH = Path(__file__).resolve().parents[2] / "alembic.ini"


def run_migrations():
    if not ALEMBIC_CFG_PATH.exists():
        logger.warning(
            "alembic.ini not found at %s — skipping migrations", ALEMBIC_CFG_PATH
        )
        return
    cfg = Config(str(ALEMBIC_CFG_PATH))
    command.upgrade(cfg, "head")
    logger.info("Migrations up to date")
