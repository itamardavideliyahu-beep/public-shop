"""
SocketIO event handlers for real-time features.
"""

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Conversation, Message


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        emit(
            "connected",
            {"user_id": current_user.id, "message": "Connected to real-time chat"},
        )
    else:
        emit("error", {"message": "Authentication required"})
        return False


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    if current_user.is_authenticated:
        emit("disconnected", {"user_id": current_user.id})


@socketio.on("join_conversation")
def handle_join_conversation(data):
    """Join a conversation room for real-time updates."""
    if not current_user.is_authenticated:
        emit("error", {"message": "Authentication required"})
        return

    conversation_id = data.get("conversation_id")
    conversation = Conversation.query.get(conversation_id)

    if conversation and current_user.id in (
        conversation.buyer_id,
        conversation.seller_id,
    ):
        room = f"conversation_{conversation_id}"
        join_room(room)
        emit("joined", {"conversation_id": conversation_id, "room": room})
    else:
        emit("error", {"message": "Conversation not found or unauthorized"})


@socketio.on("leave_conversation")
def handle_leave_conversation(data):
    """Leave a conversation room."""
    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    room = f"conversation_{conversation_id}"
    leave_room(room)
    emit("left", {"conversation_id": conversation_id})


@socketio.on("typing")
def handle_typing(data):
    """Handle typing indicator."""
    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    conversation = Conversation.query.get(conversation_id)

    if conversation and current_user.id in (
        conversation.buyer_id,
        conversation.seller_id,
    ):
        room = f"conversation_{conversation_id}"
        emit(
            "user_typing",
            {
                "user_id": current_user.id,
                "user_name": current_user.display_name,
                "typing": data.get("typing", False),
            },
            room=room,
            include_self=False,
        )
