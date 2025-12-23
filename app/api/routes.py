"""
API routes for Public Shop.
"""

from flask import jsonify, request
from flask_login import current_user, login_required
from flask_restful import Api, Resource, reqparse

from app import db
from app.api import api_bp
from app.models import Conversation, Listing, Message, Post, User

api = Api(api_bp)

# Request parsers
listing_parser = reqparse.RequestParser()
listing_parser.add_argument("title", type=str, required=True, help="Title is required")
listing_parser.add_argument("description", type=str)
listing_parser.add_argument(
    "price", type=float, required=True, help="Price is required"
)
listing_parser.add_argument(
    "category", type=str, required=True, help="Category is required"
)

message_parser = reqparse.RequestParser()
message_parser.add_argument(
    "content", type=str, required=True, help="Message content is required"
)


class UserResource(Resource):
    """User API resource."""

    @login_required
    def get(self, user_id=None):
        """Get user(s) information."""
        if user_id:
            user = User.query.get_or_404(user_id)
            return {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "bio": user.bio,
                "avatar_filename": user.avatar_filename,
                "created_at": user.created_at.isoformat(),
                "followers_count": user.followers.count(),
                "following_count": user.followed.count(),
            }
        else:
            users = User.query.limit(50).all()
            return {
                "users": [
                    {
                        "id": u.id,
                        "display_name": u.display_name,
                        "avatar_filename": u.avatar_filename,
                    }
                    for u in users
                ]
            }


class ListingResource(Resource):
    """Listing API resource."""

    def get(self, listing_id=None):
        """Get listing(s)."""
        if listing_id:
            listing = Listing.query.get_or_404(listing_id)
            return {
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "category": listing.category,
                "image_filename": listing.image_filename,
                "seller_id": listing.seller_id,
                "seller_name": listing.seller.display_name,
                "created_at": listing.created_at.isoformat(),
                "expires_at": (
                    listing.expires_at.isoformat() if listing.expires_at else None
                ),
            }
        else:
            listings = Listing.query.filter_by(status="active").limit(50).all()
            return {
                "listings": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "price": l.price,
                        "category": l.category,
                        "image_filename": l.image_filename,
                    }
                    for l in listings
                ]
            }

    @login_required
    def post(self):
        """Create a new listing."""
        args = listing_parser.parse_args()

        listing = Listing(
            seller=current_user,
            title=args["title"],
            description=args.get("description"),
            price=args["price"],
            category=args["category"],
            status="active",
        )
        db.session.add(listing)
        db.session.commit()

        return {
            "id": listing.id,
            "title": listing.title,
            "message": "Listing created successfully",
        }, 201


class MessageResource(Resource):
    """Message API resource."""

    @login_required
    def post(self, conversation_id):
        """Send a message in a conversation."""
        conversation = Conversation.query.get_or_404(conversation_id)

        if current_user.id not in (conversation.buyer_id, conversation.seller_id):
            return {"error": "Unauthorized"}, 403

        args = message_parser.parse_args()

        message = Message(
            conversation=conversation,
            sender=current_user,
            content=args["content"],
        )
        db.session.add(message)
        conversation.updated_at = message.created_at
        db.session.commit()

        # Emit socketio event for real-time updates
        from app import socketio

        socketio.emit(
            "new_message",
            {
                "conversation_id": conversation_id,
                "message_id": message.id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            },
            room=f"conversation_{conversation_id}",
        )

        return {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "created_at": message.created_at.isoformat(),
        }, 201


# Register API resources
api.add_resource(UserResource, "/users", "/users/<int:user_id>")
api.add_resource(ListingResource, "/listings", "/listings/<int:listing_id>")
api.add_resource(MessageResource, "/conversations/<int:conversation_id>/messages")
