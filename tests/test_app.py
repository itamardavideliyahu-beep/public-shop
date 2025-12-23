"""
Basic unit tests for the Flask application.
These tests don't require a running server.
"""

import pytest
from app import create_app, db
from app.models import User, Listing


@pytest.fixture
def app():
    """Create application for testing."""
    app, socketio = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_app_exists(app):
    """Test that the app exists."""
    assert app is not None


def test_app_is_testing(app):
    """Test that the app is in testing mode."""
    assert app.config["TESTING"]


def test_home_page(client):
    """Test that the home page loads."""
    response = client.get("/")
    assert response.status_code == 200


def test_login_page(client):
    """Test that the login page loads."""
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_page(client):
    """Test that the register page loads."""
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_user_model():
    """Test User model creation."""
    user = User(email="test@example.com", display_name="Test User")
    user.set_password("password123")
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.check_password("password123")
    assert not user.check_password("wrongpassword")


def test_listing_model():
    """Test Listing model creation."""
    listing = Listing(
        title="Test Item",
        description="Test description",
        price=99.99,
        category="electronics",
        status="active",
    )
    assert listing.title == "Test Item"
    assert listing.price == 99.99
    assert listing.category == "electronics"
    assert listing.status == "active"

