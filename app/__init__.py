import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Global extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")
cache = Cache()


def create_app(config_name=None):
    """
    Application factory for Public Shop.

    This function:
    - Creates and configures the Flask app.
    - Initializes SQLAlchemy, Flask-Login, Flask-Migrate.
    - Registers blueprints.
    - Sets up error handlers and logging.

    Args:
        config_name: Configuration name (development, production, testing).
                    If None, uses FLASK_ENV environment variable or 'default'.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    from app.config import config

    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Ensure instance folder exists (useful for SQLite file DBs).
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Configure Flask-Login to not regenerate session on login
    # This prevents CSRF token invalidation when logging in from multiple places
    login_manager.session_protection = (
        "basic"  # Instead of "strong" which regenerates session
    )

    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    socketio.init_app(
        app, cors_allowed_origins=app.config.get("SOCKETIO_CORS_ALLOWED_ORIGINS", "*")
    )

    # Make extensions available
    app.extensions["limiter"] = limiter

    # Configure logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        app.logger.setLevel(logging.INFO)

    # Import models so that SQLAlchemy is aware of them
    from app import models  # noqa: F401
    from app.models import User  # noqa: F401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.messages import messages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(messages_bp)

    # Apply rate limiting to specific routes after registration
    from functools import wraps

    original_register = app.view_functions["auth.register"]
    original_login = app.view_functions["auth.login"]
    original_send_message = app.view_functions.get("main.send_message")
    original_get_messages = app.view_functions.get("main.get_messages")

    @wraps(original_register)
    @limiter.limit("5 per minute")
    def rate_limited_register(*args, **kwargs):
        return original_register(*args, **kwargs)

    @wraps(original_login)
    @limiter.limit("10 per minute")
    def rate_limited_login(*args, **kwargs):
        return original_login(*args, **kwargs)

    app.view_functions["auth.register"] = rate_limited_register
    app.view_functions["auth.login"] = rate_limited_login

    if original_send_message:

        @wraps(original_send_message)
        @limiter.limit("30 per minute")
        def rate_limited_send_message(*args, **kwargs):
            return original_send_message(*args, **kwargs)

        app.view_functions["main.send_message"] = rate_limited_send_message

    # Add rate limiting for message polling endpoint (higher limit for polling)
    # Polling happens every 2 seconds = 30 requests per minute, so 120 per minute gives buffer
    if original_get_messages:

        @wraps(original_get_messages)
        @limiter.limit("120 per minute")
        def rate_limited_get_messages(*args, **kwargs):
            return original_get_messages(*args, **kwargs)

        app.view_functions["main.get_messages"] = rate_limited_get_messages

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Context processor to add unread message count to all templates
    @app.context_processor
    def inject_unread_count():
        from flask_login import current_user

        from app.models import Conversation, Message

        unread_count = 0
        try:
            if current_user.is_authenticated:
                # Count unread messages where current_user is the recipient
                unread_count = (
                    Message.query.join(Conversation)
                    .filter(
                        (
                            (Conversation.buyer_id == current_user.id)
                            | (Conversation.seller_id == current_user.id)
                        ),
                        Message.sender_id != current_user.id,
                        Message.is_read == False,
                    )
                    .count()
                )
        except Exception:
            # If there's any error (e.g., database not initialized), return 0
            unread_count = 0
        return dict(unread_count=unread_count)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses."""
        if not app.debug:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        from flask import render_template

        app.logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template

        return render_template("errors/403.html"), 403

    # Request size limit handler
    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import flash, redirect, request, url_for

        flash("File too large. Please upload a smaller file.", "error")
        return redirect(request.referrer or url_for("main.index")), 413

    # Note: Database tables are created via migrations (flask db upgrade)
    # db.create_all() is only used for testing environments
    # In development, run: flask db upgrade
    if app.config.get("TESTING"):
        with app.app_context():
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(f"Could not create tables (may already exist): {e}")

    return app, socketio
