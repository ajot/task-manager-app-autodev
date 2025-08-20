from marshmallow import Schema, fields, validate
from app import ma
from app.models import Project

class ProjectSchema(ma.SQLAlchemyAutoSchema):
    """Project serialization schema"""
    
    class Meta:
        model = Project
        load_instance = True
        dump_only_fields = ('id', 'created_at', 'updated_at')
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    icon = fields.Str(validate=validate.Length(max=50))
    owner_id = fields.UUID(dump_only=True)
    is_archived = fields.Bool()
    
    # Nested relationships
    owner = fields.Nested('UserSchema', only=('id', 'username', 'full_name'), dump_only=True)
    tasks_count = fields.Method('get_tasks_count')
    members_count = fields.Method('get_members_count')
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_members_count(self, obj):
        return len(obj.members)

class ProjectCreateSchema(Schema):
    """Schema for project creation"""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    icon = fields.Str(validate=validate.Length(max=50))

class ProjectUpdateSchema(Schema):
    """Schema for project updates"""
    
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    icon = fields.Str(validate=validate.Length(max=50))
    is_archived = fields.Bool()

class ProjectMemberSchema(Schema):
    """Schema for project member operations"""
    
    user_id = fields.UUID(required=True)
    role = fields.Str(validate=validate.OneOf(['viewer', 'member', 'admin']))
    
class ProjectMemberUpdateSchema(Schema):
    """Schema for updating project member role"""
    
    role = fields.Str(required=True, validate=validate.OneOf(['viewer', 'member', 'admin']))