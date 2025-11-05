"""
Sheep service with business logic
"""
from typing import List, Dict, Any, Optional, Literal
from app.repositories.sheep_repository import SheepRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value, validate_date_format
from app.utils.response import success_response, error_response, not_found_response
from models import Animal, Gender, AnimalType
import uuid

class SheepService:
    """
    Sheep service handling sheep business logic
    """
    
    def get_all_sheep(self, sort_by: Optional[Literal["asc", "desc"]] = None) -> tuple:
        """
        Get all sheep with optional sorting by birth date
        
        Args:
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                
                if sort_by:
                    sheep = repo.get_all_sorted(sort_by)
                else:
                    sheep = repo.get_all()
                
                sheep_data = []
                for s in sheep:
                    sheep_data.append(self._serialize_sheep(s))
                
                return success_response(sheep_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_sheep_by_id(self, sheep_id: str) -> tuple:
        """
        Get sheep by ID
        Args:
            sheep_id: Sheep ID
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                sheep = repo.get_by_id(sheep_id)
                
                if not sheep or sheep.species != AnimalType.SHEEP:
                    return not_found_response("Sheep")
                
                return success_response(self._serialize_sheep(sheep))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_sheep(self, sheep_data: Dict[str, Any]) -> tuple:
        """
        Create a new sheep
        
        Args:
            sheep_data: Sheep data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(sheep_data, ['name'])
            
            # Validate gender if provided
            if 'gender' in sheep_data:
                validate_enum_value(sheep_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in sheep_data and sheep_data['birth_date']:
                sheep_data['birth_date'] = validate_date_format(sheep_data['birth_date'])
            
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                
                # Create sheep - ensure species is set to SHEEP
                sheep_data['id'] = str(uuid.uuid4())
                sheep_data['species'] = AnimalType.SHEEP
                sheep = repo.create(**sheep_data)
                
                return success_response(self._serialize_sheep(sheep), "Sheep created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_sheep(self, sheep_id: str, sheep_data: Dict[str, Any]) -> tuple:
        """
        Update sheep
        
        Args:
            sheep_id: Sheep ID
            sheep_data: Updated sheep data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate gender if provided
            if 'gender' in sheep_data:
                validate_enum_value(sheep_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in sheep_data:
                if sheep_data['birth_date']:
                    sheep_data['birth_date'] = validate_date_format(sheep_data['birth_date'])
                else:
                    sheep_data['birth_date'] = None
            
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                
                # Check if sheep exists and is of correct species
                sheep = repo.get_by_id(sheep_id)
                if not sheep or sheep.species != AnimalType.SHEEP:
                    return not_found_response("Sheep")
                
                # Prevent species change
                if 'species' in sheep_data:
                    sheep_data.pop('species')
                
                # Update sheep
                updated_sheep = repo.update(sheep_id, **sheep_data)
                
                return success_response(self._serialize_sheep(updated_sheep), "Sheep updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_sheep(self, sheep_id: str) -> tuple:
        """
        Delete sheep
        
        Args:
            sheep_id: Sheep ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                
                # Check if sheep exists and is of correct species
                sheep = repo.get_by_id(sheep_id)
                if not sheep or sheep.species != AnimalType.SHEEP:
                    return not_found_response("Sheep")
                
                repo.delete(sheep_id)
                return success_response(None, "Sheep deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_sheep_by_gender(self, gender: str, sort_by: Optional[Literal["asc", "desc"]] = None) -> tuple:
        """
        Get sheep by gender with optional sorting by birth date
        
        Args:
            gender: Sheep gender (MALE or FEMALE)
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            with get_db_session() as db:
                repo = SheepRepository(Animal, db)
                
                if sort_by:
                    sheep = repo.get_by_gender_sorted(Gender(gender), sort_by)
                else:
                    sheep = repo.get_by_gender(Gender(gender))
                
                sheep_data = []
                for s in sheep:
                    sheep_data.append(self._serialize_sheep(s))
                
                return success_response(sheep_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_sheep(self, sheep: Animal) -> Dict[str, Any]:
        """
        Serialize sheep model to dictionary
        
        Args:
            sheep: Sheep model instance
            
        Returns:
            Serialized sheep data
        """
        return {
            'id': sheep.id,
            'name': sheep.name,
            'species': sheep.species.value if sheep.species else None,
            'image': sheep.image,
            'birth_date': sheep.birth_date.isoformat() if sheep.birth_date else None,
            'gender': sheep.gender.value if sheep.gender else None,
            'discarded': sheep.discarded,
            'discarded_reason': sheep.discarded_reason,
            'user_id': getattr(sheep, 'user_id', None),
            'corral_id': getattr(sheep, 'corral_id', None),
            'created_at': sheep.created_at.isoformat() if sheep.created_at else None,
            'updated_at': sheep.updated_at.isoformat() if sheep.updated_at else None
        }

