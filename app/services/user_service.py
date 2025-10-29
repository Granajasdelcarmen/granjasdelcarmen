"""
User service with business logic
"""
from typing import List, Dict, Any, Optional
from app.repositories.user_repository import UserRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value
from app.utils.response import success_response, error_response, not_found_response
from models import User, Role
import uuid

class UserService:
    """
    User service handling user business logic
    """
    
    def get_all_users(self) -> tuple:
        """
        Get all users
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = UserRepository(User, db)
                users = repo.get_all()
                
                users_data = []
                for user in users:
                    users_data.append(self._serialize_user(user))
                
                return success_response(users_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_user_by_id(self, user_id: str) -> tuple:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = UserRepository(User, db)
                user = repo.get_by_id(user_id)
                
                if not user:
                    return not_found_response("User")
                
                return success_response(self._serialize_user(user))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_user(self, user_data: Dict[str, Any]) -> tuple:
        """
        Create a new user
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(user_data, ['email'])
            
            # Validate role if provided
            if 'role' in user_data:
                validate_enum_value(user_data['role'], ['admin', 'user', 'viewer'], 'role')
            
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                # Check if user already exists
                existing_user = repo.get_by_email(user_data['email'])
                if existing_user:
                    return error_response("User with this email already exists", 409)
                
                # Create user
                user_data['id'] = str(uuid.uuid4())
                user = repo.create(**user_data)
                
                return success_response(self._serialize_user(user), "User created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> tuple:
        """
        Update user
        
        Args:
            user_id: User ID
            user_data: Updated user data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate role if provided
            if 'role' in user_data:
                validate_enum_value(user_data['role'], ['admin', 'user', 'viewer'], 'role')
            
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                # Check if user exists
                if not repo.exists(user_id):
                    return not_found_response("User")
                
                # Update user
                updated_user = repo.update(user_id, **user_data)
                
                return success_response(self._serialize_user(updated_user), "User updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_user(self, user_id: str) -> tuple:
        """
        Delete user
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                if not repo.exists(user_id):
                    return not_found_response("User")
                
                repo.delete(user_id)
                return success_response(None, "User deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def seed_test_user(self) -> tuple:
        """
        Create a test user for development
        
        Returns:
            Tuple of (response_data, status_code)
        """
        test_user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'user'
        }
        return self.create_user(test_user_data)
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """
        Serialize user model to dictionary
        
        Args:
            user: User model instance
            
        Returns:
            Serialized user data
        """
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'address': user.address,
            'role': user.role.value if user.role else None,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
