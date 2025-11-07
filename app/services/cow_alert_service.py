"""
Servicio para generar alertas automáticas para vacas
Basado en reglas de negocio específicas para el manejo de ganado bovino
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


class CowAlertService:
    """
    Servicio para generar alertas automáticas para vacas
    """
    
    # Constantes de tiempo (en días)
    DEWORMING_INTERVAL_DAYS = 90  # 3 meses
    BREEDING_AGE_MIN_DAYS = 18 * 30  # 18 meses (aproximado)
    BREEDING_AGE_MAX_DAYS = 24 * 30  # 24 meses
    PREGNANCY_DEWORMING_DAYS = 3 * 30  # 3 meses después de preñez
    PREGNANCY_SALT_STOP_DAYS = 6 * 30  # 6 meses de gestación
    PREGNANCY_PREPARTUM_FOOD_DAYS = 6.5 * 30  # 6.5 meses de gestación
    PREGNANCY_DURATION_DAYS = 9 * 30  # 9 meses de gestación
    PREGNANCY_WINDOW_DAYS = 7  # ±1 semana
    LACTATION_DURATION_DAYS = 7 * 30  # 7 meses de lactancia
    REST_PERIOD_MIN_DAYS = 2 * 30  # 2 meses de reposo
    REST_PERIOD_MAX_DAYS = 3 * 30  # 3 meses de reposo
    
    def create_birth_alerts(self, calf_id: str, birth_date: datetime, mother_id: Optional[str] = None) -> None:
        """
        Crea alertas cuando nace un ternero
        
        Args:
            calf_id: ID del ternero recién nacido
            birth_date: Fecha de nacimiento
            mother_id: ID de la madre (opcional, se puede obtener del ternero)
        
        Reglas para el ternero:
        1. Desparasitación cada 3 meses desde el nacimiento
        2. Si es hembra criadora, alerta para preñarla entre 18-24 meses
        
        Reglas para la madre:
        3. Al nacer: desparasitación y vitaminización de la madre
        4. 7 meses después: alerta para secar la ubre
        5. 2-3 meses después: alerta de reposo
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información del ternero
            calf = animal_repo.get_by_id(calf_id)
            if not calf or calf.species != AnimalType.COW:
                return
            
            # Obtener mother_id del ternero si no se proporcionó
            if not mother_id:
                mother_id = calf.mother_id
            
            # 1. Desparasitación cada 3 meses desde el nacimiento (para el ternero)
            for month_offset in [3, 6, 9, 12, 15, 18, 21, 24]:
                alert_date = birth_date + timedelta(days=month_offset * 30)
                alert_repo.create(
                    name='DEWORMING_REMINDER',
                    description=f'Desparasitación programada para ternero "{calf.name}" (nacido {month_offset} meses atrás)',
                    init_date=alert_date - timedelta(days=7),
                    max_date=alert_date + timedelta(days=7),
                    status=AlertStatus.PENDING,
                    priority=AlertPriority.MEDIUM,
                    animal_type=AnimalType.COW,
                    animal_id=calf_id,
                )
            
            # 2. Si es hembra criadora, alerta para preñarla entre 18-24 meses
            if calf.gender == Gender.FEMALE and getattr(calf, 'is_breeder', False):
                min_date = birth_date + timedelta(days=self.BREEDING_AGE_MIN_DAYS)
                max_date = birth_date + timedelta(days=self.BREEDING_AGE_MAX_DAYS)
                
                alert_repo.create(
                    name='BREEDING_REMINDER',
                    description=f'Ternera criadora "{calf.name}" debe ser preñada (18-24 meses de edad)',
                    init_date=min_date,
                    max_date=max_date,
                    status=AlertStatus.PENDING,
                    priority=AlertPriority.HIGH,
                    animal_type=AnimalType.COW,
                    animal_id=calf_id,
                )
            
            # 3. Al nacer ternero: desparasitación y vitaminización de la madre
            if mother_id:
                mother = animal_repo.get_by_id(mother_id)
                if mother and mother.species == AnimalType.COW and mother.gender == Gender.FEMALE:
                    alert_repo.create(
                        name='POST_BIRTH_CARE',
                        description=f'Desparasitación y vitaminización de vaca "{mother.name}" después del parto del ternero "{calf.name}"',
                        init_date=birth_date,
                        max_date=birth_date + timedelta(days=7),
                        status=AlertStatus.PENDING,
                        priority=AlertPriority.HIGH,
                        animal_type=AnimalType.COW,
                        animal_id=mother_id,
                    )
                    
                    # 4. 7 meses después: alerta para secar la ubre
                    self.create_lactation_alerts(mother_id, birth_date)
    
    def create_pregnancy_alerts(self, cow_id: str, pregnancy_date: datetime) -> None:
        """
        Crea alertas cuando una vaca queda preñada
        
        Reglas:
        1. 3 meses después: desparasitación y vitaminización
        2. 6 meses: dejar sal mineralizada
        3. 6.5 meses: empezar alimento PRE PARTO
        4. 9 meses (±1 semana): nacimiento del ternero
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información de la vaca
            cow = animal_repo.get_by_id(cow_id)
            cow_name = cow.name if cow else "Vaca"
            
            # 1. 3 meses después de preñez: desparasitación y vitaminización
            deworming_date = pregnancy_date + timedelta(days=self.PREGNANCY_DEWORMING_DAYS)
            alert_repo.create(
                name='PREGNANCY_DEWORMING',
                description=f'Desparasitación y vitaminización de vaca preñada "{cow_name}" (3 meses de gestación)',
                init_date=deworming_date - timedelta(days=7),
                max_date=deworming_date + timedelta(days=7),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
            
            # 2. 6 meses: dejar sal mineralizada
            salt_stop_date = pregnancy_date + timedelta(days=self.PREGNANCY_SALT_STOP_DAYS)
            alert_repo.create(
                name='STOP_MINERAL_SALT',
                description=f'Dejar de dar sal mineralizada a vaca preñada "{cow_name}" (6 meses de gestación)',
                init_date=salt_stop_date - timedelta(days=3),
                max_date=salt_stop_date + timedelta(days=3),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
            
            # 3. 6.5 meses: empezar alimento PRE PARTO
            prepartum_start_date = pregnancy_date + timedelta(days=self.PREGNANCY_PREPARTUM_FOOD_DAYS)
            alert_repo.create(
                name='PREPARTUM_FOOD',
                description=f'Empezar a dar alimento PRE PARTO a vaca preñada "{cow_name}" (6.5 meses de gestación)',
                init_date=prepartum_start_date - timedelta(days=3),
                max_date=prepartum_start_date + timedelta(days=3),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
            
            # 4. 9 meses (±1 semana): nacimiento del ternero
            birth_expected_date = pregnancy_date + timedelta(days=self.PREGNANCY_DURATION_DAYS)
            alert_repo.create(
                name='EXPECTED_BIRTH',
                description=f'Nacimiento esperado del ternero de la vaca "{cow_name}" (9 meses de gestación, ±1 semana)',
                init_date=birth_expected_date - timedelta(days=self.PREGNANCY_WINDOW_DAYS),
                max_date=birth_expected_date + timedelta(days=self.PREGNANCY_WINDOW_DAYS),
                status=AlertStatus.PENDING,
                priority=AlertPriority.HIGH,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
    
    def create_lactation_alerts(self, cow_id: str, birth_date: datetime) -> None:
        """
        Crea alertas relacionadas con la lactancia
        
        Reglas:
        1. 7 meses después del parto: alerta para secar la ubre
        2. 2-3 meses después del último ternero: alerta de reposo
        """
        with get_db_session() as db:
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información de la vaca y el ternero
            cow = animal_repo.get_by_id(cow_id)
            cow_name = cow.name if cow else "Vaca"
            
            # Buscar el ternero más reciente de esta vaca
            calf = db.query(Animal).filter(
                Animal.mother_id == cow_id,
                Animal.species == AnimalType.COW,
                Animal.birth_date == birth_date
            ).first()
            calf_name = calf.name if calf else "ternero"
            
            # 1. 7 meses de lactancia: secar la ubre
            drying_date = birth_date + timedelta(days=self.LACTATION_DURATION_DAYS)
            alert_repo.create(
                name='DRY_OFF_UDDER',
                description=f'Iniciar proceso de secado de ubre de vaca "{cow_name}" (7 meses de lactancia del ternero "{calf_name}")',
                init_date=drying_date - timedelta(days=7),
                max_date=drying_date + timedelta(days=7),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
            
            # 2. 2-3 meses después del último ternero: reposo
            rest_min_date = birth_date + timedelta(days=self.REST_PERIOD_MIN_DAYS)
            rest_max_date = birth_date + timedelta(days=self.REST_PERIOD_MAX_DAYS)
            
            alert_repo.create(
                name='REST_PERIOD',
                description=f'Período de reposo de vaca "{cow_name}" después del parto del ternero "{calf_name}" (2-3 meses)',
                init_date=rest_min_date,
                max_date=rest_max_date,
                status=AlertStatus.PENDING,
                priority=AlertPriority.LOW,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )
    
    def create_periodic_deworming_alert(self, cow_id: str, last_deworming_date: datetime) -> None:
        """
        Crea alerta para desparasitación periódica (cada 3 meses)
        Solo crea la alerta si no existe un evento reciente de desparasitación
        """
        with get_db_session() as db:
            from app.repositories.event_repository import EventRepository
            from models import Event
            
            # Verificar si ya existe un evento de desparasitación reciente (últimos 7 días)
            recent_date = datetime.utcnow() - timedelta(days=7)
            
            existing_event = db.query(Event).filter(
                Event.animal_id == cow_id,
                Event.animal_type == AnimalType.COW,
                Event.cow_event == CowEventType.DEWORMING,
                Event.date >= recent_date
            ).first()
            
            # Si ya existe un evento reciente, no crear alerta
            if existing_event:
                return
            
            alert_repo = AlertRepository(Alert, db)
            animal_repo = AnimalRepository(Animal, db)
            
            # Obtener información de la vaca
            cow = animal_repo.get_by_id(cow_id)
            cow_name = cow.name if cow else "Vaca"
            
            next_deworming = last_deworming_date + timedelta(days=self.DEWORMING_INTERVAL_DAYS)
            
            alert_repo.create(
                name='DEWORMING_REMINDER',
                description=f'Desparasitación periódica de vaca "{cow_name}" (cada 3 meses)',
                init_date=next_deworming - timedelta(days=7),
                max_date=next_deworming + timedelta(days=7),
                status=AlertStatus.PENDING,
                priority=AlertPriority.MEDIUM,
                animal_type=AnimalType.COW,
                animal_id=cow_id,
            )

