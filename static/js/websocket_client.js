/**
 * WebSocket client for real-time task management updates
 */

class TaskManagerWebSocket {
    constructor(options = {}) {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentProject = null;
        
        // Configuration
        this.config = {
            url: options.url || window.location.origin,
            token: options.token || this.getTokenFromSession(),
            debug: options.debug || false,
            ...options
        };
        
        // Event handlers
        this.eventHandlers = {
            'connected': [],
            'disconnected': [],
            'task_updated': [],
            'task_assigned': [],
            'comment_added': [],
            'user_typing_status': [],
            'task_status_changed': [],
            'member_added': [],
            'due_date_reminder': [],
            'user_presence': []
        };
        
        this.init();
    }
    
    /**
     * Initialize WebSocket connection
     */
    init() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded');
            return;
        }
        
        const socketOptions = {
            query: {
                token: this.config.token
            },
            transports: ['websocket', 'polling']
        };
        
        this.socket = io(this.config.url, socketOptions);
        this.setupEventListeners();
    }
    
    /**
     * Setup Socket.IO event listeners
     */
    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.log('Connected to WebSocket server');
            this.trigger('connected', { socketId: this.socket.id });
        });
        
        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            this.log('Disconnected from WebSocket server:', reason);
            this.trigger('disconnected', { reason });
            
            // Attempt reconnection if not manually disconnected
            if (reason !== 'io client disconnect') {
                this.attemptReconnection();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.attemptReconnection();
        });
        
        // Task update events
        this.socket.on('task_updated', (data) => {
            this.log('Task updated:', data);
            this.trigger('task_updated', data);
            this.updateTaskInUI(data);
        });
        
        this.socket.on('task_status_changed', (data) => {
            this.log('Task status changed:', data);
            this.trigger('task_status_changed', data);
            this.updateTaskStatus(data);
        });
        
        this.socket.on('task_assigned', (data) => {
            this.log('Task assigned:', data);
            this.trigger('task_assigned', data);
            this.updateTaskAssignment(data);
        });
        
        this.socket.on('task_assigned_to_you', (data) => {
            this.log('Task assigned to you:', data);
            this.showNotification('New Task Assignment', `You have been assigned a new task`, 'info');
        });
        
        // Comment events
        this.socket.on('comment_added', (data) => {
            this.log('Comment added:', data);
            this.trigger('comment_added', data);
            this.addCommentToUI(data);
        });
        
        // Typing indicators
        this.socket.on('user_typing_status', (data) => {
            this.trigger('user_typing_status', data);
            this.updateTypingIndicator(data);
        });
        
        // User presence
        this.socket.on('user_presence', (data) => {
            this.log('User presence update:', data);
            this.trigger('user_presence', data);
            this.updateUserPresence(data);
        });
        
        // Project events
        this.socket.on('member_added', (data) => {
            this.log('Member added to project:', data);
            this.trigger('member_added', data);
        });
        
        // Notifications
        this.socket.on('due_date_reminder', (data) => {
            this.log('Due date reminder:', data);
            this.trigger('due_date_reminder', data);
            this.showNotification('Due Date Reminder', `Task "${data.task.title}" is due soon`, 'warning');
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('Connection Error', error.message, 'error');
        });
        
        // Pong response
        this.socket.on('pong', (data) => {
            this.log('Pong received:', data);
        });
    }
    
    /**
     * Join a project room for updates
     */
    joinProject(projectId) {
        if (!this.isConnected) {
            this.log('Cannot join project: not connected');
            return;
        }
        
        this.currentProject = projectId;
        this.socket.emit('join_project', { project_id: projectId });
        this.log(`Joined project room: ${projectId}`);
    }
    
    /**
     * Leave current project room
     */
    leaveProject(projectId = null) {
        const targetProject = projectId || this.currentProject;
        if (targetProject && this.isConnected) {
            this.socket.emit('leave_project', { project_id: targetProject });
            this.log(`Left project room: ${targetProject}`);
            if (targetProject === this.currentProject) {
                this.currentProject = null;
            }
        }
    }
    
    /**
     * Emit task status update
     */
    updateTaskStatus(taskId, status, projectId = null) {
        if (!this.isConnected) return;
        
        const data = {
            task_id: taskId,
            status: status,
            project_id: projectId || this.currentProject,
            timestamp: new Date().toISOString()
        };
        
        this.socket.emit('task_status_update', data);
        this.log('Emitted task status update:', data);
    }
    
    /**
     * Emit new comment
     */
    addComment(taskId, comment, projectId = null) {
        if (!this.isConnected) return;
        
        const data = {
            task_id: taskId,
            comment: comment,
            project_id: projectId || this.currentProject,
            timestamp: new Date().toISOString()
        };
        
        this.socket.emit('new_comment', data);
        this.log('Emitted new comment:', data);
    }
    
    /**
     * Emit typing indicator
     */
    setTyping(taskId, isTyping, projectId = null) {
        if (!this.isConnected) return;
        
        const data = {
            task_id: taskId,
            project_id: projectId || this.currentProject,
            is_typing: isTyping
        };
        
        this.socket.emit('user_typing', data);
    }
    
    /**
     * Send ping to server
     */
    ping() {
        if (this.isConnected) {
            this.socket.emit('ping', { timestamp: new Date().toISOString() });
        }
    }
    
    /**
     * Register event handler
     */
    on(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(handler);
        }
    }
    
    /**
     * Remove event handler
     */
    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }
    
    /**
     * Trigger event handlers
     */
    trigger(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }
    
    /**
     * Attempt reconnection with exponential backoff
     */
    attemptReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.log('Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        this.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.socket.connect();
            }
        }, delay);
    }
    
    /**
     * Update task in UI
     */
    updateTaskInUI(data) {
        const taskElement = document.querySelector(`[data-task-id="${data.task_id}"]`);
        if (taskElement) {
            // Update task display based on data.updates
            Object.keys(data.updates).forEach(field => {
                const fieldElement = taskElement.querySelector(`[data-field="${field}"]`);
                if (fieldElement) {
                    fieldElement.textContent = data.updates[field];
                }
            });
            
            // Add visual indicator for update
            taskElement.classList.add('task-updated');
            setTimeout(() => taskElement.classList.remove('task-updated'), 2000);
        }
    }
    
    /**
     * Update task status in UI
     */
    updateTaskStatus(data) {
        const taskElement = document.querySelector(`[data-task-id="${data.task_id}"]`);
        if (taskElement) {
            const statusElement = taskElement.querySelector('.task-status');
            if (statusElement) {
                statusElement.textContent = data.new_status;
                statusElement.className = `task-status status-${data.new_status}`;
            }
        }
    }
    
    /**
     * Update task assignment in UI
     */
    updateTaskAssignment(data) {
        const taskElement = document.querySelector(`[data-task-id="${data.task_id}"]`);
        if (taskElement) {
            const assigneeElement = taskElement.querySelector('.task-assignee');
            if (assigneeElement) {
                assigneeElement.textContent = data.assignee_id ? `User ${data.assignee_id}` : 'Unassigned';
            }
        }
    }
    
    /**
     * Add comment to UI
     */
    addCommentToUI(data) {
        const commentsContainer = document.querySelector(`#task-${data.task_id}-comments`);
        if (commentsContainer) {
            const commentElement = document.createElement('div');
            commentElement.className = 'comment';
            commentElement.innerHTML = `
                <div class="comment-author">User ${data.author_id}</div>
                <div class="comment-content">${data.comment}</div>
                <div class="comment-timestamp">${new Date(data.timestamp).toLocaleString()}</div>
            `;
            commentsContainer.appendChild(commentElement);
        }
    }
    
    /**
     * Update typing indicator
     */
    updateTypingIndicator(data) {
        const indicatorElement = document.querySelector(`#typing-indicator-${data.task_id}`);
        if (indicatorElement) {
            if (data.is_typing) {
                indicatorElement.textContent = `User ${data.user_id} is typing...`;
                indicatorElement.style.display = 'block';
            } else {
                indicatorElement.style.display = 'none';
            }
        }
    }
    
    /**
     * Update user presence indicator
     */
    updateUserPresence(data) {
        const userElement = document.querySelector(`[data-user-id="${data.user_id}"]`);
        if (userElement) {
            const presenceIndicator = userElement.querySelector('.presence-indicator');
            if (presenceIndicator) {
                presenceIndicator.className = `presence-indicator ${data.is_online ? 'online' : 'offline'}`;
            }
        }
    }
    
    /**
     * Show notification to user
     */
    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to page
        let container = document.querySelector('.notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Close button handler
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.parentNode.removeChild(notification);
        });
    }
    
    /**
     * Get token from session or local storage
     */
    getTokenFromSession() {
        // Try to get from session storage first, then local storage
        return sessionStorage.getItem('access_token') || 
               localStorage.getItem('access_token') || 
               null;
    }
    
    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.isConnected = false;
        }
    }
    
    /**
     * Log debug messages
     */
    log(...args) {
        if (this.config.debug) {
            console.log('[WebSocket]', ...args);
        }
    }
}

// Export for use in other files
window.TaskManagerWebSocket = TaskManagerWebSocket;