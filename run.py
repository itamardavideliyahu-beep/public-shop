"""
Development server entry point.

For production, use a WSGI server like Gunicorn with wsgi.py.
"""
import os
from app import create_app

app, socketio = create_app(config_name=os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    # Development server settings
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    
    socketio.run(app, debug=debug, host=host, port=port, allow_unsafe_werkzeug=True)
