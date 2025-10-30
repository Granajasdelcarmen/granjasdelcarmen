"""
Granjas del Carmen - Main Application Factory
"""
from flask import Flask
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from app.config.settings import config
from app.utils.database import engine
from models import Base
import os

def create_app(config_name='default'):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration name (development, production, default)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='../templates')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Cookies de sesión seguras si usas dominios distintos/https:
    # app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    # app.config['SESSION_COOKIE_SECURE'] = True

    # Initialize CORS con origen explícito del frontend y credenciales
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": app.config['FRONTEND_URL']}}
    )
    
    # Feature flag: enable auth only if all Auth0 vars are provided
    app.config['AUTH_ENABLED'] = bool(
        app.config.get('AUTH0_DOMAIN')
        and app.config.get('AUTH0_CLIENT_ID')
        and app.config.get('AUTH0_CLIENT_SECRET')
    )

    # Initialize OAuth if enabled
    oauth = None
    if app.config['AUTH_ENABLED']:
        oauth = OAuth(app)
        oauth.register(
            "auth0",
            client_id=app.config['AUTH0_CLIENT_ID'],
            client_secret=app.config['AUTH0_CLIENT_SECRET'],
            client_kwargs={
                "scope": "openid profile email",
            },
            server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
        )
    
    # Create database tables
    Base.metadata.create_all(engine)
    
    # Register blueprints
    from app.api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp)
    
    # Initialize auth controller with oauth client
    from app.api.v1.auth_controller import init_auth_controller
    init_auth_controller(oauth)
    
    # Register main routes
    register_main_routes(app)
    
    return app

def register_main_routes(app):
    """Register main application routes"""
    from flask import render_template, session, redirect, url_for, jsonify
    from urllib.parse import quote_plus, urlencode
    import json
    from app.config.settings import config as settings_config
    
    # Store oauth instance for use in routes
    oauth_instance = None
    
    @app.route("/")
    def home():
        return render_template(
            "home.html",
            session=session.get("user"),
            pretty=json.dumps(session.get("user"), indent=4),
        )
    
    @app.route("/callback", methods=["GET", "POST"])
    def callback():
        nonlocal oauth_instance
        if not app.config.get('AUTH_ENABLED'):
            return jsonify({'error': 'Auth is disabled in this environment'}), 400
        if not oauth_instance:
            oauth_instance = OAuth(app)
            oauth_instance.register(
                "auth0",
                client_id=app.config['AUTH0_CLIENT_ID'],
                client_secret=app.config['AUTH0_CLIENT_SECRET'],
                client_kwargs={
                    "scope": "openid profile email",
                },
                server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
            )
        token = oauth_instance.auth0.authorize_access_token()
        # Guardar claims del usuario (estable y seguro usando /userinfo)
        userinfo = oauth_instance.auth0.userinfo(token=token)
        # Enrich with app role from DB if available
        try:
            from app.services.user_service import UserService
            service = UserService()
            role = None
            email = userinfo.get("email")
            if email:
                user_data, status_code = service.get_user_by_email(email)
                if status_code == 200 and isinstance(user_data, dict):
                    role = user_data.get("role")
            session["user"] = {
                "sub": userinfo.get("sub"),
                "email": email,
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
                "email_verified": userinfo.get("email_verified"),
                "role": role or "user",
            }
        except Exception:
            session["user"] = {
                "sub": userinfo.get("sub"),
                "email": userinfo.get("email"),
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
                "email_verified": userinfo.get("email_verified"),
                "role": "user",
            }
        # Redirigir al FE para que éste haga /api/v1/auth/me
        # Determinar config actual de la app y obtener FRONTEND_URL
        app_config = settings_config[app.config.get('ENV', 'default')]
        return redirect(f"{app_config.FRONTEND_URL}/auth/callback")
    
    @app.route("/login")
    def login():
        nonlocal oauth_instance
        if not app.config.get('AUTH_ENABLED'):
            # In dev without Auth0, simulate login by redirecting to /dev/login
            return redirect(url_for('dev_login'))
        if not oauth_instance:
            oauth_instance = OAuth(app)
            oauth_instance.register(
                "auth0",
                client_id=app.config['AUTH0_CLIENT_ID'],
                client_secret=app.config['AUTH0_CLIENT_SECRET'],
                client_kwargs={
                    "scope": "openid profile email",
                },
                server_metadata_url=f'https://{app.config["AUTH0_DOMAIN"]}/.well-known/openid-configuration',
            )
        return oauth_instance.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
        )
    
    @app.route("/logout")
    def logout():
        session.clear()
        # Determinar config actual de la app y obtener FRONTEND_URL
        app_config = settings_config[app.config.get('ENV', 'default')]
        if not app.config.get('AUTH_ENABLED'):
            # Simplemente redirigir al FE si no hay Auth0
            return redirect(app_config.FRONTEND_URL)
        return redirect(
            "https://"
            + app.config['AUTH0_DOMAIN']
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": app_config.FRONTEND_URL,
                    "client_id": app.config['AUTH0_CLIENT_ID'],
                },
                quote_via=quote_plus,
            )
        )

    # Dev helpers when Auth is disabled
    @app.route("/dev/login")
    def dev_login():
        if app.config.get('AUTH_ENABLED'):
            return redirect(url_for('login'))
        session["user"] = {
            "sub": "dev|user",
            "email": "dev.user@example.com",
            "name": "Dev User",
            "picture": "",
            "email_verified": True,
        }
        app_config = settings_config[app.config.get('ENV', 'default')]
        return redirect(f"{app_config.FRONTEND_URL}/auth/callback")