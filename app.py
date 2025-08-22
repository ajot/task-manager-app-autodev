#!/usr/bin/env python3
"""
Task Manager Application - Main Flask Application Entry Point
"""

import os
from flask import Flask
from app import create_app, db
from app.models import *  # Import all models for migrations

# Create the Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Add database and models to shell context"""
    return {
        'db': db,
        'User': User,
        'Project': Project,
        'Task': Task,
        'Comment': Comment,
        'Tag': Tag,
        'TaskTag': TaskTag,
        'ProjectMember': ProjectMember,
        'ActivityLog': ActivityLog
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)