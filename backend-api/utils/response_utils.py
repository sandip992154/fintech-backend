"""
Response Utilities for BANDARU PAY API
=====================================

This module contains utility functions for creating standardized API responses.
"""

from datetime import datetime
from typing import Any, Optional, List, Dict
from fastapi import HTTPException
from fastapi.responses import JSONResponse


def create_success_response(
    message: str,
    data: Optional[Any] = None,
    status_code: int = 200
) -> JSONResponse:
    """Create a standardized success response"""
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "errors": None
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_error_response(
    message: str,
    errors: Optional[List[str]] = None,
    status_code: int = 500,
    data: Optional[Any] = None
) -> JSONResponse:
    """Create a standardized error response"""
    response_data = {
        "success": False,
        "message": message,
        "data": data,
        "errors": errors or [message],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_validation_error_response(
    message: str = "Validation failed",
    field_errors: Optional[Dict[str, str]] = None,
    status_code: int = 422
) -> JSONResponse:
    """Create a validation error response"""
    response_data = {
        "success": False,
        "message": message,
        "data": None,
        "errors": field_errors or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = "Data retrieved successfully"
) -> JSONResponse:
    """Create a paginated response"""
    pages = (total + size - 1) // size if size > 0 else 1
    has_next = page < pages
    has_prev = page > 1
    
    response_data = {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        },
        "timestamp": datetime.utcnow().isoformat(),
        "errors": None
    }
    
    return JSONResponse(
        status_code=200,
        content=response_data
    )


class APIException(HTTPException):
    """Custom API Exception with standardized error format"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        errors: Optional[List[str]] = None,
        data: Optional[Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors or [message]
        self.data = data
        
        detail = {
            "success": False,
            "message": message,
            "data": data,
            "errors": self.errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        super().__init__(status_code=status_code, detail=detail)