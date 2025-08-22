from marshmallow import Schema, fields, validate
from app import ma
from app.models import Task, TaskStatus, TaskPriority

class TaskSchema(ma.SQLAlchemyAutoSchema):
    """Task serialization schema"""
    
    class Meta:
        model = Task
        load_instance = True
        dump_only_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str()
    status = fields.Enum(TaskStatus)
    priority = fields.Enum(TaskPriority)
    due_date = fields.DateTime()
    estimated_hours = fields.Float(validate=validate.Range(min=0))
    actual_hours = fields.Float(validate=validate.Range(min=0))
    
    # Relationships
    project = fields.Nested('ProjectSchema', only=('id', 'name'), dump_only=True)
    assignee = fields.Nested('UserSchema', only=('id', 'username', 'full_name'), dump_only=True)
    creator = fields.Nested('UserSchema', only=('id', 'username', 'full_name'), dump_only=True)
    comments_count = fields.Method('get_comments_count')
    tags = fields.Nested('TagSchema', many=True, only=('id', 'name', 'color'), dump_only=True)
    
    def get_comments_count(self, obj):
        return obj.comments.count()

class TaskCreateSchema(Schema):
    """Schema for task creation"""
    
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str()
    project_id = fields.UUID(required=True)
    assignee_id = fields.UUID()
    status = fields.Str(validate=validate.OneOf([s.value for s in TaskStatus]))
    priority = fields.Str(validate=validate.OneOf([p.value for p in TaskPriority]))
    due_date = fields.DateTime()
    estimated_hours = fields.Float(validate=validate.Range(min=0))
    tag_ids = fields.List(fields.UUID())

class TaskUpdateSchema(Schema):
    """Schema for task updates"""
    
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str()
    assignee_id = fields.UUID(allow_none=True)
    status = fields.Str(validate=validate.OneOf([s.value for s in TaskStatus]))
    priority = fields.Str(validate=validate.OneOf([p.value for p in TaskPriority]))
    due_date = fields.DateTime(allow_none=True)
    estimated_hours = fields.Float(validate=validate.Range(min=0), allow_none=True)
    actual_hours = fields.Float(validate=validate.Range(min=0), allow_none=True)
    tag_ids = fields.List(fields.UUID())

class TaskStatusUpdateSchema(Schema):
    """Schema for task status updates"""
    
    status = fields.Str(required=True, validate=validate.OneOf([s.value for s in TaskStatus]))

class TaskAssignSchema(Schema):
    """Schema for task assignment"""
    
    assignee_id = fields.UUID(required=True)