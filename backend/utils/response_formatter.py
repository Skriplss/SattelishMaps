"""
Standardized API response formatters
"""
from typing import Any, Optional, Dict, List
from datetime import datetime


def success_response(
    data: Any,
    message: str = "Success",
    meta: Optional[Dict] = None
) -> Dict:
    """
    Format successful API response
    
    Args:
        data: Response data
        message: Success message
        meta: Additional metadata (pagination, etc.)
    
    Returns:
        Formatted response dict
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if meta:
        response["meta"] = meta
    
    return response


def paginated_response(
    data: List[Any],
    page: int,
    limit: int,
    total: int,
    message: str = "Success"
) -> Dict:
    """
    Format paginated API response
    
    Args:
        data: List of items
        page: Current page number
        limit: Items per page
        total: Total number of items
        message: Success message
    
    Returns:
        Formatted response with pagination metadata
    """
    total_pages = (total + limit - 1) // limit  # Ceiling division
    
    return success_response(
        data=data,
        message=message,
        meta={
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    )


def error_response(
    error: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict] = None
) -> Dict:
    """
    Format error API response
    
    Args:
        error: Error type/code
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Formatted error response
    """
    response = {
        "success": False,
        "error": error,
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def created_response(
    data: Any,
    message: str = "Resource created successfully"
) -> Dict:
    """Format response for created resources"""
    return success_response(data=data, message=message)


def deleted_response(message: str = "Resource deleted successfully") -> Dict:
    """Format response for deleted resources"""
    return success_response(data=None, message=message)


def no_content_response() -> Dict:
    """Format response for operations with no content"""
    return success_response(data=None, message="Operation completed successfully")
