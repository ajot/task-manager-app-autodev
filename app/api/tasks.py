"""
Task management API endpoints
"""

from flask import Blueprint, request
from datetime import datetime
from app import db
from app.models import Task, Project, User, Tag, TaskTag, TaskStatus, TaskPriority, ActivityLog, ActivityAction
from app.schemas import TaskSchema, TaskCreateSchema, TaskUpdateSchema, TaskStatusUpdateSchema, TaskAssignSchema
from app.utils.responses import success_response, error_response
from app.utils.decorators import jwt_required_with_user, permission_required
from app.utils.helpers import validate_json, get_or_404, paginate_query, get_request_filters, apply_task_filters

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required_with_user
def list_tasks(current_user):
    """
    List all tasks with filtering and pagination
    
    GET /api/tasks?project_id=xxx&status=todo&priority=high&assignee_id=xxx&page=1&per_page=20
    """
    # Base query for user's accessible tasks
    query = Task.query.join(Project).filter(
        (Project.owner_id == current_user.id) |
        (Project.id.in_(
            db.session.query(db.session.query(ProjectMember.project_id).filter_by(
                user_id=current_user.id
            ).subquery())
        ))
    )
    
    # Apply filters
    if request.args.get('project_id'):
        query = query.filter(Task.project_id == request.args.get('project_id'))
    
    filters = get_request_filters()
    query = apply_task_filters(query, filters)
    
    # Order by updated_at
    query = query.order_by(Task.updated_at.desc())
    
    # Paginate
    pagination_data = paginate_query(query)
    
    # Serialize tasks
    task_schema = TaskSchema(many=True)
    tasks_data = task_schema.dump(pagination_data['items'])
    
    return success_response(
        data={
            'tasks': tasks_data,
            'pagination': {
                'page': pagination_data['page'],
                'per_page': pagination_data['per_page'],
                'total': pagination_data['total'],
                'pages': (pagination_data['total'] + pagination_data['per_page'] - 1) // pagination_data['per_page']
            }
        },
        message="Tasks retrieved successfully"
    )

