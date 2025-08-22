"""
Task Views - Task management interface
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
import requests
from functools import wraps

task_views_bp = Blueprint('task_views', __name__, url_prefix='/tasks')

def login_required(f):
    """Decorator to require login for views"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth_views.login'))
        return f(*args, **kwargs)
    return decorated_function

@task_views_bp.route('/')
@login_required
def tasks_list():
    """List all tasks"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    # Get filter parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id')
    
    params = {}
    if status:
        params['status'] = status
    if priority:
        params['priority'] = priority
    if project_id:
        params['project_id'] = project_id
    
    response = requests.get(
        request.url_root + 'api/tasks',
        headers=headers,
        params=params
    )
    
    tasks = []
    if response.status_code == 200:
        tasks = response.json()['data']['tasks']
    
    # Get projects for filter dropdown
    projects_response = requests.get(
        request.url_root + 'api/projects',
        headers=headers
    )
    projects = projects_response.json()['data']['projects'] if projects_response.status_code == 200 else []
    
    return render_template('tasks/list.html', 
                         tasks=tasks,
                         projects=projects,
                         current_filters=params)

@task_views_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_task():
    """Create new task"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'project_id': request.form.get('project_id'),
            'assignee_id': request.form.get('assignee_id'),
            'status': request.form.get('status', 'todo'),
            'priority': request.form.get('priority', 'medium'),
            'due_date': request.form.get('due_date'),
            'estimated_hours': request.form.get('estimated_hours')
        }
        
        # Remove empty values
        data = {k: v for k, v in data.items() if v}
        
        response = requests.post(
            request.url_root + 'api/tasks',
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            flash('Task created successfully!', 'success')
            task_data = response.json()['data']
            return redirect(url_for('task_views.task_detail', task_id=task_data['id']))
        else:
            flash('Failed to create task', 'danger')
    
    # Get projects for dropdown
    projects_response = requests.get(
        request.url_root + 'api/projects',
        headers=headers
    )
    projects = projects_response.json()['data']['projects'] if projects_response.status_code == 200 else []
    
    return render_template('tasks/new.html', projects=projects)

@task_views_bp.route('/<task_id>')
@login_required
def task_detail(task_id):
    """View task details"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    # Get task details
    task_response = requests.get(
        f"{request.url_root}api/tasks/{task_id}",
        headers=headers
    )
    
    if task_response.status_code != 200:
        flash('Task not found', 'danger')
        return redirect(url_for('task_views.tasks_list'))
    
    task = task_response.json()['data']
    
    # Get task comments
    comments_response = requests.get(
        f"{request.url_root}api/comments/tasks/{task_id}/comments",
        headers=headers
    )
    comments = comments_response.json()['data']['comments'] if comments_response.status_code == 200 else []
    
    # Get task history
    history_response = requests.get(
        f"{request.url_root}api/tasks/{task_id}/history",
        headers=headers
    )
    history = history_response.json()['data']['activities'] if history_response.status_code == 200 else []
    
    return render_template('tasks/detail.html', 
                         task=task,
                         comments=comments,
                         history=history)

@task_views_bp.route('/<task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit task"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'status': request.form.get('status'),
            'priority': request.form.get('priority'),
            'due_date': request.form.get('due_date'),
            'estimated_hours': request.form.get('estimated_hours')
        }
        
        # Remove empty values
        data = {k: v for k, v in data.items() if v}
        
        response = requests.put(
            f"{request.url_root}api/tasks/{task_id}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            flash('Task updated successfully!', 'success')
            return redirect(url_for('task_views.task_detail', task_id=task_id))
        else:
            flash('Failed to update task', 'danger')
    
    # Get current task data
    response = requests.get(
        f"{request.url_root}api/tasks/{task_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        flash('Task not found', 'danger')
        return redirect(url_for('task_views.tasks_list'))
    
    task = response.json()['data']
    return render_template('tasks/edit.html', task=task)

@task_views_bp.route('/<task_id>/status', methods=['POST'])
@login_required
def update_task_status(task_id):
    """Update task status (AJAX endpoint)"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    data = {'status': request.json.get('status')}
    
    response = requests.put(
        f"{request.url_root}api/tasks/{task_id}/status",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return jsonify({'success': True, 'message': 'Status updated'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update status'}), 400

@task_views_bp.route('/<task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    """Add comment to task"""
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    
    data = {'content': request.form.get('content')}
    
    response = requests.post(
        f"{request.url_root}api/comments/tasks/{task_id}/comments",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        flash('Comment added successfully!', 'success')
    else:
        flash('Failed to add comment', 'danger')
    
    return redirect(url_for('task_views.task_detail', task_id=task_id))