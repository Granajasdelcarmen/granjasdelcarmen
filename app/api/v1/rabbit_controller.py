"""
Rabbit API controller
"""
from flask_restx import Resource, fields
from flask import request
from app.services.rabbit_service import RabbitService
from app.api.v1 import rabbits_ns, api

# Initialize service
rabbit_service = RabbitService()

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
    'birth_date': fields.String(description='Rabbit birth date (YYYY-MM-DD format)'),
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

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

@rabbits_ns.route('/')
class RabbitList(Resource):
    @rabbits_ns.doc('list_rabbits')
    @rabbits_ns.marshal_list_with(rabbit_model)
    def get(self):
        """Get list of all rabbits"""
        response_data, status_code = rabbit_service.get_all_rabbits()
        return response_data, status_code

@rabbits_ns.route('/add')
class RabbitAdd(Resource):
    @rabbits_ns.doc('add_rabbit')
    @rabbits_ns.expect(rabbit_create_model)
    @rabbits_ns.marshal_with(rabbit_model, code=201)
    @rabbits_ns.marshal_with(error_model, code=400)
    @rabbits_ns.marshal_with(error_model, code=500)
    def post(self):
        """Add a new rabbit"""
        rabbit_data = request.get_json() or {}
        response_data, status_code = rabbit_service.create_rabbit(rabbit_data)
        return response_data, status_code

@rabbits_ns.route('/<string:rabbit_id>')
class RabbitDetail(Resource):
    @rabbits_ns.doc('get_rabbit')
    @rabbits_ns.marshal_with(rabbit_model)
    @rabbits_ns.marshal_with(error_model, code=404)
    @rabbits_ns.marshal_with(error_model, code=500)
    def get(self, rabbit_id):
        """Get rabbit by ID"""
        response_data, status_code = rabbit_service.get_rabbit_by_id(rabbit_id)
        return response_data, status_code
    
    @rabbits_ns.doc('update_rabbit')
    @rabbits_ns.expect(rabbit_update_model)
    @rabbits_ns.marshal_with(rabbit_model)
    @rabbits_ns.marshal_with(error_model, code=400)
    @rabbits_ns.marshal_with(error_model, code=404)
    @rabbits_ns.marshal_with(error_model, code=500)
    def put(self, rabbit_id):
        """Update rabbit by ID"""
        rabbit_data = request.get_json() or {}
        response_data, status_code = rabbit_service.update_rabbit(rabbit_id, rabbit_data)
        return response_data, status_code
    
    @rabbits_ns.doc('delete_rabbit')
    @rabbits_ns.marshal_with(api.model('Success', {
        'message': fields.String(description='Success message')
    }))
    @rabbits_ns.marshal_with(error_model, code=404)
    @rabbits_ns.marshal_with(error_model, code=500)
    def delete(self, rabbit_id):
        """Delete rabbit by ID"""
        response_data, status_code = rabbit_service.delete_rabbit(rabbit_id)
        return response_data, status_code

@rabbits_ns.route('/gender/<string:gender>')
class RabbitByGender(Resource):
    @rabbits_ns.doc('get_rabbits_by_gender')
    @rabbits_ns.marshal_list_with(rabbit_model)
    @rabbits_ns.marshal_with(error_model, code=400)
    @rabbits_ns.marshal_with(error_model, code=500)
    def get(self, gender):
        """Get rabbits by gender"""
        response_data, status_code = rabbit_service.get_rabbits_by_gender(gender)
        return response_data, status_code
