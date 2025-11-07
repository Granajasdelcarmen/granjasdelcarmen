"""
Authentication API controller
"""
from flask_restx import Resource, fields
from flask import session, url_for
from urllib.parse import quote_plus, urlencode
from app.config.settings import Config
from app.api.v1 import auth_ns, api

# Auth0 client (will be injected)
oauth = None

def init_auth_controller(oauth_client):
    """Initialize auth controller with oauth client"""
    global oauth
    oauth = oauth_client

# API Models
login_url_model = api.model('LoginUrl', {
    'loginUrl': fields.String(description='Auth0 login URL')
})

logout_url_model = api.model('LogoutUrl', {
    'logoutUrl': fields.String(description='Auth0 logout URL')
})

auth_user_model = api.model('AuthUser', {
    'sub': fields.String(description='User ID from Auth0'),
    'email': fields.String(description='User email'),
    'name': fields.String(description='User full name'),
    'picture': fields.String(description='User profile picture URL'),
    'email_verified': fields.Boolean(description='Email verification status'),
    'role': fields.String(description='Application role (admin/user/viewer)')
})

@auth_ns.route('/login-url')
class AuthLoginUrl(Resource):
    @auth_ns.doc('get_login_url')
    @auth_ns.marshal_with(login_url_model)
    def get(self):
        """Get backend /login absolute URL for redirection"""
        # We redirect via backend /login which handles Auth0 flow
        login_absolute = url_for("login", _external=True)
        return {"loginUrl": login_absolute}

@auth_ns.route('/logout-url')
class AuthLogoutUrl(Resource):
    @auth_ns.doc('get_logout_url')
    @auth_ns.marshal_with(logout_url_model)
    def get(self):
        """Get Auth0 logout URL for frontend redirection"""
        return {
            "logoutUrl": (
                "https://"
                + Config.AUTH0_DOMAIN
                + "/v2/logout?"
                + urlencode(
                    {
                        "returnTo": Config.FRONTEND_URL,
                        "client_id": Config.AUTH0_CLIENT_ID,
                    },
                    quote_via=quote_plus,
                )
            )
        }

@auth_ns.route('/me')
class AuthMe(Resource):
    @auth_ns.doc('get_current_user')
    @auth_ns.marshal_with(auth_user_model)
    def get(self):
        """Get current authenticated user information"""
        # Get user from session first
        session_user = session.get("user")
        if not session_user or not session_user.get("sub"):
            return None
        
        # Get fresh user data from database to ensure role is up-to-date
        try:
            from app.services.user_service import UserService
            service = UserService()
            
            response_data, status_code = service.get_user_by_id(session_user.get("sub"))
            
            if status_code == 200:
                # Response format: {"message": "...", "data": {...}}
                # Extract user data from response
                user_data = response_data.get("data") if isinstance(response_data, dict) else response_data
                
                if isinstance(user_data, dict):
                    # Update session with fresh role from database
                    session_user["role"] = user_data.get("role", "user")
                    session["user"] = session_user
                    return session_user
                else:
                    # Invalid response format, return session user
                    return session_user
            else:
                # User not found in DB, return session user with default role
                return session_user
        except Exception as e:
            # Fallback to session user if DB query fails
            import logging
            from app.utils.logger import Logger
            Logger.error(f"Error getting user from DB: {e}", exc_info=e)
            return session_user
