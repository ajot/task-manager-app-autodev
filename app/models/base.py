from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app import db

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save the record to database"""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete the record from database"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}