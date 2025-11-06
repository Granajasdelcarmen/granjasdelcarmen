"""
Finance API controller
"""
from flask_restx import Resource, fields
from flask import request
from app.services.product_sale_service import ProductSaleService
from app.services.expense_service import ExpenseService
from app.api.v1 import finance_ns, api
from app.utils.decorators import validate_auth_and_role, get_current_user_id
from models import Role

# Initialize services
product_sale_service = ProductSaleService()
expense_service = ExpenseService()

# API Models
product_sale_model = api.model('ProductSale', {
    'id': fields.String(description='Product sale ID'),
    'product_type': fields.String(description='Product type (miel, huevos, leche, otros)'),
    'quantity': fields.Float(description='Quantity sold'),
    'unit_price': fields.Float(description='Price per unit'),
    'total_price': fields.Float(description='Total price (quantity * unit_price)'),
    'sale_date': fields.DateTime(description='Sale date'),
    'customer_name': fields.String(description='Customer name (optional)'),
    'notes': fields.String(description='Additional notes'),
    'sold_by': fields.String(description='User ID who made the sale'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

product_sale_create_model = api.model('ProductSaleCreate', {
    'product_type': fields.String(required=True, enum=['miel', 'huevos', 'leche', 'otros'], description='Product type'),
    'quantity': fields.Float(required=True, description='Quantity sold'),
    'unit_price': fields.Float(required=True, description='Price per unit'),
    'sale_date': fields.String(required=True, description='Sale date (ISO format)'),
    'customer_name': fields.String(description='Customer name (optional)'),
    'notes': fields.String(description='Additional notes')
})

expense_model = api.model('Expense', {
    'id': fields.String(description='Expense ID'),
    'category': fields.String(description='Expense category'),
    'description': fields.String(description='Expense description'),
    'amount': fields.Float(description='Expense amount'),
    'expense_date': fields.DateTime(description='Expense date'),
    'vendor': fields.String(description='Vendor name (optional)'),
    'notes': fields.String(description='Additional notes'),
    'created_by': fields.String(description='User ID who created the expense'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

expense_create_model = api.model('ExpenseCreate', {
    'category': fields.String(required=True, enum=['alimentacion', 'medicamentos', 'mantenimiento', 'personal', 'servicios', 'equipos', 'otros'], description='Expense category'),
    'description': fields.String(required=True, description='Expense description'),
    'amount': fields.Float(required=True, description='Expense amount'),
    'expense_date': fields.String(required=True, description='Expense date (ISO format)'),
    'vendor': fields.String(description='Vendor name (optional)'),
    'notes': fields.String(description='Additional notes')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

# Product Sales Endpoints
@finance_ns.route('/product-sales')
class ProductSaleList(Resource):
    @finance_ns.doc('list_product_sales')
    @finance_ns.param('sort', 'Sort order by sale_date: asc (ascending) or desc (descending)')
    def get(self):
        """Get list of all product sales (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        sort_by = request.args.get('sort')
        if sort_by and sort_by not in ['asc', 'desc']:
            return {'error': 'Sort parameter must be "asc" or "desc"'}, 400
        
        response_data, status_code = product_sale_service.get_all_product_sales(sort_by)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        # If it's an error response, return it as is
        if isinstance(response_data, dict) and 'error' in response_data:
            return response_data, status_code
        
        return response_data, status_code
    
    @finance_ns.doc('create_product_sale')
    @finance_ns.expect(product_sale_create_model)
    def post(self):
        """Create a new product sale (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        user_id = get_current_user_id()
        if not user_id:
            return {'error': 'User ID not found'}, 401
        
        sale_data = request.get_json() or {}
        response_data, status_code = product_sale_service.create_product_sale(sale_data, user_id)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code

@finance_ns.route('/product-sales/<string:sale_id>')
class ProductSaleDetail(Resource):
    @finance_ns.doc('get_product_sale')
    def get(self, sale_id):
        """Get product sale by ID (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = product_sale_service.get_product_sale_by_id(sale_id)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code
    
    @finance_ns.doc('update_product_sale')
    @finance_ns.expect(product_sale_create_model)
    def put(self, sale_id):
        """Update product sale (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        sale_data = request.get_json() or {}
        response_data, status_code = product_sale_service.update_product_sale(sale_id, sale_data)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code
    
    @finance_ns.doc('delete_product_sale')
    def delete(self, sale_id):
        """Delete product sale (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = product_sale_service.delete_product_sale(sale_id)
        return response_data, status_code

# Expenses Endpoints
@finance_ns.route('/expenses')
class ExpenseList(Resource):
    @finance_ns.doc('list_expenses')
    @finance_ns.param('sort', 'Sort order by expense_date: asc (ascending) or desc (descending)')
    def get(self):
        """Get list of all expenses (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        sort_by = request.args.get('sort')
        if sort_by and sort_by not in ['asc', 'desc']:
            return {'error': 'Sort parameter must be "asc" or "desc"'}, 400
        
        response_data, status_code = expense_service.get_all_expenses(sort_by)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        # If it's an error response, return it as is
        if isinstance(response_data, dict) and 'error' in response_data:
            return response_data, status_code
        
        return response_data, status_code
    
    @finance_ns.doc('create_expense')
    @finance_ns.expect(expense_create_model)
    def post(self):
        """Create a new expense (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        user_id = get_current_user_id()
        if not user_id:
            return {'error': 'User ID not found'}, 401
        
        expense_data = request.get_json() or {}
        response_data, status_code = expense_service.create_expense(expense_data, user_id)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code

@finance_ns.route('/expenses/<string:expense_id>')
class ExpenseDetail(Resource):
    @finance_ns.doc('get_expense')
    def get(self, expense_id):
        """Get expense by ID (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = expense_service.get_expense_by_id(expense_id)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code
    
    @finance_ns.doc('update_expense')
    @finance_ns.expect(expense_create_model)
    def put(self, expense_id):
        """Update expense (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        expense_data = request.get_json() or {}
        response_data, status_code = expense_service.update_expense(expense_id, expense_data)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code
    
    @finance_ns.doc('delete_expense')
    def delete(self, expense_id):
        """Delete expense (admin only)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = expense_service.delete_expense(expense_id)
        
        # Extract data from response if it's wrapped in success_response format
        if isinstance(response_data, dict) and 'data' in response_data:
            return response_data['data'], status_code
        
        return response_data, status_code

