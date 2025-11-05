"""
Authentication and Authorization Decorators
Provides decorators for securing endpoints
"""
from functools import wraps
from flask import request, session
from typing import Optional, Callable
from app.utils.auth import get_current_user, get_current_user_role, is_admin
from app.utils.response import error_response
from models import Role


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication
    Checks if user is authenticated via session or X-User-ID header
    
    Usage:
        @require_auth
        def my_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session first (for cookie-based auth)
        user = get_current_user()
        
        # If no session, check X-User-ID header
        if not user:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return error_response("Authentication required", 401)
            
            # Get user from database by header ID
            try:
                from app.services.user_service import UserService
                service = UserService()
                response_data, status_code = service.get_user_by_id(user_id)
                
                if status_code != 200:
                    return error_response("Invalid user ID", 401)
                
                user_data = response_data.get("data") if isinstance(response_data, dict) else response_data
                if not isinstance(user_data, dict):
                    return error_response("Invalid user data", 401)
                
                # Store user in request context for this request
                request.current_user = user_data
                request.current_user_id = user_id
            except Exception:
                return error_response("Authentication failed", 401)
        else:
            # Store user from session in request context
            request.current_user = user
            request.current_user_id = user.get("sub")
        
        return f(*args, **kwargs)
    return decorated_function


def require_role(*allowed_roles: Role):
    """
    Decorator to require specific roles
    Must be used after @require_auth
    
    Usage:
        @require_auth
        @require_role(Role.ADMIN)
        def admin_only_endpoint():
            ...
        
        @require_auth
        @require_role(Role.ADMIN, Role.USER)
        def admin_or_user_endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user from request context (set by @require_auth)
            user = getattr(request, 'current_user', None)
            
            if not user:
                # Try to get from session
                user = get_current_user()
                if not user:
                    return error_response("Authentication required", 401)
            
            # Get role from user
            role_str = user.get("role")
            if not role_str:
                return error_response("User role not found", 403)
            
            try:
                user_role = Role(role_str.lower())
            except ValueError:
                return error_response("Invalid user role", 403)
            
            # Check if user has required role
            if user_role not in allowed_roles:
                return error_response(
                    f"Access denied. Required roles: {', '.join([r.value for r in allowed_roles])}", 
                    403
                )
            
            # Store role in request context
            request.current_user_role = user_role
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f: Callable) -> Callable:
    """
    Decorator to require admin role
    Must be used after @require_auth
    
    Usage:
        @require_auth
        @require_admin
        def admin_only_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from request context (set by @require_auth)
        user = getattr(request, 'current_user', None)
        
        if not user:
            # Try to get from session
            user = get_current_user()
            if not user:
                return error_response("Authentication required", 401)
        
        # Check if user is admin
        if not is_admin():
            # Double check with role from user
            role_str = user.get("role", "").lower()
            if role_str != "admin":
                return error_response("Only administrators can perform this action", 403)
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id() -> Optional[str]:
    """
    Get current user ID from request context or session
    Should be called after @require_auth decorator
    
    Returns:
        User ID (Auth0 sub) or None
    """
    # Try request context first (set by @require_auth)
    user_id = getattr(request, 'current_user_id', None)
    if user_id:
        return user_id
    
    # Fallback to session
    user = get_current_user()
    if user:
        return user.get("sub")
    
    return None


def validate_auth_and_role(allowed_roles: Optional[list] = None) -> tuple:
    """
    Validate authentication and optionally check role
    Helper function for use in Resource methods
    
    Args:
        allowed_roles: List of allowed roles (Role enum values). None = any authenticated user
    
    Returns:
        Tuple of (user_dict, error_response) or (None, None) if valid
        If error_response is not None, return it from the endpoint
    """
    # Check session first (for cookie-based auth)
    user = get_current_user()
    
    # If no session, check X-User-ID header
    if not user:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return None, error_response("Authentication required", 401)
        
        # Get user from database by header ID
        try:
            from app.services.user_service import UserService
            service = UserService()
            response_data, status_code = service.get_user_by_id(user_id)
            
            if status_code != 200:
                return None, error_response("Invalid user ID", 401)
            
            user_data = response_data.get("data") if isinstance(response_data, dict) else response_data
            if not isinstance(user_data, dict):
                return None, error_response("Invalid user data", 401)
            
            user = user_data
        except Exception as e:
            import logging
            logging.error(f"Error validating auth: {e}")
            return None, error_response("Authentication failed", 401)
    
    # If roles are specified, check role
    if allowed_roles:
        role_str = user.get("role", "").lower()
        try:
            user_role = Role(role_str)
            if user_role not in allowed_roles:
                role_names = [r.value for r in allowed_roles]
                return None, error_response(
                    f"Access denied. Required roles: {', '.join(role_names)}", 
                    403
                )
        except ValueError:
            return None, error_response("Invalid user role", 403)
    
    return user, None


def get_request_user_role() -> Optional[Role]:
    """
    Get current user role from request context
    Should be called after @require_auth decorator
    
    Returns:
        User Role enum or None
    """
    # Try request context first (set by @require_role)
    role = getattr(request, 'current_user_role', None)
    if role:
        return role
    
    # Fallback to session
    return get_current_user_role()

