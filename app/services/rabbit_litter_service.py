"""
Rabbit Litter Service - Handles creation of rabbit litters and dead offspring
"""
from typing import List, Dict, Any
from datetime import timedelta
from app.repositories.animal_repository import AnimalRepository
from app.repositories.base import BaseRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_enum_value, validate_date_format
from app.utils.response import success_response, error_response
from models import Animal, AnimalType, Gender, AnimalOrigin, DeadOffspring
import uuid


class RabbitLitterService:
    """
    Service for handling rabbit litter operations
    """
    
    def create_litter(self, litter_data: Dict[str, Any]) -> tuple:
        """
        Create a litter of rabbits (multiple rabbits at once) and optionally register dead offspring
        
        Args:
            litter_data: Dictionary with:
                - mother_id (required): ID of the mother rabbit
                - father_id (optional): ID of the father rabbit
                - birth_date (required): Birth date for all rabbits in the litter
                - count (required): Number of LIVE rabbits to create (5-12 typical)
                - genders (optional): List of genders ['MALE', 'FEMALE'] for each live rabbit
                - name_prefix (optional): Prefix for rabbit names (default: "Conejo")
                - corral_id (optional): Corral ID for all rabbits
                - dead_count (optional): Number of dead offspring (default: 0)
                - dead_notes (optional): Notes about dead offspring
                - dead_suspected_cause (optional): Suspected cause of death
                - recorded_by (required if dead_count > 0): User ID who recorded this
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(litter_data, ['mother_id', 'birth_date', 'count'])
            
            mother_id = litter_data['mother_id']
            father_id = litter_data.get('father_id')
            birth_date = validate_date_format(litter_data['birth_date'])
            count = int(litter_data['count'])
            
            # Validate count (typical range 5-12, but allow flexibility)
            if count < 1 or count > 20:
                return error_response("Count must be between 1 and 20", 400)
            
            # Parse genders if provided
            genders = litter_data.get('genders', [])
            if genders and len(genders) != count:
                return error_response(f"Number of genders ({len(genders)}) must match count ({count})", 400)
            
            # Validate genders if provided
            if genders:
                for gender in genders:
                    validate_enum_value(gender, ['MALE', 'FEMALE'], 'gender')
            
            name_prefix = litter_data.get('name_prefix', 'Conejo')
            corral_id = litter_data.get('corral_id')
            
            with get_db_session() as db:
                animal_repo = AnimalRepository(Animal, db)
                
                # Validate mother exists and is a rabbit
                mother = animal_repo.get_by_id(mother_id)
                if not mother:
                    return error_response("Mother rabbit not found", 404)
                if mother.species != AnimalType.RABBIT:
                    return error_response("Mother must be a rabbit", 400)
                if mother.gender != Gender.FEMALE:
                    return error_response("Mother must be FEMALE", 400)
                if mother.discarded:
                    return error_response("Mother rabbit is discarded", 400)
                
                # Validate father if provided
                father = None
                if father_id:
                    father = animal_repo.get_by_id(father_id)
                    if not father:
                        return error_response("Father rabbit not found", 404)
                    if father.species != AnimalType.RABBIT:
                        return error_response("Father must be a rabbit", 400)
                    if father.gender != Gender.MALE:
                        return error_response("Father must be MALE", 400)
                    if father.discarded:
                        return error_response("Father rabbit is discarded", 400)
                
                # Create rabbits (all in one transaction)
                created_rabbits = []
                try:
                    for i in range(count):
                        # Determine gender
                        if genders and i < len(genders):
                            gender = Gender(genders[i])
                        else:
                            # Default: alternate or random (for simplicity, alternate)
                            gender = Gender.MALE if i % 2 == 0 else Gender.FEMALE
                        
                        # Generate name
                        rabbit_name = f"{name_prefix} {i + 1}"
                        
                        # Create rabbit data
                        rabbit_data = {
                            'id': str(uuid.uuid4()),
                            'name': rabbit_name,
                            'species': AnimalType.RABBIT,
                            'gender': gender,
                            'birth_date': birth_date,
                            'origin': AnimalOrigin.BORN,
                            'mother_id': mother_id,
                            'father_id': father_id if father_id else None,
                            'corral_id': corral_id
                        }
                        
                        # Create rabbit instance and add to session (without commit)
                        rabbit = Animal(**rabbit_data)
                        db.add(rabbit)
                        created_rabbits.append(rabbit)
                    
                    # Handle dead offspring if provided (before commit)
                    dead_offspring_record = None
                    dead_count = int(litter_data.get('dead_count', 0))
                    if dead_count > 0:
                        recorded_by = litter_data.get('recorded_by')
                        if not recorded_by:
                            db.rollback()
                            return error_response("recorded_by is required when dead_count > 0", 400)
                        
                        dead_offspring_record = DeadOffspring(
                            mother_id=mother_id,
                            father_id=father_id if father_id else None,
                            birth_date=birth_date,
                            species=AnimalType.RABBIT,
                            count=dead_count,
                            notes=litter_data.get('dead_notes'),
                            suspected_cause=litter_data.get('dead_suspected_cause'),
                            recorded_by=recorded_by
                        )
                        db.add(dead_offspring_record)
                    
                    # Commit all at once
                    db.commit()
                    
                    # Crear alertas automáticas para la coneja madre (lactancia)
                    from app.services.rabbit_alert_service import RabbitAlertService
                    rabbit_alert_service = RabbitAlertService()
                    rabbit_alert_service.create_lactation_alerts(mother_id, birth_date)
                    
                    # Crear alertas para cada conejo recién nacido
                    # Para hembras criadoras: alerta individual de reproducción
                    # Para no criadores: crear alerta agrupada de sacrificio para toda la camada
                    non_breeder_rabbits = [r for r in created_rabbits if not getattr(r, 'is_breeder', False)]
                    breeder_rabbits = [r for r in created_rabbits if getattr(r, 'is_breeder', False)]
                    
                    # Alertas individuales para criadores
                    for rabbit in breeder_rabbits:
                        if rabbit.birth_date:
                            rabbit_alert_service.create_birth_alerts(rabbit.id, rabbit.birth_date)
                    
                    # Alerta agrupada de sacrificio para no criadores de la misma camada
                    if non_breeder_rabbits:
                        rabbit_names = [r.name for r in non_breeder_rabbits]
                        names_list = ", ".join(rabbit_names)
                        
                        slaughter_min_date = birth_date + timedelta(days=rabbit_alert_service.SLAUGHTER_MIN_DAYS)
                        slaughter_max_date = birth_date + timedelta(days=rabbit_alert_service.SLAUGHTER_MAX_DAYS)
                        
                        from app.repositories.alert_repository import AlertRepository
                        from models import Alert, AlertStatus, AlertPriority
                        import json
                        alert_repo = AlertRepository(Alert, db)
                        
                        # Almacenar IDs de los conejos en la alerta
                        rabbit_ids_list = [r.id for r in non_breeder_rabbits]
                        rabbit_ids_json = json.dumps(rabbit_ids_list)
                        
                        alert_repo.create(
                            name='SLAUGHTER_REMINDER',
                            description=f'Conejos no criadores deben ser sacrificados (80-90 días de edad) - Conejos: {names_list}',
                            init_date=slaughter_min_date,
                            max_date=slaughter_max_date,
                            status=AlertStatus.PENDING,
                            priority=AlertPriority.MEDIUM,
                            animal_type=AnimalType.RABBIT,
                            animal_id=mother_id,  # Usar ID de la madre para agrupar
                            rabbit_ids=rabbit_ids_json,  # Almacenar IDs de los conejos
                        )
                    
                    # Refresh all objects
                    for rabbit in created_rabbits:
                        db.refresh(rabbit)
                    if dead_offspring_record:
                        db.refresh(dead_offspring_record)
                        
                except Exception as e:
                    db.rollback()
                    raise e
                
                # Serialize created rabbits
                rabbits_data = []
                for rabbit in created_rabbits:
                    rabbits_data.append({
                        'id': rabbit.id,
                        'name': rabbit.name,
                        'gender': rabbit.gender.value if rabbit.gender else None,
                        'birth_date': rabbit.birth_date.isoformat() if rabbit.birth_date else None,
                        'mother_id': rabbit.mother_id,
                        'father_id': rabbit.father_id
                    })
                
                response_data = {
                    'litter': rabbits_data,
                    'count': len(created_rabbits),
                    'mother_id': mother_id,
                    'father_id': father_id
                }
                
                if dead_offspring_record:
                    response_data['dead_offspring'] = {
                        'id': dead_offspring_record.id,
                        'count': dead_offspring_record.count,
                        'notes': dead_offspring_record.notes,
                        'suspected_cause': dead_offspring_record.suspected_cause
                    }
                
                message = f"Litter of {len(created_rabbits)} live rabbits created"
                if dead_count > 0:
                    message += f" and {dead_count} dead offspring registered"
                message += " successfully"
                
                return success_response(response_data, message, 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def register_dead_offspring(self, dead_offspring_data: Dict[str, Any]) -> tuple:
        """
        Register dead offspring (rabbits born dead)
        
        Args:
            dead_offspring_data: Dictionary with:
                - mother_id (required): ID of the mother
                - father_id (optional): ID of the father
                - birth_date (required): Date when they were born dead
                - count (required): Number of dead offspring
                - notes (optional): Notes about possible causes
                - suspected_cause (optional): Suspected cause (e.g., "enfermedad", "déficit vitamínico", "alimento")
                - recorded_by (required): User ID who recorded this
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(dead_offspring_data, ['mother_id', 'birth_date', 'count', 'recorded_by'])
            
            mother_id = dead_offspring_data['mother_id']
            father_id = dead_offspring_data.get('father_id')
            birth_date = validate_date_format(dead_offspring_data['birth_date'])
            count = int(dead_offspring_data['count'])
            notes = dead_offspring_data.get('notes')
            suspected_cause = dead_offspring_data.get('suspected_cause')
            recorded_by = dead_offspring_data['recorded_by']
            
            # Validate count
            if count < 1:
                return error_response("Count must be at least 1", 400)
            
            with get_db_session() as db:
                animal_repo = AnimalRepository(Animal, db)
                dead_offspring_repo = BaseRepository(DeadOffspring, db)
                
                # Validate mother exists
                mother = animal_repo.get_by_id(mother_id)
                if not mother:
                    return error_response("Mother not found", 404)
                if mother.species != AnimalType.RABBIT:
                    return error_response("Mother must be a rabbit", 400)
                
                # Validate father if provided
                if father_id:
                    father = animal_repo.get_by_id(father_id)
                    if not father:
                        return error_response("Father not found", 404)
                    if father.species != AnimalType.RABBIT:
                        return error_response("Father must be a rabbit", 400)
                
                # Create dead offspring record
                dead_offspring_record = dead_offspring_repo.create(
                    mother_id=mother_id,
                    father_id=father_id,
                    birth_date=birth_date,
                    species=AnimalType.RABBIT,
                    count=count,
                    notes=notes,
                    suspected_cause=suspected_cause,
                    recorded_by=recorded_by
                )
                
                return success_response(
                    {
                        'id': dead_offspring_record.id,
                        'mother_id': dead_offspring_record.mother_id,
                        'father_id': dead_offspring_record.father_id,
                        'birth_date': dead_offspring_record.birth_date.isoformat() if dead_offspring_record.birth_date else None,
                        'count': dead_offspring_record.count,
                        'notes': dead_offspring_record.notes,
                        'suspected_cause': dead_offspring_record.suspected_cause,
                        'recorded_by': dead_offspring_record.recorded_by,
                        'created_at': dead_offspring_record.created_at.isoformat() if dead_offspring_record.created_at else None
                    },
                    f"Registered {count} dead offspring",
                    201
                )
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_dead_offspring_by_mother(self, mother_id: str) -> tuple:
        """
        Get all dead offspring records for a specific mother
        
        Args:
            mother_id: ID of the mother
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                dead_offspring_repo = BaseRepository(DeadOffspring, db)
                
                # Query dead offspring by mother
                dead_offspring_list = db.query(DeadOffspring).filter(
                    DeadOffspring.mother_id == mother_id
                ).order_by(DeadOffspring.birth_date.desc()).all()
                
                # Serialize
                records = []
                for record in dead_offspring_list:
                    records.append({
                        'id': record.id,
                        'mother_id': record.mother_id,
                        'father_id': record.father_id,
                        'birth_date': record.birth_date.isoformat() if record.birth_date else None,
                        'death_date': record.death_date.isoformat() if record.death_date else None,
                        'count': record.count,
                        'notes': record.notes,
                        'suspected_cause': record.suspected_cause,
                        'recorded_by': record.recorded_by,
                        'created_at': record.created_at.isoformat() if record.created_at else None
                    })
                
                return success_response(records)
        except Exception as e:
            return error_response(str(e), 500)

