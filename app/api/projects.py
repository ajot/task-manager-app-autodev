"""
Project management API endpoints
"""

from flask import Blueprint, request
from app import db
from app.models import Project, ProjectMember, User, MemberRole
from app.schemas import ProjectSchema, ProjectCreateSchema, ProjectUpdateSchema, ProjectMemberSchema, ProjectMemberUpdateSchema
from app.utils.responses import success_response, error_response
from app.utils.decorators import jwt_required_with_user, permission_required
from app.utils.helpers import validate_json, get_or_404, paginate_query

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('', methods=['GET'])
@jwt_required_with_user
def list_projects(current_user):
    """
    List all user's projects
    
    GET /api/projects?page=1&per_page=20&archived=false
    """
    # Build query for user's projects (owned + member)
    owned_projects = Project.query.filter_by(owner_id=current_user.id)
    
    member_project_ids = db.session.query(ProjectMember.project_id).filter_by(
        user_id=current_user.id
    ).subquery()
    
    member_projects = Project.query.filter(
        Project.id.in_(member_project_ids)
    )
    
    # Combine queries
    query = owned_projects.union(member_projects)
    
    # Apply filters
    archived = request.args.get('archived', 'false').lower() == 'true'
    query = query.filter(Project.is_archived == archived)
    
    # Order by updated_at
    query = query.order_by(Project.updated_at.desc())
    
    # Paginate
    pagination_data = paginate_query(query)
    
    # Serialize projects
    project_schema = ProjectSchema(many=True)
    projects_data = project_schema.dump(pagination_data['items'])
    
    return success_response(
        data={
            'projects': projects_data,
            'pagination': {
                'page': pagination_data['page'],
                'per_page': pagination_data['per_page'],
                'total': pagination_data['total'],
                'pages': (pagination_data['total'] + pagination_data['per_page'] - 1) // pagination_data['per_page']
            }
        },
        message="Projects retrieved successfully"
    )

