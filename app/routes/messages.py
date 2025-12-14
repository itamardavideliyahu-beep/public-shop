from flask import Blueprint

# Messages blueprint for future messaging / conversations features.
# For now this is just a minimal placeholder so the app can import and register it.
messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
