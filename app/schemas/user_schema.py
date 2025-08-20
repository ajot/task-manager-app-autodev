from marshmallow import Schema, fields, validate, validates, ValidationError
from app import ma
from app.models import User

class UserSchema(ma.SQLAlchemyAutoSchema):
    """User serialization schema"""
    
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash',)
        dump_only_fields = ('id', 'created_at', 'updated_at', 'last_login')

    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    full_name = fields.Str(validate=validate.Length(max=100))
    avatar_url = fields.Url()

class UserCreateSchema(Schema):
    """Schema for user registration"""
    
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    full_name = fields.Str(validate=validate.Length(max=100))
    
    @validates('username')
    def validate_username(self, value):
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists')
    
    @validates('email')
    def validate_email(self, value):
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already registered')

class UserLoginSchema(Schema):
    """Schema for user login"""
    
    username_or_email = fields.Str(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(missing=False)

class UserUpdateSchema(Schema):
    """Schema for user profile updates"""
    
    full_name = fields.Str(validate=validate.Length(max=100))
    avatar_url = fields.Url()

class ChangePasswordSchema(Schema):
    """Schema for password change"""
    
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))