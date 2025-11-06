"""
Inventory API controller
"""
from flask_restx import Resource, fields
from flask import request
from app.services.inventory_service import InventoryService
from app.api.v1 import inventory_ns, api
from app.utils.decorators import validate_auth_and_role
from models import Role

# Initialize service
inventory_service = InventoryService()

# API Models
inventory_model = api.model('InventoryItem', {
    'id': fields.String(description='Unique item identifier'),
    'item': fields.String(description='Item name'),
    'quantity': fields.Integer(description='Item quantity'),
    'created_at': fields.DateTime(description='Item creation timestamp'),
    'updated_at': fields.DateTime(description='Item last update timestamp')
})

inventory_create_model = api.model('InventoryCreate', {
    'item': fields.String(required=True, description='Item name'),
    'quantity': fields.Integer(required=True, description='Item quantity')
})

inventory_update_model = api.model('InventoryUpdate', {
    'item': fields.String(description='Item name'),
    'quantity': fields.Integer(description='Item quantity')
})

quantity_update_model = api.model('QuantityUpdate', {
    'quantity': fields.Integer(required=True, description='New quantity value')
})

quantity_operation_model = api.model('QuantityOperation', {
    'amount': fields.Integer(required=True, description='Amount to add/subtract')
})

search_model = api.model('Search', {
    'search_term': fields.String(required=True, description='Search term')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

@inventory_ns.route('/')
class InventoryList(Resource):
    @inventory_ns.doc('list_inventory_items')
    def get(self):
        """Get list of all inventory items"""
        response_data, status_code = inventory_service.get_all_items()
        return response_data, status_code
    
    @inventory_ns.doc('create_inventory_item')
    @inventory_ns.expect(inventory_create_model)
    def post(self):
        """Create a new inventory item (admin/user only)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        item_data = request.get_json() or {}
        response_data, status_code = inventory_service.create_item(item_data)
        return response_data, status_code

@inventory_ns.route('/seed')
class InventorySeed(Resource):
    @inventory_ns.doc('seed_inventory_items')
    def get(self):
        """Create test inventory items for development"""
        response_data, status_code = inventory_service.seed_test_items()
        return response_data, status_code

@inventory_ns.route('/<string:item_id>')
class InventoryDetail(Resource):
    @inventory_ns.doc('get_inventory_item')
    def get(self, item_id):
        """Get inventory item by ID"""
        response_data, status_code = inventory_service.get_item_by_id(item_id)
        return response_data, status_code
    
    @inventory_ns.doc('update_inventory_item')
    @inventory_ns.expect(inventory_update_model)
    def put(self, item_id):
        """Update inventory item by ID (admin/user only)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        item_data = request.get_json() or {}
        response_data, status_code = inventory_service.update_item(item_id, item_data)
        return response_data, status_code
    
    @inventory_ns.doc('delete_inventory_item')
    def delete(self, item_id):
        """Delete inventory item by ID (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = inventory_service.delete_item(item_id)
        return response_data, status_code

@inventory_ns.route('/search')
class InventorySearch(Resource):
    @inventory_ns.doc('search_inventory_items')
    def get(self):
        """Search inventory items by name"""
        search_term = request.args.get('q', '')
        response_data, status_code = inventory_service.search_items(search_term)
        return response_data, status_code

@inventory_ns.route('/low-stock')
class InventoryLowStock(Resource):
    @inventory_ns.doc('get_low_stock_items')
    def get(self):
        """Get items with low stock"""
        threshold = request.args.get('threshold', 10, type=int)
        response_data, status_code = inventory_service.get_low_stock_items(threshold)
        return response_data, status_code

@inventory_ns.route('/high-stock')
class InventoryHighStock(Resource):
    @inventory_ns.doc('get_high_stock_items')
    def get(self):
        """Get items with high stock"""
        threshold = request.args.get('threshold', 100, type=int)
        response_data, status_code = inventory_service.get_high_stock_items(threshold)
        return response_data, status_code

@inventory_ns.route('/<string:item_id>/quantity')
class InventoryQuantity(Resource):
    @inventory_ns.doc('update_item_quantity')
    @inventory_ns.expect(quantity_update_model)
    def put(self, item_id):
        """Update item quantity (admin/user only)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data = request.get_json() or {}
        quantity = data.get('quantity')
        response_data, status_code = inventory_service.update_quantity(item_id, quantity)
        return response_data, status_code

@inventory_ns.route('/<string:item_id>/add')
class InventoryAddQuantity(Resource):
    @inventory_ns.doc('add_item_quantity')
    @inventory_ns.expect(quantity_operation_model)
    def post(self, item_id):
        """Add quantity to existing item (admin/user only)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data = request.get_json() or {}
        amount = data.get('amount')
        response_data, status_code = inventory_service.add_quantity(item_id, amount)
        return response_data, status_code

@inventory_ns.route('/<string:item_id>/subtract')
class InventorySubtractQuantity(Resource):
    @inventory_ns.doc('subtract_item_quantity')
    @inventory_ns.expect(quantity_operation_model)
    def post(self, item_id):
        """Subtract quantity from existing item (admin/user only)"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data = request.get_json() or {}
        amount = data.get('amount')
        response_data, status_code = inventory_service.subtract_quantity(item_id, amount)
        return response_data, status_code
