"""
Project Views - Project management interface
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import requests
from functools import wraps

project_views_bp = Blueprint('project_views', __name__, url_prefix='/projects')

def login_required(f):
    """Decorator to require login for views"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth_views.login'))
        return f(*args, **kwargs)
    return decorated_function

@project_views_bp.route('/')
@login_required
def projects_list():
    """List all projects"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    response = requests.get(
        request.url_root + 'api/projects',
        headers=headers
    )
    
    projects = []
    if response.status_code == 200:
        projects = response.json()['data']['projects']
    
    return render_template('projects/list.html', projects=projects)

@project_views_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Create new project"""
    if request.method == 'POST':
        headers = {'Authorization': f"Bearer {session['access_token']}"}
        
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'color': request.form.get('color', '#3498db')
        }
        
        response = requests.post(
            request.url_root + 'api/projects',
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            flash('Project created successfully!', 'success')
            return redirect(url_for('project_views.projects_list'))
        else:
            flash('Failed to create project', 'danger')
    
    return render_template('projects/new.html')

@project_views_bp.route('/<project_id>')
@login_required
def project_detail(project_id):
    """View project details"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    # Get project details
    project_response = requests.get(
        f"{request.url_root}api/projects/{project_id}",
        headers=headers
    )
    
    # Get project tasks
    tasks_response = requests.get(
        f"{request.url_root}api/tasks?project_id={project_id}",
        headers=headers
    )
    
    # Get project members
    members_response = requests.get(
        f"{request.url_root}api/projects/{project_id}/members",
        headers=headers
    )
    
    if project_response.status_code != 200:
        flash('Project not found', 'danger')
        return redirect(url_for('project_views.projects_list'))
    
    project = project_response.json()['data']
    tasks = tasks_response.json()['data']['tasks'] if tasks_response.status_code == 200 else []
    members = members_response.json()['data']['members'] if members_response.status_code == 200 else []
    
    return render_template('projects/detail.html', 
                         project=project,
                         tasks=tasks,
                         members=members)

@project_views_bp.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit project"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'color': request.form.get('color')
        }
        
        response = requests.put(
            f"{request.url_root}api/projects/{project_id}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            flash('Project updated successfully!', 'success')
            return redirect(url_for('project_views.project_detail', project_id=project_id))
        else:
            flash('Failed to update project', 'danger')
    
    # Get current project data
    response = requests.get(
        f"{request.url_root}api/projects/{project_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        flash('Project not found', 'danger')
        return redirect(url_for('project_views.projects_list'))
    
    project = response.json()['data']
    return render_template('projects/edit.html', project=project)