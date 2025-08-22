"""
Comments API endpoints
"""

from flask import Blueprint
from app import db
from app.models import Comment, Task, Project, ProjectMember, ActivityLog, ActivityAction
from app.schemas import CommentSchema, CommentCreateSchema, CommentUpdateSchema
from app.utils.responses import success_response, error_response
from app.utils.decorators import jwt_required_with_user
from app.utils.helpers import validate_json, get_or_404, paginate_query

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/tasks/<task_id>/comments', methods=['GET'])
@jwt_required_with_user
def get_task_comments(current_user, task_id):
    """
    Get comments for a task
    
    GET /api/comments/tasks/{task_id}/comments?page=1&per_page=20
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
    
    # Get comments with pagination
    query = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.asc())
    pagination_data = paginate_query(query)
    
    # Serialize comments
    comment_schema = CommentSchema(many=True)
    comments_data = comment_schema.dump(pagination_data['items'])
    
    return success_response(
        data={
            'comments': comments_data,
            'pagination': {
                'page': pagination_data['page'],
                'per_page': pagination_data['per_page'],
                'total': pagination_data['total'],
                'pages': (pagination_data['total'] + pagination_data['per_page'] - 1) // pagination_data['per_page']
            }
        },
        message="Comments retrieved successfully"
    )

@comments_bp.route('/tasks/<task_id>/comments', methods=['POST'])
@jwt_required_with_user
@validate_json(CommentCreateSchema)
def create_comment(current_user, task_id, validated_data):
    """
    Add comment to task
    
    POST /api/comments/tasks/{task_id}/comments
    {
        "content": "This is a comment"
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
        if not member:
            return error_response("Access denied", status_code=403)
    
    try:
        comment = Comment(
            task_id=task_id,
            user_id=current_user.id,
            content=validated_data['content']
        )
        
        db.session.add(comment)
        db.session.flush()  # Get comment ID
        
        # Log activity
        ActivityLog.log_activity(
            user=current_user,
            project=project,
            task=task,
            action=ActivityAction.COMMENTED,
            details={'comment_preview': validated_data['content'][:100]}
        )
        
        db.session.commit()
        
        comment_schema = CommentSchema()
        comment_data = comment_schema.dump(comment)
        
        return success_response(
            data=comment_data,
            message="Comment added successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Comment creation failed: {str(e)}", status_code=500)

@comments_bp.route('/<comment_id>', methods=['PUT'])
@jwt_required_with_user
@validate_json(CommentUpdateSchema)
def update_comment(current_user, comment_id, validated_data):
    """
    Edit comment
    
    PUT /api/comments/{comment_id}
    {
        "content": "Updated comment content"
    }
    """
    comment = get_or_404(Comment, comment_id)
    
    # Only comment author can edit
    if comment.user_id != current_user.id:
        return error_response("You can only edit your own comments", status_code=403)
    
    try:
        comment.content = validated_data['content']
        comment.mark_edited()
        
        db.session.commit()
        
        comment_schema = CommentSchema()
        comment_data = comment_schema.dump(comment)
        
        return success_response(
            data=comment_data,
            message="Comment updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Comment update failed: {str(e)}", status_code=500)

@comments_bp.route('/<comment_id>', methods=['DELETE'])
@jwt_required_with_user
def delete_comment(current_user, comment_id):
    """
    Delete comment
    
    DELETE /api/comments/{comment_id}
    """
    comment = get_or_404(Comment, comment_id)
    
    # Check if user can delete (author or project admin/owner)
    can_delete = False
    
    if comment.user_id == current_user.id:
        can_delete = True
    else:
        # Check if user is project admin/owner
        task = comment.task
        project = task.project
        
        if project.owner_id == current_user.id:
            can_delete = True
        else:
            member = ProjectMember.query.filter_by(
                project_id=project.id,
                user_id=current_user.id
            ).first()
            if member and member.role.value == 'admin':
                can_delete = True
    
    if not can_delete:
        return error_response("Insufficient permissions to delete comment", status_code=403)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        
        return success_response(message="Comment deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Comment deletion failed: {str(e)}", status_code=500)