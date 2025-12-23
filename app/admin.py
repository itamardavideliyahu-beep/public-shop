"""
Flask-Admin configuration for Public Shop.
"""

from flask import redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app import db
from app.models import Conversation, Listing, Message, Post, User


class SecureAdminIndexView(AdminIndexView):
    """Secure admin index view that requires authentication."""

    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        # Check if user is admin (you can add an is_admin field to User model)
        # For now, allow any authenticated user
        return super().index()


class SecureModelView(ModelView):
    """Base model view with authentication."""

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login"))


class UserAdminView(SecureModelView):
    """Admin view for User model."""

    column_list = ["id", "email", "display_name", "created_at", "mfa_enabled"]
    column_searchable_list = ["email", "display_name"]
    column_filters = ["created_at", "mfa_enabled", "region"]
    form_columns = ["email", "display_name", "bio", "region", "mfa_enabled"]


class ListingAdminView(SecureModelView):
    """Admin view for Listing model."""

    column_list = [
        "id",
        "title",
        "price",
        "category",
        "status",
        "seller",
        "created_at",
        "expires_at",
    ]
    column_searchable_list = ["title", "description"]
    column_filters = ["category", "status", "created_at"]
    form_columns = [
        "title",
        "description",
        "price",
        "category",
        "status",
        "seller",
        "expires_at",
    ]


class PostAdminView(SecureModelView):
    """Admin view for Post model."""

    column_list = ["id", "author", "content", "created_at"]
    column_searchable_list = ["content"]
    column_filters = ["created_at"]


class ConversationAdminView(SecureModelView):
    """Admin view for Conversation model."""

    column_list = ["id", "buyer", "seller", "listing", "created_at", "updated_at"]
    column_filters = ["created_at"]


class MessageAdminView(SecureModelView):
    """Admin view for Message model."""

    column_list = ["id", "conversation", "sender", "content", "created_at", "is_read"]
    column_searchable_list = ["content"]
    column_filters = ["created_at", "is_read"]


def setup_admin(app):
    """Setup Flask-Admin."""
    admin = Admin(
        app,
        name="Public Shop Admin",
        template_mode="bootstrap4",
        index_view=SecureAdminIndexView(),
    )

    admin.add_view(UserAdminView(User, db.session, name="Users", category="Models"))
    admin.add_view(
        ListingAdminView(Listing, db.session, name="Listings", category="Models")
    )
    admin.add_view(PostAdminView(Post, db.session, name="Posts", category="Models"))
    admin.add_view(
        ConversationAdminView(
            Conversation, db.session, name="Conversations", category="Models"
        )
    )
    admin.add_view(
        MessageAdminView(Message, db.session, name="Messages", category="Models")
    )
