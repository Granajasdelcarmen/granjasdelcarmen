"""
Sheep API controller
Uses generic AnimalService with AnimalType.SHEEP
"""
from flask_restx import Resource, fields
from flask import request
from app.services.animal_service import AnimalService
from app.api.v1 import sheep_ns, api
from app.utils.decorators import validate_auth_and_role
from models import AnimalType, Role

# Initialize generic service
animal_service = AnimalService()
SPECIES = AnimalType.SHEEP

# API Models
sheep_model = api.model('Sheep', {
    'id': fields.String(description='Unique sheep identifier'),
    'name': fields.String(description='Sheep name'),
    'image': fields.String(description='Sheep image URL'),
    'birth_date': fields.DateTime(description='Sheep birth date'),
    'gender': fields.String(description='Sheep gender'),
    'discarded': fields.Boolean(description='Whether sheep is discarded'),
    'discarded_reason': fields.String(description='Reason for discarding'),
    'user_id': fields.String(description='Owner user ID'),
    'created_at': fields.DateTime(description='Sheep creation timestamp'),
    'updated_at': fields.DateTime(description='Sheep last update timestamp')
})

sheep_create_model = api.model('SheepCreate', {
    'name': fields.String(required=True, description='Sheep name'),
    'image': fields.String(description='Sheep image URL'),
    'birth_date': fields.String(required=True, description='Sheep birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Sheep gender'),
    'user_id': fields.String(description='Owner user ID')
})

sheep_update_model = api.model('SheepUpdate', {
    'name': fields.String(description='Sheep name'),
    'image': fields.String(description='Sheep image URL'),
    'birth_date': fields.String(description='Sheep birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Sheep gender'),
    'user_id': fields.String(description='Owner user ID')
})

sheep_discard_model = api.model('SheepDiscard', {
    'reason': fields.String(required=True, description='Reason for discarding the sheep (e.g., "Muerto", "Eliminado")')
})

sheep_sale_model = api.model('SheepSale', {
    'price': fields.Float(required=True, description='Sale price'),
    'weight': fields.Float(description='Weight at sale time'),
    'height': fields.Float(description='Height at sale time'),
    'notes': fields.String(description='Additional notes about the sale'),
    'sold_by': fields.String(required=True, description='User ID who made the sale'),
    'reason': fields.String(description='Reason for sale (defaults to "Vendido")')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

@sheep_ns.route('/')
class SheepList(Resource):
    @sheep_ns.doc('list_sheep')
    @sheep_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @sheep_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self):
        """Get list of all sheep with optional sorting by birth date and discarded filter"""
        sort_by = request.args.get('sort')
        if sort_by and sort_by not in ['asc', 'desc']:
            return {'error': 'Sort parameter must be "asc" or "desc"'}, 400
        
        # Parse discarded parameter (default: False = active only)
        discarded_param = request.args.get('discarded')
        discarded = False  # Default: show only active animals
        if discarded_param is not None:
            if discarded_param.lower() == 'true':
                discarded = True
            elif discarded_param.lower() == 'false':
                discarded = False
            elif discarded_param.lower() in ['null', 'all', '']:
                discarded = None  # Show all animals
        
        response_data, status_code = animal_service.get_all_animals(SPECIES, sort_by, discarded)
        return response_data, status_code

@sheep_ns.route('/add')
class SheepAdd(Resource):
    @sheep_ns.doc('add_sheep')
    @sheep_ns.expect(sheep_create_model)
    def post(self):
        """Add a new sheep"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        sheep_data = request.get_json() or {}
        # Basic validation: birth_date required
        if not sheep_data.get('birth_date'):
            return {'error': 'birth_date is required (YYYY-MM-DD)'}, 400
        response_data, status_code = animal_service.create_animal(SPECIES, sheep_data)
        return response_data, status_code

@sheep_ns.route('/<string:sheep_id>')
class SheepDetail(Resource):
    @sheep_ns.doc('get_sheep')
    def get(self, sheep_id):
        """Get sheep by ID"""
        response_data, status_code = animal_service.get_animal_by_id(SPECIES, sheep_id)
        return response_data, status_code
    
    @sheep_ns.doc('update_sheep')
    @sheep_ns.expect(sheep_update_model)
    def put(self, sheep_id):
        """Update sheep by ID"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        sheep_data = request.get_json() or {}
        response_data, status_code = animal_service.update_animal(SPECIES, sheep_id, sheep_data)
        return response_data, status_code
    
    @sheep_ns.doc('delete_sheep')
    def delete(self, sheep_id):
        """Delete sheep by ID"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = animal_service.delete_animal(SPECIES, sheep_id)
        return response_data, status_code

@sheep_ns.route('/<string:sheep_id>/discard')
class SheepDiscard(Resource):
    @sheep_ns.doc('discard_sheep')
    @sheep_ns.expect(sheep_discard_model)
    def post(self, sheep_id):
        """Discard a sheep (mark as discarded without sale)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        data = request.get_json() or {}
        reason = data.get('reason')
        
        if not reason:
            return {'error': 'reason is required'}, 400
        
        response_data, status_code = animal_service.discard_animal(SPECIES, sheep_id, reason)
        return response_data, status_code

@sheep_ns.route('/<string:sheep_id>/sell')
class SheepSell(Resource):
    @sheep_ns.doc('sell_sheep')
    @sheep_ns.expect(sheep_sale_model)
    def post(self, sheep_id):
        """Sell a sheep - creates sale record and marks as discarded"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        sale_data = request.get_json() or {}
        
        # Validate required fields
        if not sale_data.get('price'):
            return {'error': 'price is required'}, 400
        if not sale_data.get('sold_by'):
            return {'error': 'sold_by (user ID) is required'}, 400
        
        response_data, status_code = animal_service.sell_animal(SPECIES, sheep_id, sale_data)
        return response_data, status_code

@sheep_ns.route('/gender/<string:gender>')
class SheepByGender(Resource):
    @sheep_ns.doc('get_sheep_by_gender')
    @sheep_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @sheep_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self, gender):
        """Get sheep by gender with optional sorting by birth date and discarded filter"""
        sort_by = request.args.get('sort')
        if sort_by and sort_by not in ['asc', 'desc']:
            return {'error': 'Sort parameter must be "asc" or "desc"'}, 400
        
        # Parse discarded parameter (default: False = active only)
        discarded_param = request.args.get('discarded')
        discarded = False  # Default: show only active animals
        if discarded_param is not None:
            if discarded_param.lower() == 'true':
                discarded = True
            elif discarded_param.lower() == 'false':
                discarded = False
            elif discarded_param.lower() in ['null', 'all', '']:
                discarded = None  # Show all animals
        
        response_data, status_code = animal_service.get_animals_by_gender(SPECIES, gender, sort_by, discarded)
        return response_data, status_code

