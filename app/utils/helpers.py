"""
Helper utility functions
"""

from flask import request, abort
from sqlalchemy.orm import Query
from typing import Type, Any, Dict, Optional
from app import db
from app.utils.responses import error_response, validation_error_response

def get_or_404(model: Type[db.Model], id_value: Any, message: str = None):
    """
    Get model instance by ID or return 404 error
    
    Args:
        model: SQLAlchemy model class
        id_value: ID value to search for
        message: Custom error message
        
    Returns:
        Model instance
        
    Raises:
        404 error if not found
    """
    instance = model.query.get(id_value)
    if not instance:
        error_msg = message or f"{model.__name__} not found"
        abort(404, description=error_msg)
    return instance

def validate_json(schema_class):
    """
    Decorator to validate JSON request data against a schema
    
    Args:
        schema_class: Marshmallow schema class
        
    Returns:
        Decorator function
    """
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return error_response("Content-Type must be application/json", status_code=400)
            
            schema = schema_class()
            try:
                validated_data = schema.load(request.json)
                return f(validated_data=validated_data, *args, **kwargs)
            except Exception as e:
                if hasattr(e, 'messages'):
                    return validation_error_response(e.messages)
                return error_response("Invalid JSON data", status_code=400)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def paginate_query(query: Query, page: int = None, per_page: int = None) -> Dict:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (from request if None)
        per_page: Items per page (from request if None)
        
    Returns:
        Dictionary with pagination info and items
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total
    }

def get_request_filters() -> Dict[str, Any]:
    """
    Extract common filters from request args
    
    Returns:
        Dictionary of filters
    """
    filters = {}
    
    # Date filters
    if request.args.get('created_after'):
        filters['created_after'] = request.args.get('created_after')
    if request.args.get('created_before'):
        filters['created_before'] = request.args.get('created_before')
    
    # Search filter
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    # Status filter
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    # Priority filter
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    
    # Assignee filter
    if request.args.get('assignee_id'):
        filters['assignee_id'] = request.args.get('assignee_id')
    
    return filters

def apply_task_filters(query: Query, filters: Dict[str, Any]) -> Query:
    """
    Apply filters to a task query
    
    Args:
        query: Base query
        filters: Dictionary of filters
        
    Returns:
        Filtered query
    """
    from app.models import Task, TaskStatus, TaskPriority
    
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        query = query.filter(
            Task.title.ilike(search_term) |
            Task.description.ilike(search_term)
        )
    
    if filters.get('status'):
        query = query.filter(Task.status == TaskStatus(filters['status']))
    
    if filters.get('priority'):
        query = query.filter(Task.priority == TaskPriority(filters['priority']))
    
    if filters.get('assignee_id'):
        query = query.filter(Task.assignee_id == filters['assignee_id'])
    
    if filters.get('created_after'):
        query = query.filter(Task.created_at >= filters['created_after'])
    
    if filters.get('created_before'):
        query = query.filter(Task.created_at <= filters['created_before'])
    
    return query