@tasks_bp.route('', methods=['POST'])
@jwt_required_with_user
@validate_json(TaskCreateSchema)
def create_task(current_user, validated_data):
    """
    Create a new task
    
    POST /api/tasks
    {
        "title": "Task Title",
        "description": "Task description",
        "project_id": "project-uuid",
        "assignee_id": "user-uuid",
        "status": "todo",
        "priority": "medium",
        "due_date": "2024-01-30T10:00:00Z",
        "estimated_hours": 8.0,
        "tag_ids": ["tag-uuid1", "tag-uuid2"]
    }
    """
    project_id = validated_data['project_id']
    
    # Check if user has permission to create tasks in this project
    project = get_or_404(Project, project_id)
    
    # Verify project access
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=current_user.id
        ).first()
        if not member or member.role == MemberRole.VIEWER:
            return error_response("Insufficient permissions to create tasks", status_code=403)
    
    try:
        task = Task(
            title=validated_data['title'],
            description=validated_data.get('description'),
            project_id=project_id,
            creator_id=current_user.id,
            assignee_id=validated_data.get('assignee_id'),
            status=TaskStatus(validated_data.get('status', 'todo')),
            priority=TaskPriority(validated_data.get('priority', 'medium')),
            due_date=validated_data.get('due_date'),
            estimated_hours=validated_data.get('estimated_hours')
        )
        
        db.session.add(task)
        db.session.flush()  # Get task ID
        
        # Add tags if provided
        tag_ids = validated_data.get('tag_ids', [])
        for tag_id in tag_ids:
            tag = get_or_404(Tag, tag_id)
            task_tag = TaskTag(task_id=task.id, tag_id=tag.id)
            db.session.add(task_tag)
        
        # Log activity
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            task=task,
            action=ActivityAction.CREATED,
            details={'task_title': task.title}
        )
        
        db.session.commit()
        
        task_schema = TaskSchema()
        task_data = task_schema.dump(task)
        
        return success_response(
            data=task_data,
            message="Task created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Task creation failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>', methods=['GET'])
@jwt_required_with_user
def get_task(current_user, task_id):
    """
    Get task details
    
    GET /api/tasks/{task_id}
    """
    task = get_or_404(Task, task_id)
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member:
            return error_response("Access denied", status_code=403)
    
    task_schema = TaskSchema()
    task_data = task_schema.dump(task)
    
    return success_response(
        data=task_data,
        message="Task retrieved successfully"
    )

@tasks_bp.route('/<task_id>', methods=['PUT'])
@jwt_required_with_user
@validate_json(TaskUpdateSchema)
def update_task(current_user, task_id, validated_data):
    """
    Update task
    
    PUT /api/tasks/{task_id}
    {
        "title": "Updated Task Title",
        "description": "Updated description",
        "status": "in_progress",
        "priority": "high"
    }
    """
    task = get_or_404(Task, task_id)
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member or member.role == MemberRole.VIEWER:
            return error_response("Insufficient permissions to update task", status_code=403)
    
    try:
        # Track changes for activity log
        changes = {}
        
        # Update task fields
        for field, value in validated_data.items():
            if field == 'tag_ids':
                continue  # Handle separately
            
            if hasattr(task, field):
                old_value = getattr(task, field)
                if field in ['status', 'priority'] and isinstance(value, str):
                    if field == 'status':
                        value = TaskStatus(value)
                    elif field == 'priority':
                        value = TaskPriority(value)
                
                if old_value != value:
                    changes[field] = {'old': str(old_value), 'new': str(value)}
                    setattr(task, field, value)
        
        # Handle tag updates
        if 'tag_ids' in validated_data:
            # Remove existing tags
            TaskTag.query.filter_by(task_id=task.id).delete()
            
            # Add new tags
            for tag_id in validated_data['tag_ids']:
                tag = get_or_404(Tag, tag_id)
                task_tag = TaskTag(task_id=task.id, tag_id=tag.id)
                db.session.add(task_tag)
        
        # Mark as completed if status changed to done
        if 'status' in changes and changes['status']['new'] == 'TaskStatus.DONE':
            task.completed_at = datetime.utcnow()
        
        # Log activity if there were changes
        if changes:
            ActivityLog.log_activity(
                user=current_user,
                project=project,
                task=task,
                action=ActivityAction.UPDATED,
                details={'changes': changes}
            )
        
        db.session.commit()
        
        task_schema = TaskSchema()
        task_data = task_schema.dump(task)
        
        return success_response(
            data=task_data,
            message="Task updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Task update failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>', methods=['DELETE'])
@jwt_required_with_user
def delete_task(current_user, task_id):
    """
    Delete task
    
    DELETE /api/tasks/{task_id}
    """
    task = get_or_404(Task, task_id)
    
    # Check project access and permissions
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member or member.role == MemberRole.VIEWER:
            return error_response("Insufficient permissions to delete task", status_code=403)
    
    try:
        # Log activity before deletion
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            action=ActivityAction.DELETED,
            details={'task_title': task.title, 'task_id': str(task.id)}
        )
        
        db.session.delete(task)
        db.session.commit()
        
        return success_response(message="Task deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Task deletion failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>/status', methods=['PUT'])
@jwt_required_with_user
@validate_json(TaskStatusUpdateSchema)
def update_task_status(current_user, task_id, validated_data):
    """
    Update task status
    
    PUT /api/tasks/{task_id}/status
    {
        "status": "in_progress"
    }
    """
    task = get_or_404(Task, task_id)
    new_status = TaskStatus(validated_data['status'])
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member:
            return error_response("Access denied", status_code=403)
    
    try:
        old_status = task.status
        task.status = new_status
        
        # Mark completion timestamp
        if new_status == TaskStatus.DONE:
            task.completed_at = datetime.utcnow()
        elif old_status == TaskStatus.DONE:
            task.completed_at = None
        
        # Log activity
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            task=task,
            action=ActivityAction.STATUS_CHANGED,
            details={
                'old_status': old_status.value,
                'new_status': new_status.value
            }
        )
        
        db.session.commit()
        
        task_schema = TaskSchema()
        task_data = task_schema.dump(task)
        
        return success_response(
            data=task_data,
            message="Task status updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Status update failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>/assign', methods=['PUT'])
@jwt_required_with_user
@validate_json(TaskAssignSchema)
def assign_task(current_user, task_id, validated_data):
    """
    Assign task to user
    
    PUT /api/tasks/{task_id}/assign
    {
        "assignee_id": "user-uuid"
    }
    """
    task = get_or_404(Task, task_id)
    assignee_id = validated_data['assignee_id']
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member or member.role == MemberRole.VIEWER:
            return error_response("Insufficient permissions to assign task", status_code=403)
    
    # Verify assignee exists and has project access
    assignee = get_or_404(User, assignee_id)
    if project.owner_id != assignee.id:
        assignee_member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=assignee_id
        ).first()
        if not assignee_member:
            return error_response("Assignee is not a project member", status_code=400)
    
    try:
        old_assignee_id = task.assignee_id
        task.assignee_id = assignee_id
        
        # Log activity
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            task=task,
            action=ActivityAction.ASSIGNED,
            details={
                'assignee_username': assignee.username,
                'old_assignee_id': str(old_assignee_id) if old_assignee_id else None
            }
        )
        
        db.session.commit()
        
        task_schema = TaskSchema()
        task_data = task_schema.dump(task)
        
        return success_response(
            data=task_data,
            message="Task assigned successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Task assignment failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>/complete', methods=['POST'])
@jwt_required_with_user
def complete_task(current_user, task_id):
    """
    Mark task as complete
    
    POST /api/tasks/{task_id}/complete
    """
    task = get_or_404(Task, task_id)
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member:
            return error_response("Access denied", status_code=403)
    
    try:
        task.mark_complete()
        
        # Log activity
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            task=task,
            action=ActivityAction.COMPLETED,
            details={'task_title': task.title}
        )
        
        db.session.commit()
        
        task_schema = TaskSchema()
        task_data = task_schema.dump(task)
        
        return success_response(
            data=task_data,
            message="Task marked as complete"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Task completion failed: {str(e)}", status_code=500)

@tasks_bp.route('/<task_id>/history', methods=['GET'])
@jwt_required_with_user
def get_task_history(current_user, task_id):
    """
    Get task activity history
    
    GET /api/tasks/{task_id}/history
    """
    task = get_or_404(Task, task_id)
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member:
            return error_response("Access denied", status_code=403)
    
    # Get activity logs for this task
    activities = ActivityLog.query.filter_by(task_id=task_id).order_by(
        ActivityLog.created_at.desc()
    ).all()
    
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': str(activity.id),
            'action': activity.action.value,
            'user': {
                'id': str(activity.user.id),
                'username': activity.user.username,
                'full_name': activity.user.full_name
            },
            'details': activity.details,
            'created_at': activity.created_at.isoformat()
        })
    
    return success_response(
        data={'activities': activities_data},
        message="Task history retrieved successfully"
    )