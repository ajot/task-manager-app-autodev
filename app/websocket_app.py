"""
Flask application with WebSocket integration
"""

from flask import Flask
from flask_socketio import SocketIO
from app.websocket_config import init_websocket
import app.websocket_events  # Import to register event handlers
from app.services.realtime_service import RealTimeService

def create_websocket_app(app=None):
    """
    Create Flask application with WebSocket support
    
    Args:
        app: Existing Flask app instance (optional)
        
    Returns:
        Tuple of (app, socketio)
    """
    if app is None:
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize WebSocket
    socketio = init_websocket(app)
    
    # Add WebSocket configuration
    app.config.update({
        'WEBSOCKET_ENABLED': True,
        'WEBSOCKET_CORS_ORIGINS': '*',
        'WEBSOCKET_ASYNC_MODE': 'threading'
    })
    
    # Register WebSocket blueprint or routes if needed
    # (Event handlers are automatically registered via import)
    
    return app, socketio

def integrate_with_existing_app(app):
    """
    Integrate WebSocket functionality with existing Flask app
    
    Args:
        app: Existing Flask application instance
        
    Returns:
        SocketIO instance
    """
    # Add WebSocket dependencies to requirements
    socketio = init_websocket(app)
    
    # Import event handlers to register them
    import app.websocket_events
    
    # Add RealTimeService to app context
    app.realtime_service = RealTimeService
    
    return socketio

# Example usage for standalone WebSocket app
if __name__ == '__main__':
    app, socketio = create_websocket_app()
    
    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebSocket Test</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        </head>
        <body>
            <h1>WebSocket Test Page</h1>
            <div id="messages"></div>
            <script>
                const socket = io();
                socket.on('connect', function() {
                    console.log('Connected');
                    document.getElementById('messages').innerHTML += '<p>Connected to WebSocket</p>';
                });
                socket.on('disconnect', function() {
                    console.log('Disconnected');
                    document.getElementById('messages').innerHTML += '<p>Disconnected from WebSocket</p>';
                });
            </script>
        </body>
        </html>
        '''
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)