from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


# Association table for "follow" relationships between users
followers = db.Table(
    "followers",
    db.Column(
        "follower_id",
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True,
    ),
    db.Column(
        "followed_id",
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True,
    ),
)


class User(db.Model, UserMixin):
    """
    Application user.

    Represents a person that can log in, create stories (posts),
    create offers (listings), and send messages in conversations.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=True, index=True)  # Unique username for search
    display_name = db.Column(db.String(80), nullable=False)

    # Optional profile fields
    avatar_filename = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(50), nullable=True, default="israel")  # Default to Israel
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # MFA fields (kept for backward compatibility, but not used in registration)
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(32), nullable=True)  # TOTP secret

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships: content
    posts = db.relationship(
        "Post",
        back_populates="author",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    listings = db.relationship(
        "Listing",
        back_populates="seller",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Follow relationships:
    # "followed" = users that this user follows
    # "followers" = users that follow this user (backref)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    # Conversations where this user is the buyer
    buyer_conversations = db.relationship(
        "Conversation",
        foreign_keys="Conversation.buyer_id",
        back_populates="buyer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Conversations where this user is the seller
    seller_conversations = db.relationship(
        "Conversation",
        foreign_keys="Conversation.seller_id",
        back_populates="seller",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Messages sent by this user
    messages = db.relationship(
        "Message",
        back_populates="sender",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # --- password helpers ---
    def set_password(self, plain_password: str) -> None:
        """
        Set the user's password by hashing the plain-text password.
        """
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """
        Check if the provided plain-text password matches the stored hash.
        """
        return check_password_hash(self.password_hash, plain_password)

    # --- follow helpers ---
    def follow(self, user: "User") -> None:
        """
        Follow another user if not already following.
        """
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user: "User") -> None:
        """
        Unfollow another user if currently following.
        """
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user: "User") -> bool:
        """
        Check if this user is following the given user.
        """
        if user.id is None:
            return False
        return (
            self.followed
            .filter(followers.c.followed_id == user.id)
            .count()
        ) > 0

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Post(db.Model):
    """
    Social story created by a user that appears in the social feed.
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    content = db.Column(db.Text, nullable=False)

    # Optional image path stored for this story
    image_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationship back to the author (User)
    author = db.relationship(
        "User",
        back_populates="posts",
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} author_id={self.author_id}>"


class Listing(db.Model):
    """
    Marketplace offer created by a user (seller).

    Other users will be able to view and potentially buy this item.
    """
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Optional image file name stored for this offer
    image_filename = db.Column(db.String(255), nullable=True)

    # Category of the offer (for filtering and navigation)
    # Examples: "real_estate", "cars", "electronics", etc.
    category = db.Column(
        db.String(50),
        nullable=False,
        default="other",
        index=True,
    )
    
    # Whether this listing is for free (giveaway) or for sale
    is_free = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Storing price as Numeric is usually better for money,
    # but for simplicity we use Float in this project.
    price = db.Column(db.Float, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="active",  # "active", "sold", "inactive"
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Expiration date for the offer
    expires_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True,
    )

    # Relationship back to the seller (User)
    seller = db.relationship(
        "User",
        back_populates="listings",
    )

    # Conversations related to this listing (buyer contacting seller)
    conversations = db.relationship(
        "Conversation",
        back_populates="listing",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Listing id={self.id} "
            f"title={self.title!r} "
            f"seller_id={self.seller_id} "
            f"category={self.category!r}>"
        )


class Conversation(db.Model):
    """
    One-to-one conversation between a buyer and a seller,
    usually about a specific listing.
    """
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id"),
        nullable=True,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        back_populates="buyer_conversations",
    )

    seller = db.relationship(
        "User",
        foreign_keys=[seller_id],
        back_populates="seller_conversations",
    )

    listing = db.relationship(
        "Listing",
        back_populates="conversations",
    )

    messages = db.relationship(
        "Message",
        back_populates="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation id={self.id} "
            f"buyer_id={self.buyer_id} "
            f"seller_id={self.seller_id} "
            f"listing_id={self.listing_id}>"
        )


class Message(db.Model):
    """
    Single message inside a conversation.
    """
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Relationships
    conversation = db.relationship(
        "Conversation",
        back_populates="messages",
    )

    sender = db.relationship(
        "User",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} "
            f"conversation_id={self.conversation_id} "
            f"sender_id={self.sender_id}>"
        )


class EmailVerification(db.Model):
    """
    Email verification codes for new user registrations.
    """
    __tablename__ = "email_verifications"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    verification_code = db.Column(db.String(6), nullable=False)  # 6-digit code
    username = db.Column(db.String(30), nullable=False)  # Username for new user
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    expires_at = db.Column(
        db.DateTime,
        nullable=False,
        index=True,
    )
    
    verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EmailVerification id={self.id} email={self.email!r} verified={self.verified}>"
