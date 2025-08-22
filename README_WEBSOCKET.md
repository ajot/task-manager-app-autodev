# WebSocket Real-time Implementation Guide

## Overview
This implementation provides real-time updates for the task management application using Flask-SocketIO. It enables instant notifications for task updates, assignments, comments, and user presence.

## Architecture

### Backend Components

1. **websocket_config.py** - WebSocket configuration and initialization
2. **websocket_events.py** - Event handlers for WebSocket connections
3. **services/realtime_service.py** - Service layer for broadcasting updates
4. **websocket_app.py** - Flask app integration

### Frontend Components

1. **websocket_client.js** - JavaScript WebSocket client
2. **websocket_notifications.css** - Styling for real-time UI updates

## Features

### Real-time Updates
- Task status changes
- Task assignments
- New comments
- Project member additions
- Due date reminders
- User presence indicators
- Typing indicators

### Authentication
- JWT token-based authentication for WebSocket connections
- User session management
- Automatic reconnection with exponential backoff

### Broadcasting
- Project-specific rooms for targeted updates
- Personal user rooms for direct notifications
- Efficient event routing

## Installation

1. **Install Dependencies**
```bash
pip install flask-socketio==5.3.6
pip install python-socketio==5.10.0
pip install python-engineio==4.7.1
pip install eventlet==0.33.3
pip install pyjwt==2.8.0
```

2. **Add to existing Flask app**
```python
from app.websocket_app import integrate_with_existing_app

app = Flask(__name__)
socketio = integrate_with_existing_app(app)

# Run with SocketIO
socketio.run(app, debug=True)
```

## Usage

### Backend Integration

```python
from app.services.realtime_service import RealTimeService

# Broadcast task update
RealTimeService.broadcast_task_updated(
    task_id=123,
    updates={'status': 'completed'},
    project_id=456,
    updater_id=789
)

# Broadcast new comment
RealTimeService.broadcast_comment_added(
    task_id=123,
    comment_data={'content': 'Great work!'},
    project_id=456,
    author_id=789
)
```

### Frontend Integration

```javascript
// Initialize WebSocket client
const websocket = new TaskManagerWebSocket({
    debug: true,
    token: getUserToken()
});

// Join project for updates
websocket.joinProject(projectId);

// Listen for task updates
websocket.on('task_updated', (data) => {
    console.log('Task updated:', data);
    updateTaskInUI(data);
});

// Send status update
websocket.updateTaskStatus(taskId, 'completed');
```

### HTML Integration

```html
<!-- Include Socket.IO client -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>

<!-- Include WebSocket client -->
<script src="/static/js/websocket_client.js"></script>

<!-- Include notification styles -->
<link rel="stylesheet" href="/static/css/websocket_notifications.css">
```

## Event Types

### Client to Server
- `connect` - Initial connection
- `join_project` - Join project room
- `leave_project` - Leave project room
- `task_status_update` - Update task status
- `new_comment` - Add comment
- `user_typing` - Typing indicator
- `ping` - Connection keepalive

### Server to Client
- `connected` - Connection confirmed
- `task_updated` - Task was updated
- `task_status_changed` - Task status changed
- `task_assigned` - Task was assigned
- `comment_added` - New comment added
- `user_typing_status` - User typing status
- `user_presence` - User online/offline
- `due_date_reminder` - Due date notification

## Security

- JWT token authentication for all connections
- User authorization for project access
- Input validation for all events
- Rate limiting (placeholder for Redis implementation)

## Deployment Considerations

### Development
```python
# Run with built-in development server
socketio.run(app, debug=True)
```

### Production
```python
# Use eventlet or gevent for production
import eventlet
eventlet.monkey_patch()

# Or with gunicorn
# gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 app:app
```

### Scaling
- For multiple server instances, implement Redis adapter:
```python
from flask_socketio import SocketIO
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
socketio = SocketIO(app, message_queue='redis://localhost:6379')
```

## Configuration

### Environment Variables
```bash
# WebSocket settings
WEBSOCKET_CORS_ORIGINS="*"
WEBSOCKET_ASYNC_MODE="threading"
WEBSOCKET_PING_TIMEOUT=60
WEBSOCKET_PING_INTERVAL=25

# Redis (for scaling)
REDIS_URL="redis://localhost:6379"
```

### Flask Configuration
```python
app.config.update({
    'WEBSOCKET_ENABLED': True,
    'WEBSOCKET_CORS_ORIGINS': '*',
    'WEBSOCKET_ASYNC_MODE': 'threading'
})
```

## Testing

### Manual Testing
1. Open multiple browser tabs
2. Join the same project
3. Update task status in one tab
4. Verify real-time update in other tabs

### Automated Testing
```python
import unittest
from flask_socketio import SocketIOTestClient

class WebSocketTest(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_websocket_app()
        self.client = SocketIOTestClient(self.socketio, self.app)
    
    def test_connect(self):
        received = self.client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'connected')
```

## Monitoring

### Connection Health
- Implement ping/pong for connection monitoring
- Track connected users per project
- Monitor reconnection attempts

### Performance Metrics
- Message throughput
- Connection duration
- Event processing time
- Memory usage

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check JWT token validity
   - Verify CORS settings
   - Check firewall/proxy configuration

2. **Events Not Received**
   - Ensure user joined correct project room
   - Check authentication
   - Verify event name spelling

3. **Memory Leaks**
   - Clean up event handlers on disconnect
   - Remove users from connected_users dict
   - Clear typing indicators

### Debug Mode
```javascript
const websocket = new TaskManagerWebSocket({
    debug: true // Enables console logging
});
```

## Future Enhancements

- File sharing with progress updates
- Video/voice chat integration
- Advanced user presence (idle, busy, etc.)
- Message persistence for offline users
- Push notifications for mobile devices
- WebRTC for peer-to-peer features