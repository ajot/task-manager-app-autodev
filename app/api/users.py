"""
User management API endpoints
"""

from flask import Blueprint, request
from app import db
from app.models import User
from app.schemas import UserSchema, UserUpdateSchema, ChangePasswordSchema
from app.utils.responses import success_response, error_response
from app.utils.decorators import jwt_required_with_user
from app.utils.helpers import validate_json, get_or_404, paginate_query

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required_with_user
def get_profile(current_user):
    """
    Get current user profile
    
    GET /api/users/profile
    """
    user_schema = UserSchema()
    user_data = user_schema.dump(current_user)
    
    return success_response(
        data=user_data,
        message="Profile retrieved successfully"
    )

@users_bp.route('/profile', methods=['PUT'])
@jwt_required_with_user
@validate_json(UserUpdateSchema)
def update_profile(current_user, validated_data):
    """
    Update current user profile
    
    PUT /api/users/profile
    {
        "full_name": "John Doe Updated",
        "avatar_url": "https://example.com/avatar.jpg"
    }
    """
    try:
        # Update user fields
        for field, value in validated_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        db.session.commit()
        
        user_schema = UserSchema()
        user_data = user_schema.dump(current_user)
        
        return success_response(
            data=user_data,
            message="Profile updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Profile update failed: {str(e)}", status_code=500)

@users_bp.route('/change-password', methods=['PUT'])
@jwt_required_with_user
@validate_json(ChangePasswordSchema)
def change_password(current_user, validated_data):
    """
    Change user password
    
    PUT /api/users/change-password
    {
        "current_password": "oldpassword",
        "new_password": "newpassword"
    }
    """
    current_password = validated_data['current_password']
    new_password = validated_data['new_password']
    
    # Verify current password
    if not current_user.check_password(current_password):
        return error_response("Current password is incorrect", status_code=400)
    
    try:
        # Set new password
        current_user.set_password(new_password)
        db.session.commit()
        
        return success_response(message="Password changed successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Password change failed: {str(e)}", status_code=500)

@users_bp.route('/search', methods=['GET'])
@jwt_required_with_user
def search_users(current_user):
    """
    Search users by username or email
    
    GET /api/users/search?q=search_term&page=1&per_page=20
    """
    search_term = request.args.get('q', '').strip()
    if not search_term:
        return error_response("Search term is required", status_code=400)
    
    if len(search_term) < 2:
        return error_response("Search term must be at least 2 characters", status_code=400)
    
    # Build search query
    search_pattern = f"%{search_term}%"
    query = User.query.filter(
        (User.username.ilike(search_pattern)) |
        (User.email.ilike(search_pattern)) |
        (User.full_name.ilike(search_pattern))
    ).filter(User.is_active == True)
    
    # Paginate results
    pagination_data = paginate_query(query)
    
    # Serialize users
    user_schema = UserSchema(many=True)
    users_data = user_schema.dump(pagination_data['items'])
    
    return success_response(
        data={
            'users': users_data,
            'pagination': {
                'page': pagination_data['page'],
                'per_page': pagination_data['per_page'],
                'total': pagination_data['total'],
                'pages': (pagination_data['total'] + pagination_data['per_page'] - 1) // pagination_data['per_page']
            }
        },
        message="Users retrieved successfully"
    )

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required_with_user
def get_user(current_user, user_id):
    """
    Get user by ID
    
    GET /api/users/{user_id}
    """
    user = get_or_404(User, user_id)
    
    if not user.is_active:
        return error_response("User not found", status_code=404)
    
    user_schema = UserSchema()
    user_data = user_schema.dump(user)
    
    return success_response(
        data=user_data,
        message="User retrieved successfully"
    )

@users_bp.route('/profile', methods=['DELETE'])
@jwt_required_with_user
def delete_account(current_user):
    """
    Delete current user account (soft delete)
    
    DELETE /api/users/profile
    """
    try:
        # Soft delete by deactivating account
        current_user.is_active = False
        db.session.commit()
        
        return success_response(message="Account deactivated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Account deletion failed: {str(e)}", status_code=500)

@users_bp.route('/upload-avatar', methods=['POST'])
@jwt_required_with_user
def upload_avatar(current_user):
    """
    Upload user avatar
    
    POST /api/users/upload-avatar
    Content-Type: multipart/form-data
    """
    # TODO: Implement file upload with proper validation and storage
    return error_response("Avatar upload not yet implemented", status_code=501)