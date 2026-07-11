"""
Standardized API response formatters
"""
from typing import Any, Optional, Dict
from datetime import datetime, timezone


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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if meta:
        response["meta"] = meta
    
    return response


