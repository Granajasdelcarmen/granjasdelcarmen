"""
Application Configuration
"""
import os
from dotenv import find_dotenv, load_dotenv

# Load environment variables
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-key")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    
    # Auth0 Configuration
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 3000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    CORS_SUPPORTS_CREDENTIALS = True
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # OAuth redirections work with top-level GET; Lax is adequate in dev
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
