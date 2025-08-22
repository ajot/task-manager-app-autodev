"""
Dashboard Views - Main user dashboard
"""

from flask import Blueprint, render_template, redirect, url_for, session, request
import requests
from functools import wraps

dashboard_views_bp = Blueprint('dashboard_views', __name__)

def login_required(f):
    """Decorator to require login for views"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth_views.login'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_views_bp.route('/')
@dashboard_views_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    # Get user's projects
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    # Fetch projects
    projects_response = requests.get(
        request.url_root + 'api/projects',
        headers=headers
    )
    
    # Fetch recent tasks
    tasks_response = requests.get(
        request.url_root + 'api/tasks?per_page=10',
        headers=headers
    )
    
    projects = []
    tasks = []
    
    if projects_response.status_code == 200:
        projects = projects_response.json()['data']['projects']
    
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()['data']['tasks']
    
    # Calculate statistics
    stats = {
        'total_projects': len(projects),
        'total_tasks': len(tasks),
        'pending_tasks': len([t for t in tasks if t['status'] == 'todo']),
        'completed_tasks': len([t for t in tasks if t['status'] == 'done'])
    }
    
    return render_template('dashboard.html', 
                         user=session.get('user'),
                         projects=projects,
                         recent_tasks=tasks[:5],
                         stats=stats)