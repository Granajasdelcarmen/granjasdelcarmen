"""
Rabbit service with business logic
"""
from typing import List, Dict, Any, Optional
from app.repositories.rabbit_repository import RabbitRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value, validate_date_format
from app.utils.response import success_response, error_response, not_found_response
from models import Rabbit, Gender
import uuid

class RabbitService:
    """
    Rabbit service handling rabbit business logic
    """
    
    def get_all_rabbits(self) -> tuple:
        """
        Get all rabbits
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                rabbits = repo.get_all()
                
                rabbits_data = []
                for rabbit in rabbits:
                    rabbits_data.append(self._serialize_rabbit(rabbit))
                
                return success_response(rabbits_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_rabbit_by_id(self, rabbit_id: str) -> tuple:
        """
        Get rabbit by ID
        
        Args:
            rabbit_id: Rabbit ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                rabbit = repo.get_by_id(rabbit_id)
                
                if not rabbit:
                    return not_found_response("Rabbit")
                
                return success_response(self._serialize_rabbit(rabbit))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_rabbit(self, rabbit_data: Dict[str, Any]) -> tuple:
        """
        Create a new rabbit
        
        Args:
            rabbit_data: Rabbit data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(rabbit_data, ['name'])
            
            # Validate gender if provided
            if 'gender' in rabbit_data:
                validate_enum_value(rabbit_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in rabbit_data and rabbit_data['birth_date']:
                rabbit_data['birth_date'] = validate_date_format(rabbit_data['birth_date'])
            
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                
                # Create rabbit
                rabbit_data['id'] = str(uuid.uuid4())
                rabbit = repo.create(**rabbit_data)
                
                return success_response(self._serialize_rabbit(rabbit), "Rabbit created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_rabbit(self, rabbit_id: str, rabbit_data: Dict[str, Any]) -> tuple:
        """
        Update rabbit
        
        Args:
            rabbit_id: Rabbit ID
            rabbit_data: Updated rabbit data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate gender if provided
            if 'gender' in rabbit_data:
                validate_enum_value(rabbit_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in rabbit_data:
                if rabbit_data['birth_date']:
                    rabbit_data['birth_date'] = validate_date_format(rabbit_data['birth_date'])
                else:
                    rabbit_data['birth_date'] = None
            
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                
                # Check if rabbit exists
                if not repo.exists(rabbit_id):
                    return not_found_response("Rabbit")
                
                # Update rabbit
                updated_rabbit = repo.update(rabbit_id, **rabbit_data)
                
                return success_response(self._serialize_rabbit(updated_rabbit), "Rabbit updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_rabbit(self, rabbit_id: str) -> tuple:
        """
        Delete rabbit
        
        Args:
            rabbit_id: Rabbit ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                
                if not repo.exists(rabbit_id):
                    return not_found_response("Rabbit")
                
                repo.delete(rabbit_id)
                return success_response(None, "Rabbit deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_rabbits_by_gender(self, gender: str) -> tuple:
        """
        Get rabbits by gender
        
        Args:
            gender: Rabbit gender (MALE or FEMALE)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                rabbits = repo.get_by_gender(Gender(gender))
                
                rabbits_data = []
                for rabbit in rabbits:
                    rabbits_data.append(self._serialize_rabbit(rabbit))
                
                return success_response(rabbits_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def discard_rabbit(self, rabbit_id: str, reason: str) -> tuple:
        """
        Mark a rabbit as discarded
        
        Args:
            rabbit_id: Rabbit ID
            reason: Reason for discarding
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = RabbitRepository(Rabbit, db)
                
                if not repo.exists(rabbit_id):
                    return not_found_response("Rabbit")
                
                success = repo.discard_rabbit(rabbit_id, reason)
                if success:
                    return success_response(None, "Rabbit discarded successfully")
                else:
                    return error_response("Failed to discard rabbit", 500)
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_rabbit(self, rabbit: Rabbit) -> Dict[str, Any]:
        """
        Serialize rabbit model to dictionary
        
        Args:
            rabbit: Rabbit model instance
            
        Returns:
            Serialized rabbit data
        """
        return {
            'id': rabbit.id,
            'name': rabbit.name,
            'image': rabbit.image,
            'birth_date': rabbit.birth_date.isoformat() if rabbit.birth_date else None,
            'gender': rabbit.gender.value if rabbit.gender else None,
            'discarded': rabbit.discarded,
            'discarded_reason': rabbit.discarded_reason,
            'user_id': getattr(rabbit, 'user_id', None),
            'created_at': rabbit.created_at.isoformat() if rabbit.created_at else None,
            'updated_at': rabbit.updated_at.isoformat() if rabbit.updated_at else None
        }
