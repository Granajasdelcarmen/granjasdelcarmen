"""
User service with business logic
"""
from typing import List, Dict, Any, Optional

from sqlalchemy import true
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
            print("get_all_users")
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

    def get_user_by_email(self, email: str) -> tuple:
        """
        Get user by email
        
        Args:
            email: User email
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = UserRepository(User, db)
                user = repo.get_by_email(email)
                if not user:
                    return not_found_response("User")
                return success_response(self._serialize_user(user))
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_or_create_user_by_auth0_sub(
        self, 
        auth0_sub: str, 
        email: str, 
        name: str = None,
        picture: str = None
    ) -> tuple:
        """
        Get or create user by Auth0 sub ID (used in Auth0 callback)
        If user doesn't exist, creates it with default role 'user'
        
        Args:
            auth0_sub: Auth0 sub ID (will be used as user.id)
            email: User email
            name: User name (optional)
            picture: User picture URL (optional)
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                # Try to get user by ID (Auth0 sub)
                user = repo.get_by_id(auth0_sub)
                
                if user:
                    # User exists, return it
                    return success_response(self._serialize_user(user))
                
                # User doesn't exist, create it
                # Check if email already exists (shouldn't happen, but just in case)
                existing_user = repo.get_by_email(email)
                if existing_user:
                    # Email exists but ID is different - update ID to match Auth0 sub
                    # This handles edge cases where user was created manually
                    existing_user.id = auth0_sub
                    db.commit()
                    db.refresh(existing_user)
                    return success_response(self._serialize_user(existing_user))
                
                # Create new user with Auth0 sub as ID
                user_data = {
                    'id': auth0_sub,  # Use Auth0 sub as ID
                    'email': email,
                    'name': name,
                    'role': Role.USER,  # Default role, admin can change it later (user, trabajador, viewer, admin)
                    'is_active': True
                }
                
                user = repo.create(**user_data)
                
                return success_response(self._serialize_user(user), "User created successfully", 201)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_user_role(self, user_id: str, role: str) -> tuple:
        """
        Update user role (admin only)
        
        Args:
            user_id: User ID
            role: New role (admin, user, viewer, trabajador)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Map role to enum value (Role enum values are lowercase: "admin", "user", etc.)
            role_mapping = {
                'admin': 'admin',
                'user': 'user',
                'viewer': 'viewer',
                'trabajador': 'trabajador'
            }
            
            # Normalize role to lowercase
            role_lower = role.lower()
            
            if role_lower not in role_mapping:
                return error_response(f"Invalid role: {role}. Valid roles are: admin, user, viewer, trabajador", 400)
            
            # Get the enum value (which is lowercase)
            role_value = role_mapping[role_lower]
            
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                # Check if user exists
                user = repo.get_by_id(user_id)
                if not user:
                    return not_found_response("User")
                
                # Update role using the enum value (lowercase)
                user.role = Role(role_value)
                db.commit()
                db.refresh(user)
                
                return success_response(self._serialize_user(user), "User role updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
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
            # Validate and convert role if provided (Role enum values are lowercase: "admin", "user", etc.)
            if 'role' in user_data:
                role_mapping = {
                    'admin': 'admin',
                    'user': 'user',
                    'viewer': 'viewer',
                    'trabajador': 'trabajador'
                }
                role_lower = user_data['role'].lower()
                if role_lower in role_mapping:
                    user_data['role'] = Role(role_mapping[role_lower])  # Convert to Role enum
                else:
                    return error_response(f"Invalid role: {user_data['role']}. Valid roles are: admin, user, viewer, trabajador", 400)
            
            with get_db_session() as db:
                repo = UserRepository(User, db)
                
                # Check if user already exists by email
                existing_user = repo.get_by_email(user_data['email'])
                if existing_user:
                    return error_response("User with this email already exists", 409)
                
                # Check if ID is provided (for Auth0 sub), otherwise generate UUID
                if 'id' not in user_data:
                    user_data['id'] = str(uuid.uuid4())
                
                # Create user
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
            # Validate and convert role if provided (Role enum values are lowercase: "admin", "user", etc.)
            if 'role' in user_data:
                role_mapping = {
                    'admin': 'admin',
                    'user': 'user',
                    'viewer': 'viewer',
                    'trabajador': 'trabajador'
                }
                role_lower = user_data['role'].lower()
                if role_lower in role_mapping:
                    user_data['role'] = Role(role_mapping[role_lower])  # Convert to Role enum
                else:
                    return error_response(f"Invalid role: {user_data['role']}. Valid roles are: admin, user, viewer, trabajador", 400)
            
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
            'role': 'user',
            'phone': '1234567890',
            'address': '123 Main St, Anytown, USA',
            'is_active': true,
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
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
