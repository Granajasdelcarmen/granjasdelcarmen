"""
Response utilities for consistent API responses
"""
from typing import Any, Dict, Optional
from flask import jsonify

def success_response(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"message": message}
    if data is not None:
        response["data"] = data
    
    return response, status_code

def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None) -> tuple:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Optional error code
        
    Returns:
        Tuple of (error_dict, status_code)
    """
    error = {"error": message}
    if error_code:
        error["code"] = error_code
    
    return error, status_code

def validation_error_response(message: str) -> tuple:
    """
    Create a validation error response
    
    Args:
        message: Validation error message
        
    Returns:
        Tuple of (error_dict, 400)
    """
    return error_response(message, 400, "VALIDATION_ERROR")

def not_found_response(resource: str) -> tuple:
    """
    Create a not found error response
    
    Args:
        resource: Name of the resource that was not found
        
    Returns:
        Tuple of (error_dict, 404)
    """
    return error_response(f"{resource} not found", 404, "NOT_FOUND")

def server_error_response(message: str = "Internal server error") -> tuple:
    """
    Create a server error response
    
    Args:
        message: Error message
        
    Returns:
        Tuple of (error_dict, 500)
    """
    return error_response(message, 500, "SERVER_ERROR")
