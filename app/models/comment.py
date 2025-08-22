from sqlalchemy import Column, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app import db

class Comment(BaseModel):
    """Comment model for task comments"""
    __tablename__ = 'comments'
    
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    task = db.relationship('Task', back_populates='comments')
    user = db.relationship('User', back_populates='comments')
    
    def mark_edited(self):
        """Mark comment as edited"""
        self.is_edited = True
        self.save()
    
    def __repr__(self):
        return f'<Comment by {self.user_id} on task {self.task_id}>'