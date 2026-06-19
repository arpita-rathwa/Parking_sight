import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = (
    "postgresql+psycopg2://parksight:parksight@localhost:5432/parksight_test"
)


@pytest.fixture(scope="session")
def test_engine():
    try:
        from shared.models.database import Base

        engine = create_engine(TEST_DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)
    except ImportError:
        pytest.skip("Database dependencies not available")
        yield None


@pytest.fixture(scope="function")
def test_db(test_engine):
    if test_engine is None:
        pytest.skip("No database engine")
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
