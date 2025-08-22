#!/usr/bin/env python3
"""
Task Manager Application - Main Flask Application Entry Point
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app import create_app, db

# Create the Flask application
app = create_app()

# Initialize CORS
CORS(app)

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

@app.route('/health')
def health_check():
    """Health check endpoint for DigitalOcean App Platform"""
    return jsonify({
        'status': 'healthy',
        'message': 'Task Manager API is running',
        'version': '1.0.0'
    })

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Task Manager API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'users': '/api/users', 
            'projects': '/api/projects',
            'tasks': '/api/tasks',
            'comments': '/api/comments',
            'tags': '/api/tags'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)