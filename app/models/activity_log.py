from datetime import datetime
from sqlalchemy import Column, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from app.models.base import BaseModel
from app import db

class ActivityAction(enum.Enum):
    CREATED = 'created'
    UPDATED = 'updated'
    DELETED = 'deleted'
    COMPLETED = 'completed'
    COMMENTED = 'commented'
    ASSIGNED = 'assigned'
    STATUS_CHANGED = 'status_changed'
    MEMBER_ADDED = 'member_added'
    MEMBER_REMOVED = 'member_removed'

class ActivityLog(BaseModel):
    """Activity log for tracking user actions"""
    __tablename__ = 'activity_logs'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))
    action = Column(Enum(ActivityAction), nullable=False)
    details = Column(JSONB)  # Store additional context about the activity
    
    # Override created_at to not have default (we only need it from BaseModel)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='activities')
    project = db.relationship('Project', back_populates='activities')
    task = db.relationship('Task', back_populates='activities')
    
    @classmethod
    def log_activity(cls, user, project, action, task=None, details=None):
        """Helper method to create an activity log entry"""
        activity = cls(
            user_id=user.id,
            project_id=project.id,
            task_id=task.id if task else None,
            action=action,
            details=details or {}
        )
        db.session.add(activity)
        return activity
    
    def __repr__(self):
        return f'<ActivityLog {self.action.value} by {self.user_id}>'