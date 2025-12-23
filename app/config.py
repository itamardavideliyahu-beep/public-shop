import os
from pathlib import Path


class Config:
    """
    Base configuration for the application.

    Configuration is loaded from environment variables with sensible defaults
    for development. In production, all sensitive values should be set via
    environment variables or a .env file.
    """

    # Base directory
    BASE_DIR = Path(__file__).parent.parent

    # Secret key for sessions, CSRF, etc.
    # In production, always set SECRET_KEY in the environment.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

    # SQLAlchemy settings
    # Use absolute path to avoid issues with spaces in directory names
    default_db_path = BASE_DIR / "instance" / "public_shop.db"
    # Ensure the instance directory exists
    default_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Format path for SQLite - convert to absolute path and use forward slashes
    # SQLite on Windows handles forward slashes correctly
    abs_db_path = default_db_path.resolve()
    # Use 3 slashes for absolute paths: sqlite:///C:/path/to/db
    db_uri = f"sqlite:///{abs_db_path.as_posix()}"

    # Get from environment or use default
    # Priority: DATABASE_URL from env > POSTGRES_* vars > default SQLite path
    env_db_uri = os.environ.get("DATABASE_URL")

    # Check if DATABASE_URL has password (contains :password@ or no password part)
    # If DATABASE_URL exists but doesn't have password, try to build from POSTGRES_* vars
    postgres_user = os.environ.get("POSTGRES_USER")
    postgres_password = os.environ.get("POSTGRES_PASSWORD")
    postgres_host = os.environ.get("POSTGRES_HOST")
    postgres_db = os.environ.get("POSTGRES_DB")

    if env_db_uri:
        # Check if URL has password (format: postgresql://user:password@host or postgresql://user@host)
        if "://" in env_db_uri and "@" in env_db_uri:
            # Extract user and host parts
            parts = env_db_uri.split("@", 1)
            if len(parts) == 2:
                user_part = parts[0]
                host_part = parts[1]
                # Check if password exists (user:password format)
                if "://" in user_part and ":" not in user_part.split("://")[1]:
                    # No password in URL, try to use POSTGRES_PASSWORD if available
                    if (
                        postgres_user
                        and postgres_password
                        and postgres_host
                        and postgres_db
                    ):
                        # Build URL from POSTGRES_* variables
                        SQLALCHEMY_DATABASE_URI = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}/{postgres_db}"
                        if "sslmode" in host_part:
                            SQLALCHEMY_DATABASE_URI += "?" + host_part.split("?", 1)[1]
                    else:
                        # Use DATABASE_URL as is (will fail if password required)
                        SQLALCHEMY_DATABASE_URI = env_db_uri
                else:
                    # Has password, use as is
                    SQLALCHEMY_DATABASE_URI = env_db_uri
            else:
                SQLALCHEMY_DATABASE_URI = env_db_uri
        else:
            SQLALCHEMY_DATABASE_URI = env_db_uri
    elif postgres_user and postgres_password and postgres_host and postgres_db:
        # No DATABASE_URL, but have POSTGRES_* vars - build URL
        SQLALCHEMY_DATABASE_URI = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}/{postgres_db}"
    else:
        # Use absolute path to ensure it works with spaces (SQLite default)
        SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get("SQLALCHEMY_ECHO", "False").lower() == "true"

    # File upload settings
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_UPLOAD_SIZE", 16 * 1024 * 1024)
    )  # 16MB default
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_IMAGE_SIZE = int(
        os.environ.get("MAX_IMAGE_SIZE", 5 * 1024 * 1024)
    )  # 5MB default

    # Security settings
    # Note: SESSION_COOKIE_SECURE should be True only when using HTTPS
    # For ACI without HTTPS, keep it False
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = int(
        os.environ.get("SESSION_LIFETIME", 86400)
    )  # 24 hours

    # Additional security headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files

    # CSRF Protection Settings
    WTF_CSRF_SSL_STRICT = False  # Allow CSRF over HTTP (for non-HTTPS deployments)
    WTF_CSRF_CHECK_DEFAULT = True

    # Application settings
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    TESTING = os.environ.get("FLASK_TESTING", "False").lower() == "true"

    # Pagination
    POSTS_PER_PAGE = int(os.environ.get("POSTS_PER_PAGE", 20))
    LISTINGS_PER_PAGE = int(os.environ.get("LISTINGS_PER_PAGE", 20))
    CONVERSATIONS_PER_PAGE = int(os.environ.get("CONVERSATIONS_PER_PAGE", 20))

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_DEFAULT = "200 per hour"

    # Image Optimization
    THUMBNAIL_SIZE = (400, 400)  # Thumbnail dimensions
    AVATAR_SIZE = (200, 200)  # Avatar dimensions

    # Email Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@publicshop.com"
    )

    # Caching Configuration
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL", "redis://localhost:6379/0")

    # SocketIO Configuration
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get("SOCKETIO_CORS_ALLOWED_ORIGINS", "*")

    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure upload directories exist
        for subdir in ["listings", "avatars"]:
            upload_path = Config.UPLOAD_FOLDER / subdir
            upload_path.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    # SESSION_COOKIE_SECURE should be True only with HTTPS
    # ACI without HTTPS = keep False, otherwise cookies won't work
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Validate SECRET_KEY in production
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key or secret_key == "dev-secret-change-this-in-production":
            raise ValueError(
                "SECRET_KEY must be set in production environment! Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )

        # Validate email configuration
        if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
            app.logger.warning(
                "Email configuration not set. Email verification will not work!"
            )

        # Log to stderr in production
        import logging
        from logging import StreamHandler

        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

        # Production-specific settings
        app.config["SQLALCHEMY_ECHO"] = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
