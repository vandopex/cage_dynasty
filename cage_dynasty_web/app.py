"""
Cage Dynasty - MMA Management Simulation
Flask Web Application Entry Point
"""

import os as _os

from flask import Flask
from routes import register_routes
from game_bridge import get_bridge, GameBridge

def create_app():
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__)

    # Configuration — env-var overrides for production deployment
    app.config['SECRET_KEY'] = _os.environ.get(
        'SECRET_KEY', 'dev-only-fallback-change-in-prod')
    app.config['DEBUG'] = (
        _os.environ.get('FLASK_DEBUG', '').lower() == 'true')
    
    # Initialize game bridge (connects to real game engine or mock)
    app.game_bridge = get_bridge()
    
    # Register all routes
    register_routes(app)
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(
        debug=_os.environ.get('FLASK_DEBUG', '').lower() == 'true',
        host='0.0.0.0',
        port=5001,
    )
