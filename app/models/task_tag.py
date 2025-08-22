from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app import db

class TaskTag(db.Model):
    """Junction table for many-to-many relationship between tasks and tags"""
    __tablename__ = 'task_tags'
    
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)
    
    # Relationships
    task = db.relationship('Task', back_populates='task_tags')
    tag = db.relationship('Tag', back_populates='task_tags')
    
    __table_args__ = (
        UniqueConstraint('task_id', 'tag_id', name='_task_tag_uc'),
    )
    
    def __repr__(self):
        return f'<TaskTag task:{self.task_id} tag:{self.tag_id}>'