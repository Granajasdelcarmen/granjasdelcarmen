"""
Cow service with business logic
"""
from typing import List, Dict, Any, Optional, Literal
from app.repositories.cow_repository import CowRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value, validate_date_format
from app.utils.response import success_response, error_response, not_found_response
from models import Animal, Gender, AnimalType
import uuid

class CowService:
    """
    Cow service handling cow business logic
    """
    
    def get_all_cows(self, sort_by: Optional[Literal["asc", "desc"]] = None) -> tuple:
        """
        Get all cows with optional sorting by birth date
        
        Args:
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                
                if sort_by:
                    cows = repo.get_all_sorted(sort_by)
                else:
                    cows = repo.get_all()
                
                cows_data = []
                for cow in cows:
                    cows_data.append(self._serialize_cow(cow))
                
                return success_response(cows_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_cow_by_id(self, cow_id: str) -> tuple:
        """
        Get cow by ID
        Args:
            cow_id: Cow ID
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                cow = repo.get_by_id(cow_id)
                
                if not cow or cow.species != AnimalType.COW:
                    return not_found_response("Cow")
                
                return success_response(self._serialize_cow(cow))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_cow(self, cow_data: Dict[str, Any]) -> tuple:
        """
        Create a new cow
        
        Args:
            cow_data: Cow data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(cow_data, ['name'])
            
            # Validate gender if provided
            if 'gender' in cow_data:
                validate_enum_value(cow_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in cow_data and cow_data['birth_date']:
                cow_data['birth_date'] = validate_date_format(cow_data['birth_date'])
            
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                
                # Create cow - ensure species is set to COW
                cow_data['id'] = str(uuid.uuid4())
                cow_data['species'] = AnimalType.COW
                cow = repo.create(**cow_data)
                
                return success_response(self._serialize_cow(cow), "Cow created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_cow(self, cow_id: str, cow_data: Dict[str, Any]) -> tuple:
        """
        Update cow
        
        Args:
            cow_id: Cow ID
            cow_data: Updated cow data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate gender if provided
            if 'gender' in cow_data:
                validate_enum_value(cow_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in cow_data:
                if cow_data['birth_date']:
                    cow_data['birth_date'] = validate_date_format(cow_data['birth_date'])
                else:
                    cow_data['birth_date'] = None
            
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                
                # Check if cow exists and is of correct species
                cow = repo.get_by_id(cow_id)
                if not cow or cow.species != AnimalType.COW:
                    return not_found_response("Cow")
                
                # Prevent species change
                if 'species' in cow_data:
                    cow_data.pop('species')
                
                # Update cow
                updated_cow = repo.update(cow_id, **cow_data)
                
                return success_response(self._serialize_cow(updated_cow), "Cow updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_cow(self, cow_id: str) -> tuple:
        """
        Delete cow
        
        Args:
            cow_id: Cow ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                
                # Check if cow exists and is of correct species
                cow = repo.get_by_id(cow_id)
                if not cow or cow.species != AnimalType.COW:
                    return not_found_response("Cow")
                
                repo.delete(cow_id)
                return success_response(None, "Cow deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_cows_by_gender(self, gender: str, sort_by: Optional[Literal["asc", "desc"]] = None) -> tuple:
        """
        Get cows by gender with optional sorting by birth date
        
        Args:
            gender: Cow gender (MALE or FEMALE)
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            with get_db_session() as db:
                repo = CowRepository(Animal, db)
                
                if sort_by:
                    cows = repo.get_by_gender_sorted(Gender(gender), sort_by)
                else:
                    cows = repo.get_by_gender(Gender(gender))
                
                cows_data = []
                for cow in cows:
                    cows_data.append(self._serialize_cow(cow))
                
                return success_response(cows_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_cow(self, cow: Animal) -> Dict[str, Any]:
        """
        Serialize cow model to dictionary
        
        Args:
            cow: Cow model instance
            
        Returns:
            Serialized cow data
        """
        return {
            'id': cow.id,
            'name': cow.name,
            'species': cow.species.value if cow.species else None,
            'image': cow.image,
            'birth_date': cow.birth_date.isoformat() if cow.birth_date else None,
            'gender': cow.gender.value if cow.gender else None,
            'discarded': cow.discarded,
            'discarded_reason': cow.discarded_reason,
            'user_id': getattr(cow, 'user_id', None),
            'corral_id': getattr(cow, 'corral_id', None),
            'created_at': cow.created_at.isoformat() if cow.created_at else None,
            'updated_at': cow.updated_at.isoformat() if cow.updated_at else None
        }

