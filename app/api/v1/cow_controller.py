"""
Cow API controller
Uses generic AnimalService with AnimalType.COW
"""
from flask_restx import Resource, fields
from flask import request
from app.services.animal_service import AnimalService
from app.api.v1 import cows_ns, api
from app.utils.decorators import validate_auth_and_role
from models import AnimalType, Role

# Initialize generic service
animal_service = AnimalService()
SPECIES = AnimalType.COW

# API Models
cow_model = api.model('Cow', {
    'id': fields.String(description='Unique cow identifier'),
    'name': fields.String(description='Cow name'),
    'image': fields.String(description='Cow image URL'),
    'birth_date': fields.DateTime(description='Cow birth date'),
    'gender': fields.String(description='Cow gender'),
    'discarded': fields.Boolean(description='Whether cow is discarded'),
    'discarded_reason': fields.String(description='Reason for discarding'),
    'user_id': fields.String(description='Owner user ID'),
    'created_at': fields.DateTime(description='Cow creation timestamp'),
    'updated_at': fields.DateTime(description='Cow last update timestamp')
})

cow_create_model = api.model('CowCreate', {
    'name': fields.String(required=True, description='Cow name'),
    'image': fields.String(description='Cow image URL'),
    'birth_date': fields.String(required=True, description='Cow birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Cow gender'),
    'user_id': fields.String(description='Owner user ID')
})

cow_update_model = api.model('CowUpdate', {
    'name': fields.String(description='Cow name'),
    'image': fields.String(description='Cow image URL'),
    'birth_date': fields.String(description='Cow birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Cow gender'),
    'user_id': fields.String(description='Owner user ID')
})

cow_discard_model = api.model('CowDiscard', {
    'reason': fields.String(required=True, description='Reason for discarding the cow (e.g., "Muerto", "Eliminado")')
})

cow_sale_model = api.model('CowSale', {
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

@cows_ns.route('/')
class CowList(Resource):
    @cows_ns.doc('list_cows')
    @cows_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @cows_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self):
        """Get list of all cows with optional sorting by birth date and discarded filter"""
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

@cows_ns.route('/add')
class CowAdd(Resource):
    @cows_ns.doc('add_cow')
    @cows_ns.expect(cow_create_model)
    def post(self):
        """Add a new cow"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        cow_data = request.get_json() or {}
        # Basic validation: birth_date required
        if not cow_data.get('birth_date'):
            return {'error': 'birth_date is required (YYYY-MM-DD)'}, 400
        response_data, status_code = animal_service.create_animal(SPECIES, cow_data)
        return response_data, status_code

@cows_ns.route('/<string:cow_id>')
class CowDetail(Resource):
    @cows_ns.doc('get_cow')
    def get(self, cow_id):
        """Get cow by ID"""
        response_data, status_code = animal_service.get_animal_by_id(SPECIES, cow_id)
        return response_data, status_code
    
    @cows_ns.doc('update_cow')
    @cows_ns.expect(cow_update_model)
    def put(self, cow_id):
        """Update cow by ID"""
        user, error = validate_auth_and_role([Role.ADMIN, Role.USER, Role.TRABAJADOR])
        if error:
            return error[0], error[1]
        
        cow_data = request.get_json() or {}
        response_data, status_code = animal_service.update_animal(SPECIES, cow_id, cow_data)
        return response_data, status_code
    
    @cows_ns.doc('delete_cow')
    def delete(self, cow_id):
        """Delete cow by ID"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        response_data, status_code = animal_service.delete_animal(SPECIES, cow_id)
        return response_data, status_code

@cows_ns.route('/<string:cow_id>/discard')
class CowDiscard(Resource):
    @cows_ns.doc('discard_cow')
    @cows_ns.expect(cow_discard_model)
    def post(self, cow_id):
        """Discard a cow (mark as discarded without sale)"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        data = request.get_json() or {}
        reason = data.get('reason')
        
        if not reason:
            return {'error': 'reason is required'}, 400
        
        response_data, status_code = animal_service.discard_animal(SPECIES, cow_id, reason)
        return response_data, status_code

@cows_ns.route('/<string:cow_id>/sell')
class CowSell(Resource):
    @cows_ns.doc('sell_cow')
    @cows_ns.expect(cow_sale_model)
    def post(self, cow_id):
        """Sell a cow - creates sale record and marks as discarded"""
        user, error = validate_auth_and_role([Role.ADMIN])
        if error:
            return error[0], error[1]
        
        sale_data = request.get_json() or {}
        
        # Validate required fields
        if not sale_data.get('price'):
            return {'error': 'price is required'}, 400
        if not sale_data.get('sold_by'):
            return {'error': 'sold_by (user ID) is required'}, 400
        
        response_data, status_code = animal_service.sell_animal(SPECIES, cow_id, sale_data)
        return response_data, status_code

@cows_ns.route('/gender/<string:gender>')
class CowByGender(Resource):
    @cows_ns.doc('get_cows_by_gender')
    @cows_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @cows_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self, gender):
        """Get cows by gender with optional sorting by birth date and discarded filter"""
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

