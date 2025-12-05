import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine using PostgreSQL from Docker."""
    # Use test database URL from environment or default to Docker setup
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://crm_user:crm_password@db:5432/crm_test"
    )
    
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for a test with transaction rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()