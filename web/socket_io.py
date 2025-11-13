"""
SocketIO module for AirStrike web interface.

This module provides the SocketIO instance used for real-time communication.
"""

from flask_socketio import SocketIO
import logging
import sys
import os

# Configure basic logging if not already configured
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Create SocketIO instance with simpler configuration
socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)
logger = logging.getLogger('socketio')
logger.setLevel(logging.DEBUG)

def init_socketio(app):
    """
    Initialize SocketIO with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    try:
        # Make sure app is properly passed to SocketIO
        socketio.init_app(app)
        logging.info(f"SocketIO initialized with app {app.name}")
        
        @socketio.on('connect')
        def handle_connect():
            from web.shared import logger
            logger.info('Client connected')
            # Send a welcome message to confirm connection
            socketio.emit('welcome', {'message': 'Connected to AirStrike server'})

        @socketio.on('disconnect')
        def handle_disconnect():
            from web.shared import logger
            logger.info('Client disconnected')
            
        @socketio.on('attack_status_request')
        def handle_attack_status_request():
            from web.shared import logger, attack_state
            logger.info('Received attack status request')
            socketio.emit('attack_status', {
                'running': attack_state['running'],
                'attack_type': attack_state['attack_type'],
                'progress': attack_state['progress']
            })
            
        @socketio.on_error()
        def handle_error(e):
            from web.shared import logger
            logger.error(f"SocketIO error: {e}")
            
        # Test emit to ensure socket is working
        socketio.emit('server_startup', {'status': 'ready'})
        logging.info("SocketIO test emit sent")
        
        return True
        
    except Exception as e:
        logging.error(f"Error initializing SocketIO events: {e}")
        return False 