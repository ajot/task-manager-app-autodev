"""
Standardized API response utilities
"""

from flask import jsonify
from typing import Any, Dict, List, Optional

def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

def error_response(message: str = "An error occurred", errors: List[str] = None, status_code: int = 400) -> tuple:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        errors: List of detailed errors
        status_code: HTTP status code
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": False,
        "message": message,
        "errors": errors or []
    }
    return jsonify(response), status_code

def paginated_response(
    items: List[Any], 
    page: int, 
    per_page: int, 
    total: int, 
    message: str = "Success"
) -> tuple:
    """
    Create a standardized paginated response
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    pages = (total + per_page - 1) // per_page  # Ceiling division
    
    response = {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    }
    return jsonify(response), 200

def validation_error_response(errors: Dict[str, List[str]]) -> tuple:
    """
    Create a validation error response from Marshmallow errors
    
    Args:
        errors: Dictionary of field errors from Marshmallow
        
    Returns:
        Tuple of (response, status_code)
    """
    formatted_errors = []
    for field, messages in errors.items():
        for message in messages:
            formatted_errors.append(f"{field}: {message}")
    
    return error_response(
        message="Validation failed",
        errors=formatted_errors,
        status_code=422
    )