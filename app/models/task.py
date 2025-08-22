from sqlalchemy import Column, String, ForeignKey, Text, Enum, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.models.base import BaseModel
from app import db

class TaskStatus(enum.Enum):
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    REVIEW = 'review'
    DONE = 'done'

class TaskPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

class Task(BaseModel):
    """Task model for task management"""
    __tablename__ = 'tasks'
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date = Column(DateTime)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    completed_at = Column(DateTime)
    
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('User', back_populates='assigned_tasks',
                              foreign_keys=[assignee_id])
    creator = db.relationship('User', back_populates='created_tasks',
                             foreign_keys=[creator_id])
    comments = db.relationship('Comment', back_populates='task',
                              cascade='all, delete-orphan', lazy='dynamic')
    task_tags = db.relationship('TaskTag', back_populates='task',
                               cascade='all, delete-orphan')
    activities = db.relationship('ActivityLog', back_populates='task',
                               lazy='dynamic')
    
    def mark_complete(self):
        """Mark task as completed"""
        from datetime import datetime
        self.status = TaskStatus.DONE
        self.completed_at = datetime.utcnow()
        self.save()
    
    def assign_to(self, user):
        """Assign task to a user"""
        self.assignee_id = user.id
        self.save()
    
    def add_tag(self, tag):
        """Add a tag to the task"""
        from app.models.task_tag import TaskTag
        task_tag = TaskTag(task_id=self.id, tag_id=tag.id)
        db.session.add(task_tag)
        return task_tag
    
    def remove_tag(self, tag):
        """Remove a tag from the task"""
        from app.models.task_tag import TaskTag
        task_tag = TaskTag.query.filter_by(
            task_id=self.id, tag_id=tag.id
        ).first()
        if task_tag:
            db.session.delete(task_tag)
    
    def __repr__(self):
        return f'<Task {self.title}>'