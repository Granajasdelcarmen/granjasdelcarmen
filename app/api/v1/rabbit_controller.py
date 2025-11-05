"""
Rabbit API controller
Uses generic AnimalService with AnimalType.RABBIT
"""
from flask_restx import Resource, fields
from flask import request
from app.services.animal_service import AnimalService
from app.api.v1 import rabbits_ns, api
from models import AnimalType

# Initialize generic service
animal_service = AnimalService()
SPECIES = AnimalType.RABBIT

# API Models
rabbit_model = api.model('Rabbit', {
    'id': fields.String(description='Unique rabbit identifier'),
    'name': fields.String(description='Rabbit name'),
    'image': fields.String(description='Rabbit image URL'),
    'birth_date': fields.DateTime(description='Rabbit birth date'),
    'gender': fields.String(description='Rabbit gender'),
    'discarded': fields.Boolean(description='Whether rabbit is discarded'),
    'discarded_reason': fields.String(description='Reason for discarding'),
    'user_id': fields.String(description='Owner user ID'),
    'created_at': fields.DateTime(description='Rabbit creation timestamp'),
    'updated_at': fields.DateTime(description='Rabbit last update timestamp')
})

rabbit_create_model = api.model('RabbitCreate', {
    'name': fields.String(required=True, description='Rabbit name'),
    'image': fields.String(description='Rabbit image URL'),
    'birth_date': fields.String(required=True, description='Rabbit birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Rabbit gender'),
    'user_id': fields.String(description='Owner user ID')
})

rabbit_update_model = api.model('RabbitUpdate', {
    'name': fields.String(description='Rabbit name'),
    'image': fields.String(description='Rabbit image URL'),
    'birth_date': fields.String(description='Rabbit birth date (YYYY-MM-DD format)'),
    'gender': fields.String(enum=['MALE', 'FEMALE'], description='Rabbit gender'),
    'user_id': fields.String(description='Owner user ID')
})

rabbit_discard_model = api.model('RabbitDiscard', {
    'reason': fields.String(required=True, description='Reason for discarding the rabbit (e.g., "Muerto", "Eliminado")')
})

rabbit_sale_model = api.model('RabbitSale', {
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

@rabbits_ns.route('/')
class RabbitList(Resource):
    @rabbits_ns.doc('list_rabbits')
    @rabbits_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @rabbits_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self):
        """Get list of all rabbits with optional sorting by birth date and discarded filter"""
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

@rabbits_ns.route('/add')
class RabbitAdd(Resource):
    @rabbits_ns.doc('add_rabbit')
    @rabbits_ns.expect(rabbit_create_model)
    def post(self):
        """Add a new rabbit"""
        rabbit_data = request.get_json() or {}
        # Basic validation: birth_date required
        if not rabbit_data.get('birth_date'):
            return {'error': 'birth_date is required (YYYY-MM-DD)'}, 400
        response_data, status_code = animal_service.create_animal(SPECIES, rabbit_data)
        return response_data, status_code

@rabbits_ns.route('/<string:rabbit_id>')
class RabbitDetail(Resource):
    @rabbits_ns.doc('get_rabbit')
    def get(self, rabbit_id):
        """Get rabbit by ID"""
        response_data, status_code = animal_service.get_animal_by_id(SPECIES, rabbit_id)
        return response_data, status_code
    
    @rabbits_ns.doc('update_rabbit')
    @rabbits_ns.expect(rabbit_update_model)
    def put(self, rabbit_id):
        """Update rabbit by ID"""
        rabbit_data = request.get_json() or {}
        response_data, status_code = animal_service.update_animal(SPECIES, rabbit_id, rabbit_data)
        return response_data, status_code
    
    @rabbits_ns.doc('delete_rabbit')
    def delete(self, rabbit_id):
        """Delete rabbit by ID"""
        response_data, status_code = animal_service.delete_animal(SPECIES, rabbit_id)
        return response_data, status_code

@rabbits_ns.route('/<string:rabbit_id>/discard')
class RabbitDiscard(Resource):
    @rabbits_ns.doc('discard_rabbit')
    @rabbits_ns.expect(rabbit_discard_model)
    def post(self, rabbit_id):
        """Discard a rabbit (mark as discarded without sale) - Admin only"""
        from app.utils.decorators import validate_auth_and_role
        from models import Role
        
        # Validate authentication and check admin role
        user, error = validate_auth_and_role(allowed_roles=[Role.ADMIN])
        if error:
            return error
        
        data = request.get_json() or {}
        reason = data.get('reason')
        
        if not reason:
            return {'error': 'reason is required'}, 400
        
        response_data, status_code = animal_service.discard_animal(SPECIES, rabbit_id, reason)
        return response_data, status_code

@rabbits_ns.route('/<string:rabbit_id>/sell')
class RabbitSell(Resource):
    @rabbits_ns.doc('sell_rabbit')
    @rabbits_ns.expect(rabbit_sale_model)
    def post(self, rabbit_id):
        """Sell a rabbit - creates sale record and marks as discarded - Admin only"""
        from app.utils.decorators import validate_auth_and_role
        from models import Role
        
        # Validate authentication and check admin role
        user, error = validate_auth_and_role(allowed_roles=[Role.ADMIN])
        if error:
            return error
        
        # Get user ID (from session sub or database id)
        user_id = user.get("sub") or user.get("id")
        if not user_id:
            return {'error': 'User ID not found'}, 401
        
        sale_data = request.get_json() or {}
        
        # Validate required fields
        if not sale_data.get('price'):
            return {'error': 'price is required'}, 400
        
        # Set sold_by from authenticated user
        sale_data['sold_by'] = user_id
        
        response_data, status_code = animal_service.sell_animal(SPECIES, rabbit_id, sale_data)
        return response_data, status_code

@rabbits_ns.route('/gender/<string:gender>')
class RabbitByGender(Resource):
    @rabbits_ns.doc('get_rabbits_by_gender')
    @rabbits_ns.param('sort', 'Sort order by birth date: asc (ascending) or desc (descending)')
    @rabbits_ns.param('discarded', 'Filter by discarded status: false (active only, default), true (discarded only), or null (all)')
    def get(self, gender):
        """Get rabbits by gender with optional sorting by birth date and discarded filter"""
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
