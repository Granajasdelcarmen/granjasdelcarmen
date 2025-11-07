"""
Inventory Product API controller
"""
from flask_restx import Resource, fields
from flask import request
from app.services.inventory_product_service import InventoryProductService
from app.api.v1 import inventory_products_ns, api
from app.utils.decorators import validate_auth_and_role
from models import Role, InventoryStatus, InventoryProductType

# Initialize service
inventory_product_service = InventoryProductService()

# API Models
inventory_product_model = api.model('InventoryProduct', {
    'id': fields.String(description='Unique product identifier'),
    'product_type': fields.String(description='Product type'),
    'product_name': fields.String(description='Product name'),
    'quantity': fields.Float(description='Product quantity'),
    'unit': fields.String(description='Unit of measurement'),
    'production_date': fields.DateTime(description='Production date'),
    'expiration_date': fields.DateTime(description='Expiration date'),
    'location': fields.String(description='Storage location'),
    'unit_price': fields.Float(description='Price per unit'),
    'status': fields.String(description='Product status'),
    'animal_id': fields.String(description='Related animal ID'),
    'created_by': fields.String(description='User who created the product'),
    'notes': fields.String(description='Additional notes'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

inventory_product_create_model = api.model('InventoryProductCreate', {
    'product_type': fields.String(required=True, description='Product type (MEAT_RABBIT, EGGS, MILK, etc.)'),
    'product_name': fields.String(required=True, description='Product name'),
    'quantity': fields.Float(required=True, description='Product quantity'),
    'unit': fields.String(required=True, description='Unit (KG, LITERS, UNITS, etc.)'),
    'production_date': fields.String(description='Production date (YYYY-MM-DD)'),
    'expiration_date': fields.String(description='Expiration date (YYYY-MM-DD)'),
    'location': fields.String(description='Storage location'),
    'unit_price': fields.Float(description='Price per unit'),
    'animal_id': fields.String(description='Related animal ID'),
    'notes': fields.String(description='Additional notes'),
    'reason': fields.String(description='Reason for entry')
})

inventory_product_update_model = api.model('InventoryProductUpdate', {
    'product_name': fields.String(description='Product name'),
    'quantity': fields.Float(description='Product quantity'),
    'unit_price': fields.Float(description='Price per unit'),
    'location': fields.String(description='Storage location'),
    'expiration_date': fields.String(description='Expiration date (YYYY-MM-DD)'),
    'notes': fields.String(description='Additional notes')
})

sell_product_model = api.model('SellProduct', {
    'quantity': fields.Float(required=True, description='Quantity to sell'),
    'sale_id': fields.String(description='Sale ID if linked to a sale record')
})


@inventory_products_ns.route('/')
class InventoryProductList(Resource):
    @inventory_products_ns.doc('list_inventory_products')
    @inventory_products_ns.param('status', 'Filter by status (AVAILABLE, SOLD, EXPIRED, etc.)')
    @inventory_products_ns.param('product_type', 'Filter by product type (MEAT_RABBIT, EGGS, etc.)')
    @inventory_products_ns.param('location', 'Filter by location')
    def get(self):
        """List all inventory products with optional filters"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        status = request.args.get('status')
        product_type = request.args.get('product_type')
        location = request.args.get('location')
        
        status_enum = None
        if status:
            try:
                status_enum = InventoryStatus[status]
            except KeyError:
                pass
        
        product_type_enum = None
        if product_type:
            try:
                product_type_enum = InventoryProductType[product_type]
            except KeyError:
                pass
        
        data, status_code = inventory_product_service.list_products(
            status=status_enum,
            product_type=product_type_enum,
            location=location
        )
        return data, status_code


@inventory_products_ns.route('/<string:product_id>')
class InventoryProductDetail(Resource):
    @inventory_products_ns.doc('get_inventory_product')
    def get(self, product_id):
        """Get inventory product by ID"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data, status_code = inventory_product_service.get_product(product_id)
        return data, status_code
    
    @inventory_products_ns.doc('update_inventory_product')
    @inventory_products_ns.expect(inventory_product_update_model)
    def put(self, product_id):
        """Update inventory product"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER])
        if error:
            return error[0], error[1]
        
        product_data = request.get_json() or {}
        
        # Parse expiration_date if provided
        if 'expiration_date' in product_data and product_data['expiration_date']:
            from datetime import datetime
            try:
                product_data['expiration_date'] = datetime.fromisoformat(product_data['expiration_date'].replace('Z', '+00:00'))
            except:
                pass
        
        data, status_code = inventory_product_service.update_product(product_id, product_data)
        return data, status_code


@inventory_products_ns.route('/add')
class InventoryProductAdd(Resource):
    @inventory_products_ns.doc('create_inventory_product')
    @inventory_products_ns.expect(inventory_product_create_model)
    def post(self):
        """Create a new inventory product"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        user_id = user.get("sub") or user.get("id")
        if not user_id:
            return {'error': 'User ID not found'}, 401
        
        product_data = request.get_json() or {}
        
        # Parse dates if provided
        from datetime import datetime
        if 'production_date' in product_data and product_data['production_date']:
            try:
                product_data['production_date'] = datetime.fromisoformat(product_data['production_date'].replace('Z', '+00:00'))
            except:
                product_data['production_date'] = datetime.utcnow()
        
        if 'expiration_date' in product_data and product_data['expiration_date']:
            try:
                product_data['expiration_date'] = datetime.fromisoformat(product_data['expiration_date'].replace('Z', '+00:00'))
            except:
                pass
        
        # Convert string enums to enum objects
        if 'product_type' in product_data:
            try:
                product_data['product_type'] = InventoryProductType[product_data['product_type']]
            except KeyError:
                return {'error': f'Invalid product_type: {product_data["product_type"]}'}, 400
        
        if 'unit' in product_data:
            from models import InventoryUnit
            try:
                product_data['unit'] = InventoryUnit[product_data['unit']]
            except KeyError:
                return {'error': f'Invalid unit: {product_data["unit"]}'}, 400
        
        data, status_code = inventory_product_service.create_product(product_data, user_id)
        return data, status_code


@inventory_products_ns.route('/<string:product_id>/sell')
class InventoryProductSell(Resource):
    @inventory_products_ns.doc('sell_inventory_product')
    @inventory_products_ns.expect(sell_product_model)
    def post(self, product_id):
        """Mark product (or part of it) as sold"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER])
        if error:
            return error[0], error[1]
        
        user_id = user.get("sub") or user.get("id")
        if not user_id:
            return {'error': 'User ID not found'}, 401
        
        sale_data = request.get_json() or {}
        quantity = sale_data.get('quantity')
        sale_id = sale_data.get('sale_id')
        
        if not quantity or quantity <= 0:
            return {'error': 'Quantity is required and must be greater than 0'}, 400
        
        data, status_code = inventory_product_service.mark_as_sold(product_id, quantity, user_id, sale_id)
        return data, status_code


@inventory_products_ns.route('/<string:product_id>/transactions')
class InventoryProductTransactions(Resource):
    @inventory_products_ns.doc('get_product_transactions')
    def get(self, product_id):
        """Get all transactions for a product"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        data, status_code = inventory_product_service.get_transactions(product_id)
        return data, status_code


@inventory_products_ns.route('/expired')
class ExpiredProducts(Resource):
    @inventory_products_ns.doc('get_expired_products')
    def get(self):
        """Get all expired products"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER])
        if error:
            return error[0], error[1]
        
        data, status_code = inventory_product_service.get_expired_products()
        return data, status_code

