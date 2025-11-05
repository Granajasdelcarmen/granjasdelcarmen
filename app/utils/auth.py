"""
Authentication utilities
Helper functions for authentication and authorization
"""
from flask import session
from typing import Optional, Dict, Any
from models import Role


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from session
    
    Returns:
        User dictionary from session or None if not authenticated
    """
    return session.get("user")


def get_current_user_role() -> Optional[Role]:
    """
    Get current user's role from session
    
    Returns:
        User role (Role enum) or None if not authenticated
    """
    user = get_current_user()
    if not user:
        return None
    
    role_str = user.get("role")
    if not role_str:
        return None
    
    try:
        return Role(role_str.lower())
    except ValueError:
        return None


def is_admin() -> bool:
    """
    Check if current user is admin
    
    Returns:
        True if user is admin, False otherwise
    """
    role = get_current_user_role()
    return role == Role.ADMIN


def require_admin() -> tuple:
    """
    Check if current user is admin, return error if not
    
    Returns:
        Tuple of (error_response, status_code) if not admin, None if admin
    """
    if not is_admin():
        from app.utils.response import error_response
        return error_response("Only administrators can perform this action", 403)
    return None

