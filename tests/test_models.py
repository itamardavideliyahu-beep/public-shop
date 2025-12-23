"""
Comprehensive unit tests for database models.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, db
from app.models import Conversation, EmailVerification, Listing, Message, Post, User


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


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                email="test@example.com", display_name="Test User", username="testuser"
            )
            user.set_password("password123")

            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.email == "test@example.com"
            assert user.display_name == "Test User"
            assert user.username == "testuser"
            assert user.check_password("password123")
            assert not user.check_password("wrongpassword")

    def test_user_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User(email="test@example.com", display_name="Test")
            user.set_password("mypassword")

            assert user.password_hash != "mypassword"
            assert user.check_password("mypassword")
            assert not user.check_password("different")

    def test_user_follow_system(self, app):
        """Test following/unfollowing users."""
        with app.app_context():
            user1 = User(
                email="user1@test.com", display_name="User 1", username="user1"
            )
            user1.set_password("password123")
            user2 = User(
                email="user2@test.com", display_name="User 2", username="user2"
            )
            user2.set_password("password123")

            db.session.add_all([user1, user2])
            db.session.commit()

            # Test following
            assert not user1.is_following(user2)
            user1.follow(user2)
            db.session.commit()
            assert user1.is_following(user2)

            # Test unfollowing
            user1.unfollow(user2)
            db.session.commit()
            assert not user1.is_following(user2)

    def test_user_email_unique(self, app):
        """Test that email must be unique."""
        with app.app_context():
            user1 = User(email="test@test.com", display_name="User 1")
            user1.set_password("password123")
            db.session.add(user1)
            db.session.commit()

            user2 = User(email="test@test.com", display_name="User 2")
            db.session.add(user2)

            with pytest.raises(Exception):
                db.session.commit()


class TestListingModel:
    """Tests for Listing model."""

    def test_listing_creation(self, app):
        """Test creating a new listing."""
        with app.app_context():
            user = User(email="seller@test.com", display_name="Seller")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            listing = Listing(
                seller=user,
                title="Test Item",
                description="Test description",
                price=99.99,
                category="electronics",
                status="active",
            )
            db.session.add(listing)
            db.session.commit()

            assert listing.id is not None
            assert listing.title == "Test Item"
            assert listing.price == 99.99
            assert listing.category == "electronics"
            assert listing.seller_id == user.id

    def test_listing_expiration(self, app):
        """Test listing expiration date."""
        with app.app_context():
            user = User(email="seller@test.com", display_name="Seller")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            # Use naive datetime for compatibility with SQLite
            now = datetime.utcnow()
            expires_at = now + timedelta(days=30)
            listing = Listing(
                seller=user,
                title="Expiring Item",
                price=50.00,
                category="other",
                expires_at=expires_at,
            )
            db.session.add(listing)
            db.session.commit()

            assert listing.expires_at is not None
            # Compare with the same naive datetime
            assert listing.expires_at > now

    def test_free_listing(self, app):
        """Test free listing (giveaway)."""
        with app.app_context():
            user = User(email="seller@test.com", display_name="Seller")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            listing = Listing(
                seller=user,
                title="Free Item",
                price=0.0,
                category="other",
                is_free=True,
            )
            db.session.add(listing)
            db.session.commit()

            assert listing.is_free is True
            assert listing.price == 0.0


class TestConversationModel:
    """Tests for Conversation and Message models."""

    def test_conversation_creation(self, app):
        """Test creating a conversation."""
        with app.app_context():
            buyer = User(email="buyer@test.com", display_name="Buyer")
            buyer.set_password("password123")
            seller = User(email="seller@test.com", display_name="Seller")
            seller.set_password("password123")
            db.session.add_all([buyer, seller])
            db.session.commit()

            listing = Listing(seller=seller, title="Item", price=100, category="other")
            db.session.add(listing)
            db.session.commit()

            conversation = Conversation(buyer=buyer, seller=seller, listing=listing)
            db.session.add(conversation)
            db.session.commit()

            assert conversation.id is not None
            assert conversation.buyer_id == buyer.id
            assert conversation.seller_id == seller.id
            assert conversation.listing_id == listing.id

    def test_message_creation(self, app):
        """Test creating messages in a conversation."""
        with app.app_context():
            buyer = User(email="buyer@test.com", display_name="Buyer")
            buyer.set_password("password123")
            seller = User(email="seller@test.com", display_name="Seller")
            seller.set_password("password123")
            db.session.add_all([buyer, seller])
            db.session.commit()

            conversation = Conversation(buyer=buyer, seller=seller)
            db.session.add(conversation)
            db.session.commit()

            message = Message(
                conversation=conversation,
                sender=buyer,
                content="Hello, is this available?",
            )
            db.session.add(message)
            db.session.commit()

            assert message.id is not None
            assert message.content == "Hello, is this available?"
            assert message.sender_id == buyer.id
            assert not message.is_read


class TestEmailVerification:
    """Tests for EmailVerification model."""

    def test_verification_creation(self, app):
        """Test creating email verification."""
        with app.app_context():
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            verification = EmailVerification(
                email="test@test.com",
                verification_code="123456",
                username="testuser",
                display_name="Test User",
                password_hash="hashed",
                expires_at=expires_at,
            )
            db.session.add(verification)
            db.session.commit()

            assert verification.id is not None
            assert verification.email == "test@test.com"
            assert verification.verification_code == "123456"
            assert not verification.verified
