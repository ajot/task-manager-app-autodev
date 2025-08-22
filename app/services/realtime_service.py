"""
Real-time service for broadcasting task and project updates
"""

from app.websocket_config import socketio, broadcast_to_project, broadcast_to_user
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class RealTimeService:
    """
    Service class for managing real-time updates and notifications
    """
    
    @staticmethod
    def broadcast_task_created(task_data: Dict, project_id: int, creator_id: int):
        """
        Broadcast new task creation to project members
        
        Args:
            task_data: Task information
            project_id: Project ID
            creator_id: User who created the task
        """
        event_data = {
            'type': 'task_created',
            'task': task_data,
            'project_id': project_id,
            'created_by': creator_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'task_created', event_data)
        logger.info(f"Broadcasted task creation for project {project_id}")
    
    @staticmethod
    def broadcast_task_updated(task_id: int, updates: Dict, project_id: int, updater_id: int):
        """
        Broadcast task updates to project members
        
        Args:
            task_id: Task ID
            updates: Dictionary of updated fields
            project_id: Project ID
            updater_id: User who made the update
        """
        event_data = {
            'type': 'task_updated',
            'task_id': task_id,
            'updates': updates,
            'project_id': project_id,
            'updated_by': updater_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'task_updated', event_data)
        logger.info(f"Broadcasted task update for task {task_id} in project {project_id}")
    
    @staticmethod
    def broadcast_task_status_change(task_id: int, old_status: str, new_status: str, 
                                   project_id: int, updater_id: int):
        """
        Broadcast task status changes
        
        Args:
            task_id: Task ID
            old_status: Previous status
            new_status: New status
            project_id: Project ID
            updater_id: User who changed the status
        """
        event_data = {
            'type': 'task_status_changed',
            'task_id': task_id,
            'old_status': old_status,
            'new_status': new_status,
            'project_id': project_id,
            'updated_by': updater_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'task_status_changed', event_data)
        logger.info(f"Broadcasted status change for task {task_id}: {old_status} -> {new_status}")
    
    @staticmethod
    def broadcast_task_assignment(task_id: int, assignee_id: Optional[int], 
                                project_id: int, assigner_id: int):
        """
        Broadcast task assignment changes
        
        Args:
            task_id: Task ID
            assignee_id: New assignee ID (None if unassigned)
            project_id: Project ID
            assigner_id: User who made the assignment
        """
        event_data = {
            'type': 'task_assigned',
            'task_id': task_id,
            'assignee_id': assignee_id,
            'project_id': project_id,
            'assigned_by': assigner_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to project
        broadcast_to_project(project_id, 'task_assigned', event_data)
        
        # Send personal notification to assignee
        if assignee_id:
            personal_data = event_data.copy()
            personal_data['type'] = 'task_assigned_to_you'
            broadcast_to_user(assignee_id, 'task_assigned_to_you', personal_data)
        
        logger.info(f"Broadcasted task assignment for task {task_id} to user {assignee_id}")
    
    @staticmethod
    def broadcast_comment_added(task_id: int, comment_data: Dict, project_id: int, 
                              author_id: int):
        """
        Broadcast new comment addition
        
        Args:
            task_id: Task ID
            comment_data: Comment information
            project_id: Project ID
            author_id: Comment author ID
        """
        event_data = {
            'type': 'comment_added',
            'task_id': task_id,
            'comment': comment_data,
            'project_id': project_id,
            'author_id': author_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'comment_added', event_data)
        logger.info(f"Broadcasted new comment for task {task_id} by user {author_id}")
    
    @staticmethod
    def broadcast_project_member_added(project_id: int, member_data: Dict, 
                                     added_by: int):
        """
        Broadcast new project member addition
        
        Args:
            project_id: Project ID
            member_data: New member information
            added_by: User who added the member
        """
        event_data = {
            'type': 'member_added',
            'project_id': project_id,
            'member': member_data,
            'added_by': added_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'member_added', event_data)
        
        # Send personal notification to new member
        member_id = member_data.get('user_id')
        if member_id:
            welcome_data = event_data.copy()
            welcome_data['type'] = 'added_to_project'
            broadcast_to_user(member_id, 'added_to_project', welcome_data)
        
        logger.info(f"Broadcasted member addition for project {project_id}")
    
    @staticmethod
    def broadcast_due_date_reminder(task_id: int, task_data: Dict, 
                                  project_id: int, assignee_id: int):
        """
        Broadcast due date reminders
        
        Args:
            task_id: Task ID
            task_data: Task information
            project_id: Project ID
            assignee_id: Assignee to remind
        """
        event_data = {
            'type': 'due_date_reminder',
            'task_id': task_id,
            'task': task_data,
            'project_id': project_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to assignee
        broadcast_to_user(assignee_id, 'due_date_reminder', event_data)
        
        # Also broadcast to project (optional)
        broadcast_to_project(project_id, 'due_date_reminder', event_data)
        
        logger.info(f"Sent due date reminder for task {task_id} to user {assignee_id}")
    
    @staticmethod
    def get_online_users(project_id: int) -> List[int]:
        """
        Get list of online users in a project
        
        Args:
            project_id: Project ID
            
        Returns:
            List of user IDs currently online in the project
        """
        # This would typically query connected_users from websocket_events
        # For now, return empty list as placeholder
        return []
    
    @staticmethod
    def broadcast_user_presence(user_id: int, project_id: int, is_online: bool):
        """
        Broadcast user online/offline status
        
        Args:
            user_id: User ID
            project_id: Project ID
            is_online: Whether user is online
        """
        event_data = {
            'type': 'user_presence',
            'user_id': user_id,
            'project_id': project_id,
            'is_online': is_online,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        broadcast_to_project(project_id, 'user_presence', event_data)
        logger.info(f"Broadcasted presence update for user {user_id}: {'online' if is_online else 'offline'}")