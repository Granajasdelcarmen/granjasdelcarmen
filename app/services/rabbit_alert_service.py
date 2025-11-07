"""
Servicio para generar alertas automáticas para conejos
Basado en reglas de negocio específicas para el manejo de conejos
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.repositories.alert_repository import AlertRepository
from app.repositories.animal_repository import AnimalRepository
from app.utils.database import get_db_session
from models import (
    Alert,
    AlertStatus,
    AlertPriority,
    Animal,
    AnimalType,
    Gender,
)


class RabbitAlertService:
    """
    Servicio para generar alertas automáticas para conejos
    """
    
    # Constantes de tiempo (en días)
    BREEDING_READY_AGE_DAYS = 4 * 30  # 4 meses
    PREGNANCY_DURATION_DAYS = 30  # 30 días de gestación
    LACTATION_DURATION_DAYS = 30  # 30 días de lactancia
    REST_PERIOD_DAYS = 15  # 15 días de descanso
    SLAUGHTER_MIN_DAYS = 80  # 80 días (mínimo para sacrificio)
    SLAUGHTER_MAX_DAYS = 90  # 90 días (máximo para sacrificio)
    
    def create_birth_alerts(self, rabbit_id: str, birth_date: datetime) -> None:
        """
        Crea alertas cuando nace un conejo
        
        Reglas:
        1. Si es hembra criadora, alerta para preñarla a los 4 meses
        2. Si NO es criador, alerta para sacrificio entre 80-90 días
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información del conejo
            rabbit = animal_repo.get_by_id(rabbit_id)
            if not rabbit or rabbit.species != AnimalType.RABBIT:
                return
            
            # 1. Si es hembra criadora, alerta para preñarla a los 4 meses
            if rabbit.gender == Gender.FEMALE and getattr(rabbit, 'is_breeder', False):
                breeding_ready_date = birth_date + timedelta(days=self.BREEDING_READY_AGE_DAYS)
                
                alert_repo.create(
                    name='BREEDING_READY',
                    description=f'Coneja criadora "{rabbit.name}" está lista para quedar preñada (4 meses de edad)',
                    init_date=breeding_ready_date - timedelta(days=3),
                    max_date=breeding_ready_date + timedelta(days=7),
                    status=AlertStatus.PENDING,
                    priority=AlertPriority.HIGH,
                    animal_type=AnimalType.RABBIT,
                    animal_id=rabbit_id,
                )
            
            # 2. Si NO es criador, alerta para sacrificio entre 80-90 días
            if not getattr(rabbit, 'is_breeder', False):
                slaughter_min_date = birth_date + timedelta(days=self.SLAUGHTER_MIN_DAYS)
                slaughter_max_date = birth_date + timedelta(days=self.SLAUGHTER_MAX_DAYS)
                
                alert_repo.create(
                    name='SLAUGHTER_REMINDER',
                    description=f'Conejo "{rabbit.name}" debe ser sacrificado (80-90 días de edad)',
                    init_date=slaughter_min_date,
                    max_date=slaughter_max_date,
                    status=AlertStatus.PENDING,
                    priority=AlertPriority.MEDIUM,
                    animal_type=AnimalType.RABBIT,
                    animal_id=rabbit_id,
                )
    
    def create_pregnancy_alerts(self, rabbit_id: str, pregnancy_date: datetime) -> None:
        """
        Crea alertas cuando una coneja queda preñada
        
        Reglas:
        1. 30 días después: nacimiento de la camada
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información de la coneja
            rabbit = animal_repo.get_by_id(rabbit_id)
            rabbit_name = rabbit.name if rabbit else "Coneja"
            
            # 1. 30 días después: nacimiento de la camada
            birth_expected_date = pregnancy_date + timedelta(days=self.PREGNANCY_DURATION_DAYS)
            
            alert_repo.create(
                name='EXPECTED_BIRTH',
                description=f'Nacimiento esperado de camada de la coneja "{rabbit_name}" (30 días de gestación)',
                init_date=birth_expected_date - timedelta(days=2),
                max_date=birth_expected_date + timedelta(days=2),
                status=AlertStatus.PENDING,
                priority=AlertPriority.HIGH,
                animal_type=AnimalType.RABBIT,
                animal_id=rabbit_id,
            )
    
    def create_lactation_alerts(self, rabbit_id: str, birth_date: datetime) -> None:
        """
        Crea alertas relacionadas con la lactancia
        
        Reglas:
        1. 30 días después del parto: separar camada de la criadora
        2. 15 días después de separar: coneja lista para quedar preñada de nuevo
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información de la coneja y sus hijos
            rabbit = animal_repo.get_by_id(rabbit_id)
            rabbit_name = rabbit.name if rabbit else "Coneja"
            
            # Obtener hijos de la coneja (camada)
            if rabbit:
                children = db.query(Animal).filter(
                    Animal.mother_id == rabbit_id,
                    Animal.species == AnimalType.RABBIT,
                    Animal.discarded == False
                ).all()
                children_names = [child.name for child in children]
                children_list = ", ".join(children_names) if children_names else "camada"
            else:
                children_list = "camada"
            
            # 1. 30 días de lactancia: separar camada
            separation_date = birth_date + timedelta(days=self.LACTATION_DURATION_DAYS)
            
            alert_repo.create(
                name='SEPARATE_LITTER',
                description=f'Separar camada de la criadora "{rabbit_name}" (30 días de lactancia) - Conejos: {children_list}',
                init_date=separation_date - timedelta(days=2),
                max_date=separation_date + timedelta(days=2),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.RABBIT,
                animal_id=rabbit_id,
            )
            
            # 2. 15 días después de separar: coneja lista para quedar preñada de nuevo
            rest_end_date = separation_date + timedelta(days=self.REST_PERIOD_DAYS)
            
            alert_repo.create(
                name='BREEDING_READY',
                description=f'Coneja "{rabbit_name}" lista para quedar preñada de nuevo (15 días de descanso completados)',
                init_date=rest_end_date - timedelta(days=2),
                max_date=rest_end_date + timedelta(days=7),
                status=AlertStatus.PENDING,
                priority=AlertPriority.HIGH,
                animal_type=AnimalType.RABBIT,
                animal_id=rabbit_id,
            )
    
    def create_grouped_slaughter_alerts(self, mother_id: Optional[str] = None) -> None:
        """
        Crea alertas agrupadas de sacrificio para conejos no criadores
        que están en el rango de 80-90 días
        
        Args:
            mother_id: Si se proporciona, solo agrupa hijos de esta madre
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            today = datetime.utcnow()
            min_birth_date = today - timedelta(days=self.SLAUGHTER_MAX_DAYS)
            max_birth_date = today - timedelta(days=self.SLAUGHTER_MIN_DAYS)
            
            # Buscar conejos no criadores en el rango de edad
            # Excluir conejos ya sacrificados o descartados
            query = db.query(Animal).filter(
                Animal.species == AnimalType.RABBIT,
                Animal.is_breeder == False,
                Animal.discarded == False,
                Animal.slaughtered == False,  # No incluir ya sacrificados
                Animal.birth_date >= min_birth_date,
                Animal.birth_date <= max_birth_date
            )
            
            if mother_id:
                query = query.filter(Animal.mother_id == mother_id)
            
            rabbits_to_slaughter = query.all()
            
            if not rabbits_to_slaughter:
                return
            
            # Agrupar por madre para crear alertas más organizadas
            by_mother = {}
            for rabbit in rabbits_to_slaughter:
                mother_id_key = rabbit.mother_id or 'sin_madre'
                if mother_id_key not in by_mother:
                    by_mother[mother_id_key] = []
                by_mother[mother_id_key].append(rabbit)
            
            # Crear una alerta por cada grupo de madre
            for mother_id_key, rabbits in by_mother.items():
                # Verificar si ya existe una alerta pendiente para estos conejos
                rabbit_ids_list = [r.id for r in rabbits]
                import json
                rabbit_ids_json = json.dumps(rabbit_ids_list)
                
                # Usar el animal_id de la madre si existe, o del primer conejo si no
                alert_animal_id = mother_id_key if mother_id_key != 'sin_madre' else rabbits[0].id
                
                # Buscar alertas pendientes con los mismos IDs (alertas nuevas)
                existing_alert = db.query(Alert).filter(
                    Alert.name == 'SLAUGHTER_REMINDER',
                    Alert.status == AlertStatus.PENDING,
                    Alert.rabbit_ids == rabbit_ids_json
                ).first()
                
                # Si no hay alerta con rabbit_ids, verificar por animal_id (alertas antiguas)
                if not existing_alert and alert_animal_id != 'sin_madre':
                    existing_alert = db.query(Alert).filter(
                        Alert.name == 'SLAUGHTER_REMINDER',
                        Alert.status == AlertStatus.PENDING,
                        Alert.animal_id == alert_animal_id,
                        Alert.animal_type == AnimalType.RABBIT
                    ).first()
                    
                    # Si encontramos una alerta antigua, actualizar con rabbit_ids
                    if existing_alert:
                        existing_alert.rabbit_ids = rabbit_ids_json
                        db.commit()
                
                if existing_alert:
                    # Ya existe una alerta para estos conejos, no crear duplicado
                    continue
                
                rabbit_names = [r.name for r in rabbits]
                names_list = ", ".join(rabbit_names)
                
                alert_repo.create(
                    name='SLAUGHTER_REMINDER',
                    description=f'Conejos no criadores deben ser sacrificados (80-90 días de edad) - Conejos: {names_list}',
                    init_date=today - timedelta(days=self.SLAUGHTER_MAX_DAYS - self.SLAUGHTER_MIN_DAYS),
                    max_date=today + timedelta(days=7),
                    status=AlertStatus.PENDING,
                    priority=AlertPriority.MEDIUM,
                    animal_type=AnimalType.RABBIT,
                    animal_id=alert_animal_id,
                    rabbit_ids=rabbit_ids_json,  # Almacenar IDs de los conejos
                )

