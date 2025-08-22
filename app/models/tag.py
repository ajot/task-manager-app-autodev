from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app import db

class Tag(BaseModel):
    """Tag model for categorizing tasks"""
    __tablename__ = 'tags'
    
    name = Column(String(50), nullable=False)
    color = Column(String(7))  # Hex color code
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    
    # Relationships
    project = db.relationship('Project', back_populates='tags')
    task_tags = db.relationship('TaskTag', back_populates='tag',
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tag {self.name}>'