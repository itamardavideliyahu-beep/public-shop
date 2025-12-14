"""
WSGI entry point for production deployment.

This file is used by production WSGI servers like Gunicorn, uWSGI, etc.
"""
from app import create_app

app, socketio = create_app(config_name="production")

if __name__ == "__main__":
    socketio.run(app)

