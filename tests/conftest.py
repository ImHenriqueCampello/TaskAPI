import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Determine default test database URL
DEFAULT_TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tasks_test"
)

# Maintenance URL to create tasks_test if not exists
MAINTENANCE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)
# Make sure maintenance connects to 'postgres' or default db rather than nonexistent db
if "/tasks_test" in MAINTENANCE_URL:
    MAINTENANCE_URL = MAINTENANCE_URL.rsplit("/", 1)[0] + "/postgres"

# Ensure tasks_test exists
def _ensure_test_db_exists(test_url: str):
    db_name = test_url.rsplit("/", 1)[-1].split("?")[0]
    maintenance_url = test_url.rsplit("/", 1)[0] + "/postgres"
    try:
        m_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
        with m_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        m_engine.dispose()
    except Exception:
        # If connecting to /postgres failed, try default maintenance URL or assume DB exists
        pass

_ensure_test_db_exists(DEFAULT_TEST_URL)

# Force DATABASE_URL to test DB before importing app
os.environ["DATABASE_URL"] = DEFAULT_TEST_URL

from app.database import Base, get_db
from app.main import app

test_engine = create_engine(DEFAULT_TEST_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create all tables in test database
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up at end of test session if desired


@pytest.fixture(autouse=True)
def clean_db():
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE;"))
        conn.commit()
    yield
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE;"))
        conn.commit()


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
