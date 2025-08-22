from marshmallow import Schema, fields, validate
from app import ma
from app.models import Comment

class CommentSchema(ma.SQLAlchemyAutoSchema):
    """Comment serialization schema"""
    
    class Meta:
        model = Comment
        load_instance = True
        dump_only_fields = ('id', 'created_at', 'updated_at', 'is_edited')
    
    content = fields.Str(required=True, validate=validate.Length(min=1))
    
    # Relationships
    user = fields.Nested('UserSchema', only=('id', 'username', 'full_name', 'avatar_url'), dump_only=True)
    task = fields.Nested('TaskSchema', only=('id', 'title'), dump_only=True)

class CommentCreateSchema(Schema):
    """Schema for comment creation"""
    
    content = fields.Str(required=True, validate=validate.Length(min=1))
    task_id = fields.UUID(required=True)

class CommentUpdateSchema(Schema):
    """Schema for comment updates"""
    
    content = fields.Str(required=True, validate=validate.Length(min=1))