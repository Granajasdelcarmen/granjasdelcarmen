"""
Generic Animal Service - Unified service for all animal types
Handles all CRUD operations for any animal species
"""
from typing import List, Dict, Any, Optional, Literal
from app.repositories.animal_repository import AnimalRepository
from app.repositories.animal_sale_repository import AnimalSaleRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value, validate_date_format
from app.utils.response import success_response, error_response, not_found_response
from models import Animal, Gender, AnimalType, AnimalSale
import uuid


class AnimalService:
    """
    Generic animal service handling business logic for all animal types
    """
    
    def get_all_animals(
        self, 
        species: AnimalType,
        sort_by: Optional[Literal["asc", "desc"]] = None, 
        discarded: Optional[bool] = False
    ) -> tuple:
        """
        Get all animals of a specific species with optional sorting and discarded filter
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
            discarded: Filter by discarded status (False = active only, True = discarded only, None = all)
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                if sort_by:
                    animals = repo.get_all_sorted_by_species(species, sort_by, discarded)
                else:
                    animals = repo.get_all_by_species(species, discarded=discarded)
                
                animals_data = []
                for animal in animals:
                    animals_data.append(self._serialize_animal(animal))
                
                return success_response(animals_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_animal_by_id(self, species: AnimalType, animal_id: str) -> tuple:
        """
        Get animal by ID and species
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                animal = repo.get_by_id(animal_id)
                
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                return success_response(self._serialize_animal(animal))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_animal(self, species: AnimalType, animal_data: Dict[str, Any]) -> tuple:
        """
        Create a new animal of specified species
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            animal_data: Animal data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(animal_data, ['name'])
            
            # Validate gender if provided
            if 'gender' in animal_data:
                validate_enum_value(animal_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in animal_data and animal_data['birth_date']:
                animal_data['birth_date'] = validate_date_format(animal_data['birth_date'])
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Create animal - ensure species is set
                animal_data['id'] = str(uuid.uuid4())
                animal = repo.create_with_species(species, **animal_data)
                
                return success_response(self._serialize_animal(animal), f"{species.name.capitalize()} created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_animal(self, species: AnimalType, animal_id: str, animal_data: Dict[str, Any]) -> tuple:
        """
        Update animal
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
            animal_data: Updated animal data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate gender if provided
            if 'gender' in animal_data:
                validate_enum_value(animal_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Parse birth_date if provided
            if 'birth_date' in animal_data:
                if animal_data['birth_date']:
                    animal_data['birth_date'] = validate_date_format(animal_data['birth_date'])
                else:
                    animal_data['birth_date'] = None
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Check if animal exists and is of correct species
                animal = repo.get_by_id(animal_id)
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                # Prevent species change
                if 'species' in animal_data:
                    animal_data.pop('species')
                
                # Update animal
                updated_animal = repo.update(animal_id, **animal_data)
                
                return success_response(self._serialize_animal(updated_animal), f"{species.name.capitalize()} updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_animal(self, species: AnimalType, animal_id: str) -> tuple:
        """
        Delete animal
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Check if animal exists and is of correct species
                animal = repo.get_by_id(animal_id)
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                repo.delete(animal_id)
                return success_response(None, f"{species.name.capitalize()} deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_animals_by_gender(
        self, 
        species: AnimalType,
        gender: str, 
        sort_by: Optional[Literal["asc", "desc"]] = None, 
        discarded: Optional[bool] = False
    ) -> tuple:
        """
        Get animals by gender and species with optional sorting and discarded filter
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            gender: Animal gender (MALE or FEMALE)
            sort_by: Sort order - "asc" for ascending, "desc" for descending, None for no sorting
            discarded: Filter by discarded status (False = active only, True = discarded only, None = all)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                if sort_by:
                    animals = repo.get_by_gender_and_species_sorted(species, Gender(gender), sort_by, discarded)
                else:
                    animals = repo.get_by_gender_and_species(species, Gender(gender), discarded)
                
                animals_data = []
                for animal in animals:
                    animals_data.append(self._serialize_animal(animal))
                
                return success_response(animals_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def discard_animal(self, species: AnimalType, animal_id: str, reason: str) -> tuple:
        """
        Mark an animal as discarded (without sale)
        Only admins can discard animals
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
            reason: Reason for discarding (e.g., "Muerto", "Eliminado")
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Check if user is admin
            from app.utils.auth import require_admin
            admin_check = require_admin()
            if admin_check:
                return admin_check
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Check if animal exists and is of correct species
                animal = repo.get_by_id(animal_id)
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                success = repo.discard_animal(species, animal_id, reason)
                if success:
                    return success_response(None, f"{species.name.capitalize()} discarded successfully")
                else:
                    return error_response(f"Failed to discard {species.name.lower()}", 500)
        except Exception as e:
            return error_response(str(e), 500)
    
    def sell_animal(
        self, 
        species: AnimalType, 
        animal_id: str, 
        sale_data: Dict[str, Any]
    ) -> tuple:
        """
        Sell an animal - creates AnimalSale record and marks animal as discarded
        Only admins can sell animals
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
            sale_data: Sale data dictionary with:
                - price (required): Sale price
                - weight (optional): Weight at sale time
                - height (optional): Height (for rabbits, etc.)
                - notes (optional): Additional notes
                - sold_by (required): User ID who made the sale
                - reason (optional): Reason for sale (defaults to "Vendido")
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Check if user is admin
            from app.utils.auth import require_admin
            admin_check = require_admin()
            if admin_check:
                return admin_check
            
            # Validate required fields
            validate_required_fields(sale_data, ['price', 'sold_by'])
            
            with get_db_session() as db:
                try:
                    animal_repo = AnimalRepository(Animal, db)
                    sale_repo = AnimalSaleRepository(AnimalSale, db)
                    
                    # Check if animal exists and is of correct species
                    animal = animal_repo.get_by_id(animal_id)
                    if not animal or animal.species != species:
                        return not_found_response(species.name.capitalize())
                    
                    # Check if animal is already discarded
                    if animal.discarded:
                        return error_response(f"{species.name.capitalize()} is already discarded/sold", 400)
                    
                    # Create sale record manually (without auto-commit)
                    # Weight is in grams (integer), but we store as float for compatibility
                    sale_record_data = {
                        'id': str(uuid.uuid4()),
                        'animal_id': animal_id,
                        'animal_type': species,
                        'price': float(sale_data['price']),
                        'weight': float(sale_data['weight']) if sale_data.get('weight') is not None else None,
                        'height': float(sale_data['height']) if sale_data.get('height') is not None else None,
                        'notes': sale_data.get('notes'),
                        'sold_by': sale_data['sold_by']
                    }
                    
                    # Create sale record without commit (we'll commit manually)
                    sale_record = AnimalSale(**sale_record_data)
                    db.add(sale_record)
                    
                    # Mark animal as discarded with reason (without commit)
                    reason = sale_data.get('reason', 'Vendido')
                    animal.discarded = True
                    animal.discarded_reason = reason
                    
                    # Commit both operations together
                    db.commit()
                    db.refresh(sale_record)
                    db.refresh(animal)
                    
                    return success_response(
                        self._serialize_sale(sale_record), 
                        f"{species.name.capitalize()} sold successfully", 
                        201
                    )
                except Exception as e:
                    db.rollback()
                    raise e
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_sale(self, sale: AnimalSale) -> Dict[str, Any]:
        """
        Serialize AnimalSale model to dictionary
        
        Args:
            sale: AnimalSale model instance
            
        Returns:
            Serialized sale data
        """
        return {
            'id': sale.id,
            'animal_id': sale.animal_id,
            'animal_type': sale.animal_type.value if sale.animal_type else None,
            'price': sale.price,
            'weight': sale.weight,
            'height': sale.height,
            'notes': sale.notes,
            'sold_by': sale.sold_by,
            'created_at': sale.created_at.isoformat() if sale.created_at else None,
            'updated_at': sale.updated_at.isoformat() if sale.updated_at else None
        }
    
    def _serialize_animal(self, animal: Animal) -> Dict[str, Any]:
        """
        Serialize animal model to dictionary
        
        Args:
            animal: Animal model instance
            
        Returns:
            Serialized animal data
        """
        return {
            'id': animal.id,
            'name': animal.name,
            'species': animal.species.value if animal.species else None,
            'image': animal.image,
            'birth_date': animal.birth_date.isoformat() if animal.birth_date else None,
            'gender': animal.gender.value if animal.gender else None,
            'discarded': animal.discarded,
            'discarded_reason': animal.discarded_reason,
            'user_id': getattr(animal, 'user_id', None),
            'corral_id': getattr(animal, 'corral_id', None),
            'created_at': animal.created_at.isoformat() if animal.created_at else None,
            'updated_at': animal.updated_at.isoformat() if animal.updated_at else None
        }

