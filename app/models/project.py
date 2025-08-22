from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app import db

class Project(BaseModel):
    """Project model for organizing tasks"""
    __tablename__ = 'projects'
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    color = Column(String(7))  # Hex color code
    icon = Column(String(50))
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    owner = db.relationship('User', back_populates='owned_projects',
                          foreign_keys=[owner_id])
    tasks = db.relationship('Task', back_populates='project',
                          cascade='all, delete-orphan', lazy='dynamic')
    members = db.relationship('ProjectMember', back_populates='project',
                            cascade='all, delete-orphan')
    tags = db.relationship('Tag', back_populates='project',
                         cascade='all, delete-orphan', lazy='dynamic')
    activities = db.relationship('ActivityLog', back_populates='project',
                               lazy='dynamic')
    
    def add_member(self, user, role='member'):
        """Add a user as a project member"""
        from app.models.project_member import ProjectMember
        member = ProjectMember(project_id=self.id, user_id=user.id, role=role)
        db.session.add(member)
        return member
    
    def remove_member(self, user):
        """Remove a user from project members"""
        from app.models.project_member import ProjectMember
        member = ProjectMember.query.filter_by(
            project_id=self.id, user_id=user.id
        ).first()
        if member:
            db.session.delete(member)
    
    def is_member(self, user):
        """Check if user is a project member"""
        from app.models.project_member import ProjectMember
        return ProjectMember.query.filter_by(
            project_id=self.id, user_id=user.id
        ).first() is not None
    
    def __repr__(self):
        return f'<Project {self.name}>'