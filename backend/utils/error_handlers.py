"""
Custom exceptions and error handlers
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


# Custom Exceptions
class SatelliteDataError(Exception):
    """Base exception for satellite data operations"""
    pass


class CopernicusAPIError(SatelliteDataError):
    """Copernicus API related errors"""
    pass


class SupabaseError(SatelliteDataError):
    """Supabase database errors"""
    pass


class ImageProcessingError(SatelliteDataError):
    """Image processing errors"""
    pass


class NotFoundError(SatelliteDataError):
    """Resource not found"""
    pass


class ValidationError(SatelliteDataError):
    """Validation errors"""
    pass


# Error Response Formatters
def format_error_response(
    error: str,
    message: str,
    status_code: int,
    details: dict = None
) -> dict:
    """Format error response"""
    response = {
        "success": False,
        "error": error,
        "message": message,
        "status_code": status_code
    }
    if details:
        response["details"] = details
    return response


# Exception Handlers
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            error="validation_error",
            message="Invalid request parameters",
            status_code=422,
            details={"errors": errors}
        )
    )


async def copernicus_api_exception_handler(request: Request, exc: CopernicusAPIError):
    """Handle Copernicus API errors"""
    logger.error(f"Copernicus API error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=format_error_response(
            error="copernicus_api_error",
            message="Failed to fetch data from Copernicus API",
            status_code=503,
            details={"reason": str(exc)}
        )
    )


async def supabase_exception_handler(request: Request, exc: SupabaseError):
    """Handle Supabase errors"""
    logger.error(f"Supabase error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error="database_error",
            message="Database operation failed",
            status_code=500,
            details={"reason": str(exc)}
        )
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle not found errors"""
    logger.info(f"Resource not found: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=format_error_response(
            error="not_found",
            message=str(exc),
            status_code=404
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.exception(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error="internal_server_error",
            message="An unexpected error occurred",
            status_code=500
        )
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(CopernicusAPIError, copernicus_api_exception_handler)
    app.add_exception_handler(SupabaseError, supabase_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
