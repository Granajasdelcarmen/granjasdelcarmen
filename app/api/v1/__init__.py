"""
API v1 Package - Initialize all controllers and namespaces
"""
from flask_restx import Api, Namespace
from flask import Blueprint

# Create Blueprint for API v1
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTX API
api = Api(
    api_v1_bp,
    version='1.0',
    title='Granjas del Carmen API',
    description='API para la gestión de granjas de conejos',
    doc='/docs/',  # Swagger UI will be available at /api/v1/docs/
    contact='Granjas del Carmen',
    contact_email='info@granjasdelcarmen.com',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT'
)

# Create namespaces for different API groups
auth_ns = Namespace('auth', description='Authentication endpoints')
users_ns = Namespace('users', description='User management endpoints')
rabbits_ns = Namespace('rabbits', description='Rabbit management endpoints')
cows_ns = Namespace('cows', description='Cow management endpoints')
sheep_ns = Namespace('sheep', description='Sheep management endpoints')
inventory_ns = Namespace('inventory', description='Inventory management endpoints')
inventory_products_ns = Namespace('inventory-products', description='Inventory products management endpoints')
events_ns = Namespace('events', description='Event management endpoints')
alerts_ns = Namespace('alerts', description='Alert management endpoints')
finance_ns = Namespace('finance', description='Financial management endpoints (admin only)')

# Add namespaces to API
api.add_namespace(auth_ns)
api.add_namespace(users_ns)
api.add_namespace(rabbits_ns)
api.add_namespace(cows_ns)
api.add_namespace(sheep_ns)
api.add_namespace(inventory_ns)
api.add_namespace(inventory_products_ns)
api.add_namespace(events_ns)
api.add_namespace(alerts_ns)
api.add_namespace(finance_ns)

# Import controllers to register routes
from app.api.v1 import auth_controller, user_controller, rabbit_controller, cow_controller, sheep_controller, inventory_controller, inventory_product_controller, health_controller, event_controller, alert_controller, finance_controller