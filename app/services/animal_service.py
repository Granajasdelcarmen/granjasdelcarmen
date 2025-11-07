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
from app.utils.logger import Logger
from models import Animal, Gender, AnimalType, AnimalSale, AnimalOrigin
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
            import time
            start_time = time.time()
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                query_start = time.time()
                if sort_by:
                    animals = repo.get_all_sorted_by_species(species, sort_by, discarded)
                else:
                    animals = repo.get_all_by_species(species, discarded=discarded)
                query_time = time.time() - query_start
                
                serialize_start = time.time()
                animals_data = []
                for animal in animals:
                    animals_data.append(self._serialize_animal(animal))
                serialize_time = time.time() - serialize_start
                
                total_time = time.time() - start_time
                
                Logger.info(
                    f"⏱️ Performance - get_all_animals({species.name}): "
                    f"Total={total_time:.3f}s, Query={query_time:.3f}s, "
                    f"Serialize={serialize_time:.4f}s, Count={len(animals_data)}"
                )
                
                return success_response(animals_data)
        except Exception as e:
            Logger.error(f"Error getting animals of species {species.name}", exc_info=e)
            return error_response(str(e), 500)
    
    def get_animal_by_id(self, species: AnimalType, animal_id: str, include_children: bool = False) -> tuple:
        """
        Get animal by ID and species
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID
            include_children: Whether to include children information (default: False)
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            import time
            start_time = time.time()
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                query_start = time.time()
                animal = repo.get_by_id(animal_id, load_parents=True)
                query_time = time.time() - query_start
                
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                serialize_start = time.time()
                result = self._serialize_animal(animal, include_children=include_children, db=db)
                serialize_time = time.time() - serialize_start
                
                total_time = time.time() - start_time
                
                Logger.info(
                    f"⏱️ Performance - get_animal_by_id({species.name}, {animal_id}): "
                    f"Total={total_time:.3f}s, Query={query_time:.3f}s, "
                    f"Serialize={serialize_time:.4f}s, IncludeChildren={include_children}"
                )
                
                return success_response(result)
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_animal(self, species: AnimalType, animal_data: Dict[str, Any]) -> tuple:
        """
        Create a new animal of specified species
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            animal_data: Animal data dictionary with optional fields:
                - name (required)
                - gender (optional): MALE or FEMALE
                - birth_date (optional): ISO format date string
                - origin (optional): BORN or PURCHASED (default: PURCHASED)
                - mother_id (optional): ID of mother animal (requires origin=BORN)
                - father_id (optional): ID of father animal (requires origin=BORN)
                - purchase_date (optional): Required if origin=PURCHASED
                - purchase_price (optional): Price if purchased
                - purchase_vendor (optional): Vendor if purchased
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(animal_data, ['name'])
            
            # Validate gender if provided
            if 'gender' in animal_data:
                validate_enum_value(animal_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Validate origin if provided
            origin = None
            if 'origin' in animal_data:
                validate_enum_value(animal_data['origin'], ['BORN', 'PURCHASED'], 'origin')
                origin = AnimalOrigin(animal_data['origin'])
            else:
                origin = AnimalOrigin.PURCHASED  # Default
            
            # Parse birth_date if provided
            if 'birth_date' in animal_data and animal_data['birth_date']:
                animal_data['birth_date'] = validate_date_format(animal_data['birth_date'])
            
            # Parse purchase_date if provided
            if 'purchase_date' in animal_data and animal_data['purchase_date']:
                animal_data['purchase_date'] = validate_date_format(animal_data['purchase_date'])
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Validate parent relationships if provided
                mother_id = animal_data.get('mother_id')
                father_id = animal_data.get('father_id')
                
                if mother_id or father_id:
                    # If parent IDs are provided, origin must be BORN
                    if origin != AnimalOrigin.BORN:
                        return error_response("Animals with parents must have origin=BORN", 400)
                    
                    # Validate mother exists and is correct species and gender
                    if mother_id:
                        mother = repo.get_by_id(mother_id)
                        if not mother:
                            return error_response("Mother animal not found", 404)
                        if mother.species != species:
                            return error_response("Mother must be of the same species", 400)
                        if mother.gender != Gender.FEMALE:
                            return error_response("Mother must be FEMALE", 400)
                        if mother.discarded:
                            return error_response("Mother animal is discarded", 400)
                    
                    # Validate father exists and is correct species and gender
                    if father_id:
                        father = repo.get_by_id(father_id)
                        if not father:
                            return error_response("Father animal not found", 404)
                        if father.species != species:
                            return error_response("Father must be of the same species", 400)
                        if father.gender != Gender.MALE:
                            return error_response("Father must be MALE", 400)
                        if father.discarded:
                            return error_response("Father animal is discarded", 400)
                
                # If origin is PURCHASED, validate purchase fields
                if origin == AnimalOrigin.PURCHASED:
                    if 'purchase_date' in animal_data and animal_data['purchase_date']:
                        # Purchase date is optional but if provided, validate it
                        pass
                    # Clear parent IDs if origin is PURCHASED
                    animal_data.pop('mother_id', None)
                    animal_data.pop('father_id', None)
                else:
                    # If origin is BORN, clear purchase fields
                    animal_data.pop('purchase_date', None)
                    animal_data.pop('purchase_price', None)
                    animal_data.pop('purchase_vendor', None)
                
                # Set origin in animal_data
                animal_data['origin'] = origin
                
                # Create animal - ensure species is set
                animal_data['id'] = str(uuid.uuid4())
                animal = repo.create_with_species(species, **animal_data)
                
                # Si es una vaca que nació (origin=BORN), crear alertas automáticas
                if species == AnimalType.COW and origin == AnimalOrigin.BORN and animal.birth_date:
                    from app.services.cow_alert_service import CowAlertService
                    cow_alert_service = CowAlertService()
                    cow_alert_service.create_birth_alerts(
                        calf_id=animal.id,
                        birth_date=animal.birth_date,
                        mother_id=animal.mother_id
                    )
                
                # Si es un conejo que nació (origin=BORN), crear alertas automáticas
                if species == AnimalType.RABBIT and origin == AnimalOrigin.BORN and animal.birth_date:
                    from app.services.rabbit_alert_service import RabbitAlertService
                    rabbit_alert_service = RabbitAlertService()
                    rabbit_alert_service.create_birth_alerts(animal.id, animal.birth_date)
                
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
            animal_data: Updated animal data (can include parent relationships and origin)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate gender if provided
            if 'gender' in animal_data:
                validate_enum_value(animal_data['gender'], ['MALE', 'FEMALE'], 'gender')
            
            # Validate origin if provided
            origin = None
            if 'origin' in animal_data:
                validate_enum_value(animal_data['origin'], ['BORN', 'PURCHASED'], 'origin')
                origin = AnimalOrigin(animal_data['origin'])
            
            # Parse birth_date if provided
            if 'birth_date' in animal_data:
                if animal_data['birth_date']:
                    animal_data['birth_date'] = validate_date_format(animal_data['birth_date'])
                else:
                    animal_data['birth_date'] = None
            
            # Parse purchase_date if provided
            if 'purchase_date' in animal_data:
                if animal_data['purchase_date']:
                    animal_data['purchase_date'] = validate_date_format(animal_data['purchase_date'])
                else:
                    animal_data['purchase_date'] = None
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                # Check if animal exists and is of correct species
                animal = repo.get_by_id(animal_id)
                if not animal or animal.species != species:
                    return not_found_response(species.name.capitalize())
                
                # Prevent species change
                if 'species' in animal_data:
                    animal_data.pop('species')
                
                # Validate parent relationships if provided
                mother_id = animal_data.get('mother_id')
                father_id = animal_data.get('father_id')
                
                # Determine origin (use provided or current)
                current_origin = origin if origin else animal.origin
                
                if mother_id or father_id:
                    # If parent IDs are provided, origin must be BORN
                    if current_origin != AnimalOrigin.BORN:
                        return error_response("Animals with parents must have origin=BORN", 400)
                    
                    # Validate mother exists and is correct species and gender
                    if mother_id:
                        mother = repo.get_by_id(mother_id)
                        if not mother:
                            return error_response("Mother animal not found", 404)
                        if mother.species != species:
                            return error_response("Mother must be of the same species", 400)
                        if mother.gender != Gender.FEMALE:
                            return error_response("Mother must be FEMALE", 400)
                        if mother.discarded:
                            return error_response("Mother animal is discarded", 400)
                        # Prevent circular reference
                        if mother_id == animal_id:
                            return error_response("Animal cannot be its own mother", 400)
                    
                    # Validate father exists and is correct species and gender
                    if father_id:
                        father = repo.get_by_id(father_id)
                        if not father:
                            return error_response("Father animal not found", 404)
                        if father.species != species:
                            return error_response("Father must be of the same species", 400)
                        if father.gender != Gender.MALE:
                            return error_response("Father must be MALE", 400)
                        if father.discarded:
                            return error_response("Father animal is discarded", 400)
                        # Prevent circular reference
                        if father_id == animal_id:
                            return error_response("Animal cannot be its own father", 400)
                
                # If origin is PURCHASED, clear parent IDs if they were provided
                if current_origin == AnimalOrigin.PURCHASED:
                    # Clear parent IDs if they were set in the update
                    if 'mother_id' in animal_data or 'father_id' in animal_data:
                        animal_data['mother_id'] = None
                        animal_data['father_id'] = None
                else:
                    # If origin is BORN, clear purchase fields if they were provided
                    if 'purchase_date' in animal_data or 'purchase_price' in animal_data or 'purchase_vendor' in animal_data:
                        animal_data['purchase_date'] = None
                        animal_data['purchase_price'] = None
                        animal_data['purchase_vendor'] = None
                
                # Set origin in animal_data if provided
                if origin:
                    animal_data['origin'] = origin
                
                # Verificar si se está marcando como sacrificado
                was_slaughtered_before = getattr(animal, 'slaughtered', False)
                is_being_slaughtered = animal_data.get('slaughtered', False)
                
                # Update animal
                updated_animal = repo.update(animal_id, **animal_data)
                
                # Si se marcó como sacrificado (y antes no lo estaba), actualizar alertas
                if species == AnimalType.RABBIT and is_being_slaughtered and not was_slaughtered_before:
                    from app.services.alert_service import AlertService
                    alert_service = AlertService()
                    alert_service.update_alerts_for_slaughtered_rabbit(animal_id, db)
                
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
            import time
            start_time = time.time()
            
            validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            with get_db_session() as db:
                repo = AnimalRepository(Animal, db)
                
                query_start = time.time()
                if sort_by:
                    animals = repo.get_by_gender_and_species_sorted(species, Gender(gender), sort_by, discarded)
                else:
                    animals = repo.get_by_gender_and_species(species, Gender(gender), discarded)
                query_time = time.time() - query_start
                
                serialize_start = time.time()
                animals_data = []
                for animal in animals:
                    animals_data.append(self._serialize_animal(animal))
                serialize_time = time.time() - serialize_start
                
                total_time = time.time() - start_time
                
                Logger.info(
                    f"⏱️ Performance - get_animals_by_gender({species.name}, {gender}): "
                    f"Total={total_time:.3f}s, Query={query_time:.3f}s, "
                    f"Serialize={serialize_time:.4f}s, Count={len(animals_data)}"
                )
                
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
                    
                    # Si el animal está en congelador (sacrificado), permitir venta
                    # Si está descartado pero no en congelador, no permitir venta
                    was_in_freezer = getattr(animal, 'in_freezer', False)
                    if animal.discarded and not was_in_freezer:
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
                    
                    # Si estaba en congelador, marcar como ya no en congelador
                    if was_in_freezer:
                        animal.in_freezer = False
                    
                    # Si era un conejo sacrificado, actualizar alertas relacionadas
                    if species == AnimalType.RABBIT and was_in_freezer:
                        from app.services.alert_service import AlertService
                        alert_service = AlertService()
                        alert_service.update_alerts_for_slaughtered_rabbit(animal_id, db)
                    
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
    
    def slaughter_rabbit(self, rabbit_id: str, user_id: Optional[str] = None) -> tuple:
        """
        Mark a rabbit as slaughtered and store in freezer
        This is different from selling - the rabbit goes to inventory
        
        Args:
            rabbit_id: ID of the rabbit to slaughter
            
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                from app.repositories.animal_repository import AnimalRepository
                from models import Animal, AnimalType
                from datetime import datetime
                
                repo = AnimalRepository(Animal, db)
                rabbit = repo.get_by_id(rabbit_id)
                
                if not rabbit or rabbit.species != AnimalType.RABBIT:
                    return not_found_response("Rabbit")
                
                if rabbit.discarded:
                    return error_response("Cannot slaughter a discarded rabbit", 400)
                
                if rabbit.slaughtered:
                    return error_response("Rabbit is already slaughtered", 400)
                
                # Mark as slaughtered and in freezer
                slaughter_date = datetime.utcnow()
                rabbit.slaughtered = True
                rabbit.slaughtered_date = slaughter_date
                rabbit.in_freezer = True
                
                # Update related alerts
                from app.services.alert_service import AlertService
                alert_service = AlertService()
                alert_service.update_alerts_for_slaughtered_rabbit(rabbit_id, db)
                
                # Create SLAUGHTER event
                from app.services.event_service import EventService
                event_service = EventService()
                event_data = {
                    'scope': 'INDIVIDUAL',
                    'animal_type': 'RABBIT',
                    'animal_id': rabbit_id,
                    'rabbit_event': 'SLAUGHTER',
                    'date': slaughter_date.isoformat(),
                    'description': f'Conejo {rabbit.name} sacrificado y almacenado en congelador'
                }
                event_service.create_event(event_data)
                
                # Create inventory product entry automatically
                from app.services.inventory_product_service import InventoryProductService
                from models import InventoryProductType, InventoryUnit, InventoryStatus
                from app.repositories.inventory_product_repository import InventoryProductRepository
                from app.repositories.inventory_transaction_repository import InventoryTransactionRepository
                from models import InventoryProduct, InventoryTransaction, InventoryTransactionType
                
                # Use provided user_id or fallback to rabbit's user_id or 'system'
                if not user_id:
                    user_id = getattr(rabbit, 'user_id', None) or 'system'
                
                inventory_product_repo = InventoryProductRepository(InventoryProduct, db)
                inventory_transaction_repo = InventoryTransactionRepository(InventoryTransaction, db)
                
                # Create inventory product
                inventory_product = inventory_product_repo.create(
                    product_type=InventoryProductType.MEAT_RABBIT,
                    product_name=f"Conejo - {rabbit.name}",
                    quantity=1.0,
                    unit=InventoryUnit.UNITS,
                    production_date=slaughter_date,
                    location="congelador",
                    status=InventoryStatus.AVAILABLE,
                    animal_id=rabbit_id,
                    created_by=user_id,
                    notes=f"Conejo sacrificado el {slaughter_date.strftime('%Y-%m-%d')}"
                )
                
                # Create initial transaction (ENTRY)
                inventory_transaction_repo.create(
                    product_id=inventory_product.id,
                    transaction_type=InventoryTransactionType.ENTRY,
                    quantity=1.0,
                    reason="Sacrificio de conejo",
                    user_id=user_id,
                    notes=f"Conejo {rabbit.name} sacrificado y almacenado"
                )
                
                db.commit()
                db.refresh(rabbit)
                
                return success_response(
                    self._serialize_animal(rabbit),
                    "Rabbit slaughtered and stored in freezer successfully",
                    200
                )
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
    
    def _serialize_animal(self, animal: Animal, include_children: bool = False, db=None) -> Dict[str, Any]:
        """
        Serialize animal model to dictionary
        
        Args:
            animal: Animal model instance
            include_children: Whether to include children information (default: False)
            db: Optional database session for querying children
            
        Returns:
            Serialized animal data
        """
        # Get parent information (lazy load if needed)
        mother_info = None
        if animal.mother_id:
            try:
                # Try to access mother relationship (may trigger lazy load)
                if animal.mother:
                    mother_info = {
                        'id': animal.mother.id,
                        'name': animal.mother.name,
                        'species': animal.mother.species.value if animal.mother.species else None
                    }
            except Exception:
                # If relationship is not loaded, just use the ID
                pass
        
        father_info = None
        if animal.father_id:
            try:
                # Try to access father relationship (may trigger lazy load)
                if animal.father:
                    father_info = {
                        'id': animal.father.id,
                        'name': animal.father.name,
                        'species': animal.father.species.value if animal.father.species else None
                    }
            except Exception:
                # If relationship is not loaded, just use the ID
                pass
        
        # Get children information if requested
        children_info = None
        if include_children and db:
            # Optimized: Single query using OR condition instead of two separate queries
            from sqlalchemy import or_
            children = db.query(Animal).filter(
                or_(
                    Animal.mother_id == animal.id,
                    Animal.father_id == animal.id
                ),
                Animal.discarded == False  # Only active children
            ).all()
            
            # Serialize children
            all_children = {}
            for child in children:
                if child.id not in all_children:
                    all_children[child.id] = {
                        'id': child.id,
                        'name': child.name,
                        'species': child.species.value if child.species else None,
                        'gender': child.gender.value if child.gender else None,
                        'birth_date': child.birth_date.isoformat() if child.birth_date else None
                    }
            
            children_info = list(all_children.values())
        
        return {
            'id': animal.id,
            'name': animal.name,
            'species': animal.species.value if animal.species else None,
            'image': animal.image,
            'birth_date': animal.birth_date.isoformat() if animal.birth_date else None,
            'gender': animal.gender.value if animal.gender else None,
            'origin': animal.origin.value if animal.origin else None,
            'mother_id': animal.mother_id,
            'mother': mother_info,
            'father_id': animal.father_id,
            'father': father_info,
            'purchase_date': animal.purchase_date.isoformat() if animal.purchase_date else None,
            'purchase_price': animal.purchase_price,
            'purchase_vendor': animal.purchase_vendor,
            'is_breeder': getattr(animal, 'is_breeder', False),
            'discarded': animal.discarded,
            'discarded_reason': animal.discarded_reason,
            'slaughtered': getattr(animal, 'slaughtered', False),
            'slaughtered_date': getattr(animal, 'slaughtered_date', None).isoformat() if getattr(animal, 'slaughtered_date', None) else None,
            'in_freezer': getattr(animal, 'in_freezer', False),
            'user_id': getattr(animal, 'user_id', None),
            'corral_id': getattr(animal, 'corral_id', None),
            'created_at': animal.created_at.isoformat() if animal.created_at else None,
            'updated_at': animal.updated_at.isoformat() if animal.updated_at else None,
            'children': children_info if include_children else None
        }

