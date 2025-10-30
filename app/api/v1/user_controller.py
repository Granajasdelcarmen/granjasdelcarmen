"""
User API controller
"""
from flask_restx import Resource, fields
from app.services.user_service import UserService
from app.api.v1 import users_ns, api

# Initialize service
user_service = UserService()

# API Models
user_model = api.model('User', {
    'id': fields.String(description='Unique user identifier'),
    'email': fields.String(description='User email address'),
    'name': fields.String(description='User full name'),
    'phone': fields.String(description='User phone number'),
    'address': fields.String(description='User address'),
    'role': fields.String(description='User role'),
    'is_active': fields.Boolean(description='User active status'),
    'created_at': fields.DateTime(description='User creation timestamp'),
    'updated_at': fields.DateTime(description='User last update timestamp')
})

user_create_model = api.model('UserCreate', {
    'email': fields.String(required=True, description='User email address'),
    'name': fields.String(description='User full name'),
    'phone': fields.String(description='User phone number'),
    'address': fields.String(description='User address'),
    'role': fields.String(enum=['admin', 'user', 'viewer'], default='user', description='User role')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('list_users')
    def get(self):
        """Get list of all users"""
        response_data, status_code = user_service.get_all_users()
        return response_data, status_code
    
    @users_ns.doc('create_user')
    @users_ns.expect(user_create_model)
    def post(self):
        """Create a new user"""
        from flask import request
        user_data = request.get_json() or {}
        response_data, status_code = user_service.create_user(user_data)
        return response_data, status_code

## Seed endpoint removed: we will work only with real data moving forward

@users_ns.route('/<string:user_id>')
class UserDetail(Resource):
    @users_ns.doc('get_user')
    @users_ns.marshal_with(user_model)
    @users_ns.marshal_with(error_model, code=404)
    @users_ns.marshal_with(error_model, code=500)
    def get(self, user_id):
        """Get user by ID"""
        response_data, status_code = user_service.get_user_by_id(user_id)
        return response_data, status_code
    
    @users_ns.doc('update_user')
    @users_ns.expect(user_create_model)
    @users_ns.marshal_with(user_model)
    @users_ns.marshal_with(error_model, code=400)
    @users_ns.marshal_with(error_model, code=404)
    @users_ns.marshal_with(error_model, code=500)
    def put(self, user_id):
        """Update user by ID"""
        from flask import request
        user_data = request.get_json() or {}
        response_data, status_code = user_service.update_user(user_id, user_data)
        return response_data, status_code
    
    @users_ns.doc('delete_user')
    @users_ns.marshal_with(api.model('Success', {
        'message': fields.String(description='Success message')
    }))
    @users_ns.marshal_with(error_model, code=404)
    @users_ns.marshal_with(error_model, code=500)
    def delete(self, user_id):
        """Delete user by ID"""
        response_data, status_code = user_service.delete_user(user_id)
        return response_data, status_code
