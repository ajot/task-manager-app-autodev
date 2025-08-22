"""
Flask Views Module
"""

from flask import Blueprint

# Import all view blueprints
from .auth_views import auth_views_bp
from .dashboard_views import dashboard_views_bp
from .project_views import project_views_bp
from .task_views import task_views_bp

# List of all view blueprints to register
view_blueprints = [
    auth_views_bp,
    dashboard_views_bp,
    project_views_bp,
    task_views_bp
]