"""
Custom decorators for API endpoints
"""

from functools import wraps
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Project, ProjectMember, MemberRole
from app.utils.responses import error_response
from app.utils.helpers import get_or_404

def jwt_required_with_user(f):
    """
    JWT required decorator that also injects current user
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = get_or_404(User, current_user_id)
        return f(current_user=current_user, *args, **kwargs)
    return decorated_function

def permission_required(permission_level: str = 'member'):
    """
    Check if user has required permission level for a project
    
    Args:
        permission_level: Required permission ('viewer', 'member', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, project_id, *args, **kwargs):
            project = get_or_404(Project, project_id)
            
            # Project owner has all permissions
            if project.owner_id == current_user.id:
                return f(current_user=current_user, project=project, *args, **kwargs)
            
            # Check project membership
            membership = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=current_user.id
            ).first()
            
            if not membership:
                return error_response("Access denied: Not a project member", status_code=403)
            
            # Check permission level
            role_hierarchy = {
                'viewer': 1,
                'member': 2, 
                'admin': 3
            }
            
            required_level = role_hierarchy.get(permission_level, 2)
            user_level = role_hierarchy.get(membership.role.value, 1)
            
            if user_level < required_level:
                return error_response(f"Access denied: {permission_level} permission required", status_code=403)
            
            return f(current_user=current_user, project=project, *args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """
    Simple rate limiting decorator (placeholder for future implementation)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement actual rate limiting with Redis
            return f(*args, **kwargs)
        return decorated_function
    return decorator