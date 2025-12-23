"""
Middleware and request handlers for the application.
"""

import logging
import time
from flask import g, request
from flask_login import current_user


def setup_request_logging(app):
    """Setup request logging middleware."""

    @app.before_request
    def before_request():
        """Log request details and track timing."""
        g.start_time = time.time()

        # Log request details (except sensitive data)
        if not request.path.startswith("/static"):
            app.logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.remote_addr} "
                f"User: {current_user.id if current_user.is_authenticated else 'anonymous'}"
            )

    @app.after_request
    def after_request(response):
        """Log response details and timing."""
        if hasattr(g, "start_time") and not request.path.startswith("/static"):
            elapsed = time.time() - g.start_time
            app.logger.info(
                f"Response: {response.status_code} "
                f"Time: {elapsed:.3f}s "
                f"Path: {request.path}"
            )
        return response

    @app.teardown_request
    def teardown_request(exception=None):
        """Clean up after request."""
        if exception:
            app.logger.error(f"Request teardown error: {exception}", exc_info=True)


def setup_error_handlers(app):
    """Setup enhanced error handlers."""

    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit exceeded errors."""
        from flask import render_template, jsonify

        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return (
                jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                    }
                ),
                429,
            )

        return render_template("errors/429.html"), 429

    @app.errorhandler(400)
    def bad_request_handler(e):
        """Handle bad request errors."""
        from flask import render_template, jsonify

        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return jsonify({"error": "Bad request", "message": str(e)}), 400

        return render_template("errors/400.html"), 400
