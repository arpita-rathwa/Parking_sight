from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from shared.config.settings import settings

Base = declarative_base()


def get_engine():
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )


def get_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()
