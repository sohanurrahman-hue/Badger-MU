"""
Pytest configuration and fixtures
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_badge_engine"

from backend.api.main import app
from backend.db.base import Base
from backend.db import get_db


# Test database engine
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_badge_engine"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with database override
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_entra_token():
    """Mock Entra ID JWT token"""
    return "mock.jwt.token"


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "name": "Test User",
        "groups": ["Issuers", "Badge Admins"]
    }


@pytest.fixture
def admin_user():
    """Mock admin user"""
    return {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "admin@example.com",
        "name": "Admin User",
        "groups": ["Badge Admins"]
    }


@pytest.fixture
def issuer_user():
    """Mock issuer user"""
    return {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "issuer@example.com",
        "name": "Issuer User",
        "groups": ["Issuers"]
    }


@pytest.fixture
def sample_achievement():
    """Sample achievement data"""
    return {
        "iri": "https://example.com/achievement/test",
        "type": ["Achievement"],
        "name": "Test Achievement",
        "description": "A test achievement",
        "criteria": {
            "narrative": "Complete the test"
        }
    }


@pytest.fixture
def sample_credential():
    """Sample OpenBadgeCredential"""
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
        ],
        "id": "https://example.com/credentials/test",
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": {
            "id": "https://example.com/issuers/test",
            "type": ["Profile"],
            "name": "Test Issuer"
        },
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["AchievementSubject"],
            "achievement": {
                "id": "https://example.com/achievements/test",
                "type": ["Achievement"],
                "name": "Test Achievement"
            }
        }
    }

