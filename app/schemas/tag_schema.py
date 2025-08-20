from marshmallow import Schema, fields, validate
from app import ma
from app.models import Tag

class TagSchema(ma.SQLAlchemyAutoSchema):
    """Tag serialization schema"""
    
    class Meta:
        model = Tag
        load_instance = True
        dump_only_fields = ('id', 'created_at', 'updated_at')
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    
    # Relationships
    project = fields.Nested('ProjectSchema', only=('id', 'name'), dump_only=True)

class TagCreateSchema(Schema):
    """Schema for tag creation"""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    project_id = fields.UUID()  # Optional for global tags

class TagUpdateSchema(Schema):
    """Schema for tag updates"""
    
    name = fields.Str(validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))