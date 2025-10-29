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
    
    # Initialize CORS
    CORS(app, supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'])
    
    # Initialize OAuth
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
        session["user"] = token
        return redirect("/")
    
    @app.route("/login")
    def login():
        nonlocal oauth_instance
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
        return redirect(
            "https://"
            + app.config['AUTH0_DOMAIN']
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": url_for("home", _external=True),
                    "client_id": app.config['AUTH0_CLIENT_ID'],
                },
                quote_via=quote_plus,
            )
        )