"""
API Blueprint package
"""

from flask import Blueprint

def create_api_blueprint():
    """Create and configure API blueprint"""
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    # Import and register route modules
    from app.api import auth, users, projects, tasks, comments, tags
    
    # Register sub-blueprints
    api_bp.register_blueprint(auth.auth_bp, url_prefix='/auth')
    api_bp.register_blueprint(users.users_bp, url_prefix='/users') 
    api_bp.register_blueprint(projects.projects_bp, url_prefix='/projects')
    api_bp.register_blueprint(tasks.tasks_bp, url_prefix='/tasks')
    api_bp.register_blueprint(comments.comments_bp, url_prefix='/comments')
    api_bp.register_blueprint(tags.tags_bp, url_prefix='/tags')
    
    return api_bp