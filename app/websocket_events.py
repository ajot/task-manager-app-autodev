"""
WebSocket event handlers for real-time task management
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request, session
from app.websocket_config import socketio, authenticate_socket_user, join_user_room, leave_user_room
import logging

logger = logging.getLogger(__name__)

# Store connected users
connected_users = {}

@socketio.on('connect')
def handle_connect():
    """
    Handle client WebSocket connection
    """
    user_data = authenticate_socket_user()
    
    if not user_data:
        logger.warning("Unauthenticated WebSocket connection attempt")
        disconnect()
        return False
    
    user_id = user_data['user_id']
    connected_users[request.sid] = user_data
    
    # Join user to their personal room
    join_user_room(user_id)
    
    # Emit connection success
    emit('connected', {
        'message': 'Connected successfully',
        'user_id': user_id
    })
    
    logger.info(f"User {user_id} connected with session {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client WebSocket disconnection
    """
    if request.sid in connected_users:
        user_data = connected_users[request.sid]
        user_id = user_data['user_id']
        
        # Leave user room
        leave_user_room(user_id)
        
        # Remove from connected users
        del connected_users[request.sid]
        
        logger.info(f"User {user_id} disconnected")

@socketio.on('join_project')
def handle_join_project(data):
    """
    Join user to a project room for real-time updates
    
    Args:
        data: Dictionary containing project_id
    """
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    project_id = data.get('project_id')
    if not project_id:
        emit('error', {'message': 'Project ID required'})
        return
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    # Join project room
    room_name = f"project_{project_id}"
    join_room(room_name)
    
    emit('joined_project', {
        'project_id': project_id,
        'room': room_name
    })
    
    logger.info(f"User {user_id} joined project room: {room_name}")

@socketio.on('leave_project')
def handle_leave_project(data):
    """
    Leave a project room
    
    Args:
        data: Dictionary containing project_id
    """
    if request.sid not in connected_users:
        return
    
    project_id = data.get('project_id')
    if not project_id:
        return
    
    room_name = f"project_{project_id}"
    leave_room(room_name)
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    emit('left_project', {
        'project_id': project_id,
        'room': room_name
    })
    
    logger.info(f"User {user_id} left project room: {room_name}")

@socketio.on('task_status_update')
def handle_task_status_update(data):
    """
    Handle real-time task status updates
    
    Args:
        data: Dictionary containing task_id, status, project_id
    """
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    task_id = data.get('task_id')
    status = data.get('status')
    project_id = data.get('project_id')
    
    if not all([task_id, status, project_id]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    # Broadcast to project room
    update_data = {
        'task_id': task_id,
        'status': status,
        'updated_by': user_id,
        'timestamp': data.get('timestamp'),
        'project_id': project_id
    }
    
    socketio.emit('task_updated', update_data, room=f"project_{project_id}")
    
    logger.info(f"Task {task_id} status updated to {status} by user {user_id}")

@socketio.on('task_assignment_update')
def handle_task_assignment(data):
    """
    Handle real-time task assignment updates
    
    Args:
        data: Dictionary containing task_id, assignee_id, project_id
    """
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    task_id = data.get('task_id')
    assignee_id = data.get('assignee_id')
    project_id = data.get('project_id')
    
    if not all([task_id, project_id]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    # Broadcast to project room
    assignment_data = {
        'task_id': task_id,
        'assignee_id': assignee_id,
        'assigned_by': user_id,
        'timestamp': data.get('timestamp'),
        'project_id': project_id
    }
    
    socketio.emit('task_assigned', assignment_data, room=f"project_{project_id}")
    
    # Also notify the assigned user directly
    if assignee_id:
        socketio.emit('task_assigned_to_you', assignment_data, room=f"user_{assignee_id}")
    
    logger.info(f"Task {task_id} assigned to user {assignee_id} by user {user_id}")

@socketio.on('new_comment')
def handle_new_comment(data):
    """
    Handle real-time comment notifications
    
    Args:
        data: Dictionary containing task_id, comment, project_id
    """
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    task_id = data.get('task_id')
    comment = data.get('comment')
    project_id = data.get('project_id')
    
    if not all([task_id, comment, project_id]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    # Broadcast to project room
    comment_data = {
        'task_id': task_id,
        'comment': comment,
        'author_id': user_id,
        'timestamp': data.get('timestamp'),
        'project_id': project_id
    }
    
    socketio.emit('comment_added', comment_data, room=f"project_{project_id}")
    
    logger.info(f"New comment added to task {task_id} by user {user_id}")

@socketio.on('user_typing')
def handle_user_typing(data):
    """
    Handle typing indicators for comments
    
    Args:
        data: Dictionary containing task_id, project_id, is_typing
    """
    if request.sid not in connected_users:
        return
    
    task_id = data.get('task_id')
    project_id = data.get('project_id')
    is_typing = data.get('is_typing', False)
    
    if not all([task_id, project_id]):
        return
    
    user_data = connected_users[request.sid]
    user_id = user_data['user_id']
    
    # Broadcast typing status to project room (excluding sender)
    typing_data = {
        'task_id': task_id,
        'user_id': user_id,
        'is_typing': is_typing,
        'project_id': project_id
    }
    
    socketio.emit('user_typing_status', typing_data, room=f"project_{project_id}", include_self=False)

@socketio.on('ping')
def handle_ping():
    """
    Handle ping/pong for connection keepalive
    """
    emit('pong', {'timestamp': data.get('timestamp') if 'data' in locals() else None})