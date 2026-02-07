"""
Standardized error handling utilities for all API endpoints.
Provides consistent error responses across all modules.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class APIErrorResponse:
    """
    Standardized error response class for consistent API error handling.
    Provides clear, actionable error messages for both developers and end users.
    """
    
    @staticmethod
    def database_error(
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Handle database-related errors with proper logging."""
        logger.error(f"Database error: {message}")
        if details:
            logger.error(f"Details: {details}")
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "database_error",
                "message": message,
                "status_code": 500,
                "details": details or {},
                "timestamp": logger.handlers[0].format(logger.makeRecord(
                    logger.name, logging.ERROR, __file__, 0, "", (), None
                )) if logger.handlers else None
            }
        )
    
    @staticmethod
    def validation_error(
        message: str = "Invalid input data",
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ) -> HTTPException:
        """Handle validation errors with specific field information."""
        logger.warning(f"Validation error: {message}")
        
        error_details = details or {}
        if field:
            error_details["invalid_field"] = field
            
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "validation_error",
                "message": message,
                "status_code": 422,
                "details": error_details
            }
        )
    
    @staticmethod
    def not_found_error(
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None
    ) -> HTTPException:
        """Handle resource not found errors."""
        logger.info(f"Resource not found: {message}")
        
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
            
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": message,
                "status_code": 404,
                "details": error_details
            }
        )
    
    @staticmethod
    def unauthorized_error(
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Handle authentication errors."""
        logger.warning(f"Unauthorized access attempt: {message}")
        
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": message,
                "status_code": 401,
                "details": details or {"action": "please_login_to_continue"}
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @staticmethod
    def forbidden_error(
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None,
        required_permission: Optional[str] = None
    ) -> HTTPException:
        """Handle authorization/permission errors."""
        logger.warning(f"Forbidden access attempt: {message}")
        
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
            
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": message,
                "status_code": 403,
                "details": error_details
            }
        )
    
    @staticmethod
    def conflict_error(
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
        conflicting_field: Optional[str] = None
    ) -> HTTPException:
        """Handle resource conflict errors (duplicates, etc.)."""
        logger.warning(f"Resource conflict: {message}")
        
        error_details = details or {}
        if conflicting_field:
            error_details["conflicting_field"] = conflicting_field
            
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": message,
                "status_code": 409,
                "details": error_details
            }
        )
    
    @staticmethod
    def business_rule_error(
        message: str = "Business rule violation",
        details: Optional[Dict[str, Any]] = None,
        rule: Optional[str] = None
    ) -> HTTPException:
        """Handle business logic rule violations."""
        logger.info(f"Business rule violation: {message}")
        
        error_details = details or {}
        if rule:
            error_details["violated_rule"] = rule
            
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "business_rule_violation",
                "message": message,
                "status_code": 400,
                "details": error_details
            }
        )
    
    @staticmethod
    def rate_limit_error(
        message: str = "Too many requests",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ) -> HTTPException:
        """Handle rate limiting errors."""
        logger.warning(f"Rate limit exceeded: {message}")
        
        error_details = details or {}
        if retry_after:
            error_details["retry_after_seconds"] = retry_after
            
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
            
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": message,
                "status_code": 429,
                "details": error_details
            },
            headers=headers
        )
    
    @staticmethod
    def service_unavailable_error(
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Handle service unavailability errors."""
        logger.error(f"Service unavailable: {message}")
        
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "service_unavailable",
                "message": message,
                "status_code": 503,
                "details": details or {"action": "please_try_again_later"}
            }
        )

def handle_database_exceptions(func):
    """
    Decorator to automatically handle common database exceptions.
    Use this decorator on functions that perform database operations.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
                raise APIErrorResponse.conflict_error(
                    message="Resource already exists with this data",
                    details={
                        "error": "duplicate_entry",
                        "action": "use_different_values_for_unique_fields"
                    }
                )
            else:
                raise APIErrorResponse.database_error(
                    message="Database integrity constraint violated",
                    details={
                        "error": "integrity_violation",
                        "action": "check_data_requirements"
                    }
                )
        except SQLAlchemyError as e:
            raise APIErrorResponse.database_error(
                message="Database operation failed",
                details={
                    "error": "database_transaction_failed",
                    "action": "try_again_or_contact_support"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise APIErrorResponse.database_error(
                message="An unexpected error occurred",
                details={
                    "error": "unexpected_error",
                    "function": func.__name__,
                    "action": "contact_support"
                }
            )
    return wrapper

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present and not empty.
    Raises validation error if any field is missing or empty.
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or (isinstance(data[field], str) and data[field].strip() == ""):
            empty_fields.append(field)
    
    if missing_fields or empty_fields:
        error_details = {}
        if missing_fields:
            error_details["missing_fields"] = missing_fields
        if empty_fields:
            error_details["empty_fields"] = empty_fields
        error_details["action"] = "provide_all_required_fields"
        
        raise APIErrorResponse.validation_error(
            message="Required fields are missing or empty",
            details=error_details
        )

def validate_user_permissions(user, required_roles: List[str]) -> None:
    """
    Validate that user has required role permissions.
    Raises forbidden error if user doesn't have required role.
    """
    if not user:
        raise APIErrorResponse.unauthorized_error(
            message="User authentication required"
        )
    
    if not hasattr(user, 'role') or not user.role:
        raise APIErrorResponse.forbidden_error(
            message="User role not found",
            details={
                "action": "contact_administrator_to_assign_role"
            }
        )
    
    if user.role.name not in required_roles:
        raise APIErrorResponse.forbidden_error(
            message="Insufficient permissions for this operation",
            details={
                "required_roles": required_roles,
                "current_role": user.role.name,
                "action": "contact_administrator_for_permission"
            },
            required_permission=f"requires_one_of_{required_roles}"
        )