"""
Tags API endpoints
"""

from flask import Blueprint, request
from app import db
from app.models import Tag, Project, ProjectMember, Task, TaskTag
from app.schemas import TagSchema, TagCreateSchema, TagUpdateSchema
from app.utils.responses import success_response, error_response
from app.utils.decorators import jwt_required_with_user, permission_required
from app.utils.helpers import validate_json, get_or_404, paginate_query

tags_bp = Blueprint('tags', __name__)

@tags_bp.route('', methods=['GET'])
@jwt_required_with_user
def list_tags(current_user):
    """
    List all tags accessible to user
    
    GET /api/tags?project_id=xxx&page=1&per_page=20
    """
    # Base query for user's accessible tags
    query = Tag.query
    
    # Filter by project if specified
    project_id = request.args.get('project_id')
    if project_id:
        project = get_or_404(Project, project_id)
        
        # Check project access
        if project.owner_id != current_user.id:
            member = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=current_user.id
            ).first()
            if not member:
                return error_response("Access denied", status_code=403)
        
        query = query.filter(Tag.project_id == project_id)
    else:
        # Show global tags + tags from accessible projects
        from sqlalchemy import or_
        
        # Get accessible project IDs
        owned_project_ids = db.session.query(Project.id).filter_by(owner_id=current_user.id)
        member_project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id)
        
        accessible_project_ids = owned_project_ids.union(member_project_ids).subquery()
        
        query = query.filter(
            or_(
                Tag.project_id.is_(None),  # Global tags
                Tag.project_id.in_(accessible_project_ids)
            )
        )
    
    # Order by name
    query = query.order_by(Tag.name)
    
    # Paginate
    pagination_data = paginate_query(query)
    
    # Serialize tags
    tag_schema = TagSchema(many=True)
    tags_data = tag_schema.dump(pagination_data['items'])
    
    return success_response(
        data={
            'tags': tags_data,
            'pagination': {
                'page': pagination_data['page'],
                'per_page': pagination_data['per_page'],
                'total': pagination_data['total'],
                'pages': (pagination_data['total'] + pagination_data['per_page'] - 1) // pagination_data['per_page']
            }
        },
        message="Tags retrieved successfully"
    )

@tags_bp.route('', methods=['POST'])
@jwt_required_with_user
@validate_json(TagCreateSchema)
def create_tag(current_user, validated_data):
    """
    Create a new tag
    
    POST /api/tags
    {
        "name": "Bug",
        "color": "#FF0000",
        "project_id": "project-uuid"  // Optional for global tags
    }
    """
    project_id = validated_data.get('project_id')
    
    # If project_id provided, check permissions
    if project_id:
        project = get_or_404(Project, project_id)
        
        if project.owner_id != current_user.id:
            member = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=current_user.id
            ).first()
            if not member or member.role.value == 'viewer':
                return error_response("Insufficient permissions to create tags", status_code=403)
    
    try:
        # Check for duplicate tag name in same scope
        existing_tag = Tag.query.filter_by(
            name=validated_data['name'],
            project_id=project_id
        ).first()
        
        if existing_tag:
            scope = "project" if project_id else "global"
            return error_response(f"Tag '{validated_data['name']}' already exists in {scope} scope", status_code=400)
        
        tag = Tag(
            name=validated_data['name'],
            color=validated_data.get('color'),
            project_id=project_id
        )
        
        db.session.add(tag)
        db.session.commit()
        
        tag_schema = TagSchema()
        tag_data = tag_schema.dump(tag)
        
        return success_response(
            data=tag_data,
            message="Tag created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Tag creation failed: {str(e)}", status_code=500)

