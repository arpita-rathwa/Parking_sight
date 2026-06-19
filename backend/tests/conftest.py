import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.database import Base, get_db
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "postgresql+psycopg2://parksight:parksight@localhost:5432/parksight_test"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
