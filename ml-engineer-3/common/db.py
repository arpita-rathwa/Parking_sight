"""Database engine + session helpers. Works with SQLite (demo) or Postgres (prod)."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from common.config import get_settings
from common.models import Base

_settings = get_settings()
_engine = create_engine(_settings.database_url, future=True)


# SQLite ignores foreign keys unless told otherwise. Turn them ON so the demo
# enforces the same constraints Postgres does (and would catch FK-ordering bugs).
if _engine.dialect.name == "sqlite":

    @event.listens_for(_engine, "connect")
    def _fk_pragma(dbapi_con, _):  # pragma: no cover
        dbapi_con.execute("PRAGMA foreign_keys=ON")


_SessionFactory = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False)


def init_db() -> None:
    """Create all ML-platform tables (idempotent)."""
    Base.metadata.create_all(_engine)


@contextmanager
def session_scope():
    s = _SessionFactory()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
