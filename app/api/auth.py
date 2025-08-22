"""
Authentication API endpoints
"""

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User
from app.schemas import UserCreateSchema, UserLoginSchema, UserSchema
from app.utils.responses import success_response, error_response, validation_error_response
from app.utils.helpers import validate_json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@validate_json(UserCreateSchema)
def register(validated_data):
    """
    User registration endpoint
    
    POST /api/auth/register
    {
        "username": "johndoe",
        "email": "john@example.com", 
        "password": "securepassword",
        "full_name": "John Doe"
    }
    """
    try:
        # Create new user
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data.get('full_name')
        )
        user.set_password(validated_data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Serialize user data
        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        
        response_data = {
            'user': user_data,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        
        return success_response(
            data=response_data,
            message="User registered successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Registration failed: {str(e)}", status_code=500)

@auth_bp.route('/login', methods=['POST'])
@validate_json(UserLoginSchema)
def login(validated_data):
    """
    User login endpoint
    
    POST /api/auth/login
    {
        "username_or_email": "johndoe",
        "password": "securepassword",
        "remember_me": false
    }
    """
    username_or_email = validated_data['username_or_email']
    password = validated_data['password']
    remember_me = validated_data.get('remember_me', False)
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | 
        (User.email == username_or_email)
    ).first()
    
    if not user or not user.check_password(password):
        return error_response("Invalid credentials", status_code=401)
    
    if not user.is_active:
        return error_response("Account is deactivated", status_code=401)
    
    # Update last login
    user.update_last_login()
    
    # Generate tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # Serialize user data
    user_schema = UserSchema()
    user_data = user_schema.dump(user)
    
    response_data = {
        'user': user_data,
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    
    return success_response(
        data=response_data,
        message="Login successful"
    )

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token endpoint
    
    POST /api/auth/refresh
    Headers: Authorization: Bearer <refresh_token>
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return error_response("Invalid user", status_code=401)
    
    # Generate new access token
    access_token = create_access_token(identity=str(user.id))
    
    return success_response(
        data={'access_token': access_token},
        message="Token refreshed successfully"
    )

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user profile
    
    GET /api/auth/me
    Headers: Authorization: Bearer <access_token>
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return error_response("User not found", status_code=404)
    
    user_schema = UserSchema()
    user_data = user_schema.dump(user)
    
    return success_response(
        data=user_data,
        message="User profile retrieved successfully"
    )

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint
    
    POST /api/auth/logout
    Headers: Authorization: Bearer <access_token>
    
    Note: In a production environment, you would want to blacklist the token
    """
    # TODO: Implement token blacklisting with Redis
    return success_response(message="Logout successful")

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiate password reset
    
    POST /api/auth/forgot-password
    {
        "email": "john@example.com"
    }
    """
    if not request.is_json:
        return error_response("Content-Type must be application/json", status_code=400)
    
    email = request.json.get('email')
    if not email:
        return error_response("Email is required", status_code=400)
    
    user = User.query.filter_by(email=email).first()
    
    # Always return success to prevent email enumeration
    if user:
        # TODO: Generate reset token and send email
        pass
    
    return success_response(
        message="If the email exists, a password reset link has been sent"
    )

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Complete password reset
    
    POST /api/auth/reset-password
    {
        "token": "reset_token",
        "new_password": "newsecurepassword"
    }
    """
    if not request.is_json:
        return error_response("Content-Type must be application/json", status_code=400)
    
    # TODO: Implement password reset token validation
    return error_response("Password reset not yet implemented", status_code=501)