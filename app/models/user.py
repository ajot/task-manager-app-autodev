from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base import BaseModel
from app import db

class User(BaseModel):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    owned_projects = db.relationship('Project', back_populates='owner', 
                                    foreign_keys='Project.owner_id',
                                    lazy='dynamic')
    project_memberships = db.relationship('ProjectMember', back_populates='user',
                                         cascade='all, delete-orphan')
    created_tasks = db.relationship('Task', back_populates='creator',
                                   foreign_keys='Task.creator_id',
                                   lazy='dynamic')
    assigned_tasks = db.relationship('Task', back_populates='assignee',
                                    foreign_keys='Task.assignee_id',
                                    lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user',
                              cascade='all, delete-orphan')
    activities = db.relationship('ActivityLog', back_populates='user',
                                lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        self.save()
    
    def __repr__(self):
        return f'<User {self.username}>'