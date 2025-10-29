"""
Granjas del Carmen - Main Server Entry Point
Refactored for scalability and maintainability
"""
import os
from app import create_app
from app.config.settings import config

def main():
    """Main application entry point"""
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'default')
    
    # Create application
    app = create_app(config_name)
    
    # Get configuration
    app_config = config[config_name]
    
    # Run application
    app.run(
        host=app_config.HOST,
        port=app_config.PORT,
        debug=app_config.DEBUG
    )

if __name__ == "__main__":
    main()
