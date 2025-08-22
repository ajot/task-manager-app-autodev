from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import enum
from app import db

class MemberRole(enum.Enum):
    VIEWER = 'viewer'
    MEMBER = 'member'
    ADMIN = 'admin'

class ProjectMember(db.Model):
    """Junction table for project members with roles"""
    __tablename__ = 'project_members'
    
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', back_populates='project_memberships')
    
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='_project_member_uc'),
    )
    
    def __repr__(self):
        return f'<ProjectMember project:{self.project_id} user:{self.user_id} role:{self.role.value}>'