@tags_bp.route('/<tag_id>', methods=['PUT'])
@jwt_required_with_user
@validate_json(TagUpdateSchema)
def update_tag(current_user, tag_id, validated_data):
    """
    Update tag
    
    PUT /api/tags/{tag_id}
    {
        "name": "Updated Bug",
        "color": "#FF5733"
    }
    """
    tag = get_or_404(Tag, tag_id)
    
    # Check permissions
    if tag.project_id:
        project = tag.project
        if project.owner_id != current_user.id:
            member = ProjectMember.query.filter_by(
                project_id=tag.project_id,
                user_id=current_user.id
            ).first()
            if not member or member.role.value == 'viewer':
                return error_response("Insufficient permissions to update tag", status_code=403)
    # Global tags can only be updated by system admins (not implemented yet)
    else:
        return error_response("Cannot update global tags", status_code=403)
    
    try:
        # Check for duplicate name if name is being changed
        if 'name' in validated_data and validated_data['name'] != tag.name:
            existing_tag = Tag.query.filter_by(
                name=validated_data['name'],
                project_id=tag.project_id
            ).first()
            
            if existing_tag:
                return error_response(f"Tag '{validated_data['name']}' already exists", status_code=400)
        
        # Update tag fields
        for field, value in validated_data.items():
            if hasattr(tag, field):
                setattr(tag, field, value)
        
        db.session.commit()
        
        tag_schema = TagSchema()
        tag_data = tag_schema.dump(tag)
        
        return success_response(
            data=tag_data,
            message="Tag updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Tag update failed: {str(e)}", status_code=500)

@tags_bp.route('/<tag_id>', methods=['DELETE'])
@jwt_required_with_user
def delete_tag(current_user, tag_id):
    """
    Delete tag
    
    DELETE /api/tags/{tag_id}
    """
    tag = get_or_404(Tag, tag_id)
    
    # Check permissions
    if tag.project_id:
        project = tag.project
        if project.owner_id != current_user.id:
            member = ProjectMember.query.filter_by(
                project_id=tag.project_id,
                user_id=current_user.id
            ).first()
            if not member or member.role.value == 'viewer':
                return error_response("Insufficient permissions to delete tag", status_code=403)
    else:
        return error_response("Cannot delete global tags", status_code=403)
    
    try:
        db.session.delete(tag)
        db.session.commit()
        
        return success_response(message="Tag deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Tag deletion failed: {str(e)}", status_code=500)

@tags_bp.route('/tasks/<task_id>/tags', methods=['POST'])
@jwt_required_with_user
def add_tag_to_task(current_user, task_id):
    """
    Add tags to task
    
    POST /api/tags/tasks/{task_id}/tags
    {
        "tag_ids": ["tag-uuid1", "tag-uuid2"]
    }
    """
    if not request.is_json or 'tag_ids' not in request.json:
        return error_response("tag_ids array is required", status_code=400)
    
    task = get_or_404(Task, task_id)
    tag_ids = request.json['tag_ids']
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member or member.role.value == 'viewer':
            return error_response("Insufficient permissions to modify task tags", status_code=403)
    
    try:
        added_tags = []
        for tag_id in tag_ids:
            tag = get_or_404(Tag, tag_id)
            
            # Check if tag can be applied to this task
            if tag.project_id and tag.project_id != project.id:
                return error_response(f"Tag '{tag.name}' belongs to a different project", status_code=400)
            
            # Check if already applied
            existing = TaskTag.query.filter_by(task_id=task_id, tag_id=tag_id).first()
            if not existing:
                task_tag = TaskTag(task_id=task_id, tag_id=tag_id)
                db.session.add(task_tag)
                added_tags.append(tag.name)
        
        db.session.commit()
        
        message = f"Added tags: {', '.join(added_tags)}" if added_tags else "No new tags added"
        return success_response(message=message)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to add tags: {str(e)}", status_code=500)

@tags_bp.route('/tasks/<task_id>/tags/<tag_id>', methods=['DELETE'])
@jwt_required_with_user
def remove_tag_from_task(current_user, task_id, tag_id):
    """
    Remove tag from task
    
    DELETE /api/tags/tasks/{task_id}/tags/{tag_id}
    """
    task = get_or_404(Task, task_id)
    tag = get_or_404(Tag, tag_id)
    
    # Check project access
    project = task.project
    if project.owner_id != current_user.id:
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=current_user.id
        ).first()
        if not member or member.role.value == 'viewer':
            return error_response("Insufficient permissions to modify task tags", status_code=403)
    
    try:
        task_tag = TaskTag.query.filter_by(task_id=task_id, tag_id=tag_id).first()
        if not task_tag:
            return error_response("Tag is not applied to this task", status_code=404)
        
        db.session.delete(task_tag)
        db.session.commit()
        
        return success_response(message=f"Tag '{tag.name}' removed from task")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to remove tag: {str(e)}", status_code=500)