@projects_bp.route('', methods=['POST'])
@jwt_required_with_user
@validate_json(ProjectCreateSchema)
def create_project(current_user, validated_data):
    """
    Create a new project
    
    POST /api/projects
    {
        "name": "My Project",
        "description": "Project description",
        "color": "#FF5733",
        "icon": "project"
    }
    """
    try:
        project = Project(
            name=validated_data['name'],
            description=validated_data.get('description'),
            owner_id=current_user.id,
            color=validated_data.get('color'),
            icon=validated_data.get('icon')
        )
        
        db.session.add(project)
        db.session.commit()
        
        project_schema = ProjectSchema()
        project_data = project_schema.dump(project)
        
        return success_response(
            data=project_data,
            message="Project created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Project creation failed: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>', methods=['GET'])
@jwt_required_with_user
@permission_required('viewer')
def get_project(current_user, project, project_id):
    """
    Get project details
    
    GET /api/projects/{project_id}
    """
    project_schema = ProjectSchema()
    project_data = project_schema.dump(project)
    
    return success_response(
        data=project_data,
        message="Project retrieved successfully"
    )

@projects_bp.route('/<project_id>', methods=['PUT'])
@jwt_required_with_user
@permission_required('admin')
@validate_json(ProjectUpdateSchema)
def update_project(current_user, project, project_id, validated_data):
    """
    Update project
    
    PUT /api/projects/{project_id}
    {
        "name": "Updated Project Name",
        "description": "Updated description",
        "color": "#00FF00"
    }
    """
    try:
        # Update project fields
        for field, value in validated_data.items():
            if hasattr(project, field):
                setattr(project, field, value)
        
        db.session.commit()
        
        project_schema = ProjectSchema()
        project_data = project_schema.dump(project)
        
        return success_response(
            data=project_data,
            message="Project updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Project update failed: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>', methods=['DELETE'])
@jwt_required_with_user
def delete_project(current_user, project_id):
    """
    Delete project (only owner can delete)
    
    DELETE /api/projects/{project_id}
    """
    project = get_or_404(Project, project_id)
    
    # Only owner can delete
    if project.owner_id != current_user.id:
        return error_response("Only project owner can delete the project", status_code=403)
    
    try:
        # Soft delete by archiving
        project.is_archived = True
        db.session.commit()
        
        return success_response(message="Project deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Project deletion failed: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>/archive', methods=['POST'])
@jwt_required_with_user
@permission_required('admin')
def toggle_archive_project(current_user, project, project_id):
    """
    Archive or unarchive project
    
    POST /api/projects/{project_id}/archive
    """
    try:
        project.is_archived = not project.is_archived
        db.session.commit()
        
        action = "archived" if project.is_archived else "unarchived"
        return success_response(message=f"Project {action} successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Archive operation failed: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>/members', methods=['GET'])
@jwt_required_with_user
@permission_required('viewer')
def get_project_members(current_user, project, project_id):
    """
    Get project members
    
    GET /api/projects/{project_id}/members
    """
    members_query = db.session.query(ProjectMember, User).join(
        User, ProjectMember.user_id == User.id
    ).filter(ProjectMember.project_id == project_id)
    
    members_data = []
    for member, user in members_query.all():
        members_data.append({
            'user_id': str(user.id),
            'username': user.username,
            'full_name': user.full_name,
            'avatar_url': user.avatar_url,
            'role': member.role.value,
            'joined_at': member.joined_at.isoformat()
        })
    
    # Add project owner
    owner_data = {
        'user_id': str(project.owner.id),
        'username': project.owner.username,
        'full_name': project.owner.full_name,
        'avatar_url': project.owner.avatar_url,
        'role': 'owner',
        'joined_at': project.created_at.isoformat()
    }
    members_data.insert(0, owner_data)
    
    return success_response(
        data={'members': members_data},
        message="Project members retrieved successfully"
    )

@projects_bp.route('/<project_id>/members', methods=['POST'])
@jwt_required_with_user
@permission_required('admin')
@validate_json(ProjectMemberSchema)
def add_project_member(current_user, project, project_id, validated_data):
    """
    Add member to project
    
    POST /api/projects/{project_id}/members
    {
        "user_id": "user-uuid",
        "role": "member"
    }
    """
    user_id = validated_data['user_id']
    role = validated_data.get('role', 'member')
    
    # Check if user exists
    user = get_or_404(User, user_id)
    
    # Check if already a member
    existing_member = ProjectMember.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()
    
    if existing_member:
        return error_response("User is already a project member", status_code=400)
    
    # Cannot add owner as member
    if str(project.owner_id) == str(user_id):
        return error_response("Project owner cannot be added as member", status_code=400)
    
    try:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=MemberRole(role)
        )
        
        db.session.add(member)
        db.session.commit()
        
        return success_response(
            message=f"User added to project as {role}",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to add member: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>/members/<user_id>', methods=['PUT'])
@jwt_required_with_user
@permission_required('admin')
@validate_json(ProjectMemberUpdateSchema)
def update_member_role(current_user, project, project_id, user_id, validated_data):
    """
    Update project member role
    
    PUT /api/projects/{project_id}/members/{user_id}
    {
        "role": "admin"
    }
    """
    new_role = validated_data['role']
    
    member = ProjectMember.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()
    
    if not member:
        return error_response("User is not a project member", status_code=404)
    
    try:
        member.role = MemberRole(new_role)
        db.session.commit()
        
        return success_response(message=f"Member role updated to {new_role}")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update member role: {str(e)}", status_code=500)

@projects_bp.route('/<project_id>/members/<user_id>', methods=['DELETE'])
@jwt_required_with_user
@permission_required('admin')
def remove_project_member(current_user, project, project_id, user_id):
    """
    Remove member from project
    
    DELETE /api/projects/{project_id}/members/{user_id}
    """
    # Cannot remove project owner
    if str(project.owner_id) == str(user_id):
        return error_response("Cannot remove project owner", status_code=400)
    
    member = ProjectMember.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()
    
    if not member:
        return error_response("User is not a project member", status_code=404)
    
    try:
        db.session.delete(member)
        db.session.commit()
        
        return success_response(message="Member removed from project")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to remove member: {str(e)}", status_code=500)