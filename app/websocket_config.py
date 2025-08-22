"""
WebSocket configuration and setup for real-time task management
"""

from flask_socketio import SocketIO
from flask import request, session
from flask_jwt_extended import decode_token, JWTManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading'
)

def init_websocket(app):
    """
    Initialize WebSocket with Flask app
    
    Args:
        app: Flask application instance
    """
    socketio.init_app(app, cors_allowed_origins="*")
    return socketio

def authenticate_socket_user():
    """
    Authenticate user for WebSocket connections using JWT token
    
    Returns:
        dict: User information if authenticated, None otherwise
    """
    try:
        # Get token from session or query parameters
        token = request.args.get('token')
        if not token and 'access_token' in session:
            token = session['access_token']
        
        if not token:
            logger.warning("No token provided for WebSocket authentication")
            return None
            
        # Decode JWT token to get user info
        decoded_token = decode_token(token)
        user_id = decoded_token.get('sub')
        
        if user_id:
            return {
                'user_id': user_id,
                'token': token
            }
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        
    return None

def join_user_room(user_id, room_type='user'):
    """
    Join user to their personal room for targeted notifications
    
    Args:
        user_id: User ID
        room_type: Type of room ('user', 'project', 'task')
    """
    from flask_socketio import join_room
    
    room_name = f"{room_type}_{user_id}"
    join_room(room_name)
    logger.info(f"User {user_id} joined room: {room_name}")
    return room_name

def leave_user_room(user_id, room_type='user'):
    """
    Remove user from their room
    
    Args:
        user_id: User ID
        room_type: Type of room to leave
    """
    from flask_socketio import leave_room
    
    room_name = f"{room_type}_{user_id}"
    leave_room(room_name)
    logger.info(f"User {user_id} left room: {room_name}")

def broadcast_to_project(project_id, event_name, data):
    """
    Broadcast event to all project members
    
    Args:
        project_id: Project ID
        event_name: Name of the event
        data: Event data
    """
    room_name = f"project_{project_id}"
    socketio.emit(event_name, data, room=room_name)
    logger.info(f"Broadcasted {event_name} to project room: {room_name}")

def broadcast_to_user(user_id, event_name, data):
    """
    Send event to specific user
    
    Args:
        user_id: Target user ID
        event_name: Name of the event
        data: Event data
    """
    room_name = f"user_{user_id}"
    socketio.emit(event_name, data, room=room_name)
    logger.info(f"Sent {event_name} to user room: {room_name}")