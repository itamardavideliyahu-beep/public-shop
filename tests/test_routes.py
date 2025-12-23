"""
Tests for application routes and endpoints.
"""

import pytest

from app import create_app, db
from app.models import Listing, User


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


@pytest.fixture
def authenticated_user(app):
    """Create and return an authenticated user."""
    with app.app_context():
        user = User(
            email="test@example.com",
            display_name="Test User",
            username="testuser",
            email_verified=True,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user


class TestPublicRoutes:
    """Tests for public routes."""

    def test_index_page(self, client):
        """Test home page loads."""
        response = client.get("/")
        assert response.status_code == 200

    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get("/auth/register")
        assert response.status_code == 200

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "database" in data
        assert data["status"] in ["ok", "degraded"]


class TestAuthenticationRoutes:
    """Tests for authentication routes."""

    def test_login_with_valid_credentials(self, client, app, authenticated_user):
        """Test login with valid credentials."""
        response = client.post(
            "/auth/login",
            data={"email": "test@example.com", "password": "password123"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_login_with_invalid_credentials(self, client, app, authenticated_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={"email": "test@example.com", "password": "wrongpassword"},
            follow_redirects=True,
        )

        assert response.status_code == 200


class TestProtectedRoutes:
    """Tests for protected routes that require authentication."""

    def test_dashboard_requires_login(self, client):
        """Test that dashboard redirects to login if not authenticated."""
        response = client.get("/dashboard")
        assert response.status_code == 302  # Redirect

    def test_conversations_requires_login(self, client):
        """Test that conversations page requires login."""
        response = client.get("/conversations")
        assert response.status_code == 302  # Redirect

    def test_edit_profile_requires_login(self, client):
        """Test that edit profile requires login."""
        response = client.get("/settings/profile")
        assert response.status_code == 302  # Redirect


class TestListingRoutes:
    """Tests for listing-related routes."""

    def test_view_listing_detail(self, client, app, authenticated_user):
        """Test viewing a listing detail page."""
        with app.app_context():
            listing = Listing(
                seller=authenticated_user,
                title="Test Item",
                description="Test description",
                price=99.99,
                category="electronics",
                status="active",
            )
            db.session.add(listing)
            db.session.commit()
            listing_id = listing.id

        response = client.get(f"/listing/{listing_id}")
        assert response.status_code == 200


class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_page(self, client):
        """Test 404 error page."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_health_check_response(self, client):
        """Test health check returns proper JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "timestamp" in data
