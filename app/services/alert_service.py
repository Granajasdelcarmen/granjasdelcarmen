from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.repositories.alert_repository import AlertRepository
from app.repositories.event_repository import EventRepository
from app.services.event_service import EventService
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response, not_found_response
from models import Alert, AlertStatus, Event, AnimalType, Scope, CowEventType, RabbitEventType, SheepEventType


class AlertService:
    def list_alerts(self, params: Dict[str, Any]) -> tuple:
        try:
            with get_db_session() as db:
                # Primero verificar y actualizar alertas vencidas y obsoletas
                self.verify_and_update_alerts(db)
                
                repo = AlertRepository(Alert, db)
                status = params.get('status', 'PENDING')
                alerts = repo.list_pending_by_urgency(status=AlertStatus(status))
                return success_response([self._serialize(a) for a in alerts])
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_alerts_for_slaughtered_rabbit(self, rabbit_id: str, db) -> None:
        """
        Actualiza alertas de sacrificio cuando un conejo se sacrifica directamente
        (no desde la alerta)
        
        Args:
            rabbit_id: ID del conejo que fue sacrificado
            db: Sesión de base de datos
        """
        import json
        from models import Animal
        
        # Buscar todas las alertas de sacrificio pendientes que incluyen este conejo
        alerts = db.query(Alert).filter(
            Alert.name == 'SLAUGHTER_REMINDER',
            Alert.status == AlertStatus.PENDING,
            Alert.animal_type == AnimalType.RABBIT
        ).all()
        
        for alert in alerts:
            # Obtener IDs de conejos de la alerta
            rabbit_ids = []
            if hasattr(alert, 'rabbit_ids') and alert.rabbit_ids:
                try:
                    rabbit_ids = json.loads(alert.rabbit_ids)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Si la alerta no tiene rabbit_ids, verificar por animal_id (madre)
            if not rabbit_ids and alert.animal_id:
                from app.services.rabbit_alert_service import RabbitAlertService
                rabbit_alert_service = RabbitAlertService()
                today = datetime.utcnow()
                min_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MAX_DAYS)
                max_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MIN_DAYS)
                
                query = db.query(Animal).filter(
                    Animal.species == AnimalType.RABBIT,
                    Animal.is_breeder == False,
                    Animal.discarded == False,
                    Animal.slaughtered == False,
                    Animal.birth_date >= min_birth_date,
                    Animal.birth_date <= max_birth_date,
                    Animal.mother_id == alert.animal_id
                )
                rabbits_to_slaughter = query.all()
                rabbit_ids = [r.id for r in rabbits_to_slaughter]
            
            # Si este conejo está en la alerta, verificar si todos los conejos ya fueron sacrificados
            if rabbit_id in rabbit_ids:
                # Verificar cuántos conejos de la alerta aún no están sacrificados
                remaining_rabbits = db.query(Animal).filter(
                    Animal.id.in_(rabbit_ids),
                    Animal.species == AnimalType.RABBIT,
                    Animal.slaughtered == False,
                    Animal.discarded == False
                ).all()
                
                # Si todos los conejos fueron sacrificados, marcar alerta como completada
                if not remaining_rabbits:
                    alert.status = AlertStatus.DONE
                    alert.resolved_at = datetime.utcnow()
                else:
                    # Actualizar la descripción con los conejos que aún faltan
                    remaining_names = [r.name for r in remaining_rabbits]
                    names_list = ", ".join(remaining_names)
                    alert.description = f'Conejos no criadores deben ser sacrificados (80-90 días de edad) - Conejos: {names_list}'
                    
                    # Actualizar rabbit_ids para reflejar solo los que faltan
                    remaining_ids = [r.id for r in remaining_rabbits]
                    alert.rabbit_ids = json.dumps(remaining_ids)
    
    def verify_and_update_alerts(self, db=None) -> None:
        """
        Verifica y actualiza el estado de las alertas:
        1. Marca como EXPIRED las alertas vencidas (max_date pasado)
        2. Verifica que los conejos en alertas de sacrificio aún necesiten ser sacrificados
        
        Args:
            db: Sesión de base de datos (opcional, se crea una si no se proporciona)
        """
        import json
        from models import Animal
        
        if db is None:
            with get_db_session() as session:
                self._do_verify_and_update(session)
        else:
            self._do_verify_and_update(db)
    
    def _do_verify_and_update(self, db) -> None:
        """Método auxiliar que realiza la verificación y actualización"""
        import json
        from models import Animal
        
        today = datetime.utcnow()
        
        # 1. Marcar alertas vencidas como EXPIRED
        expired_alerts = db.query(Alert).filter(
            Alert.status == AlertStatus.PENDING,
            Alert.max_date < today
        ).all()
        
        for alert in expired_alerts:
            alert.status = AlertStatus.EXPIRED
            alert.resolved_at = today
        
        # 2. Verificar alertas de sacrificio: si todos los conejos ya fueron sacrificados, completar la alerta
        slaughter_alerts = db.query(Alert).filter(
            Alert.name == 'SLAUGHTER_REMINDER',
            Alert.status == AlertStatus.PENDING,
            Alert.animal_type == AnimalType.RABBIT
        ).all()
        
        for alert in slaughter_alerts:
            # Obtener IDs de conejos de la alerta
            rabbit_ids = []
            if hasattr(alert, 'rabbit_ids') and alert.rabbit_ids:
                try:
                    rabbit_ids = json.loads(alert.rabbit_ids)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Si no tiene rabbit_ids, intentar obtenerlos por animal_id
            if not rabbit_ids and alert.animal_id:
                from app.services.rabbit_alert_service import RabbitAlertService
                rabbit_alert_service = RabbitAlertService()
                min_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MAX_DAYS)
                max_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MIN_DAYS)
                
                query = db.query(Animal).filter(
                    Animal.species == AnimalType.RABBIT,
                    Animal.is_breeder == False,
                    Animal.discarded == False,
                    Animal.slaughtered == False,
                    Animal.birth_date >= min_birth_date,
                    Animal.birth_date <= max_birth_date,
                    Animal.mother_id == alert.animal_id
                )
                rabbits_to_slaughter = query.all()
                rabbit_ids = [r.id for r in rabbits_to_slaughter]
                
                # Guardar los IDs en la alerta
                if rabbit_ids:
                    alert.rabbit_ids = json.dumps(rabbit_ids)
            
            # Verificar si todos los conejos ya fueron sacrificados o descartados
            if rabbit_ids:
                remaining_rabbits = db.query(Animal).filter(
                    Animal.id.in_(rabbit_ids),
                    Animal.species == AnimalType.RABBIT,
                    Animal.slaughtered == False,
                    Animal.discarded == False
                ).all()
                
                # Si todos fueron sacrificados/descartados, marcar alerta como completada
                if not remaining_rabbits:
                    alert.status = AlertStatus.DONE
                    alert.resolved_at = today
                else:
                    # Actualizar descripción con los que aún faltan
                    remaining_names = [r.name for r in remaining_rabbits]
                    names_list = ", ".join(remaining_names)
                    alert.description = f'Conejos no criadores deben ser sacrificados (80-90 días de edad) - Conejos: {names_list}'
                    
                    # Actualizar rabbit_ids
                    remaining_ids = [r.id for r in remaining_rabbits]
                    alert.rabbit_ids = json.dumps(remaining_ids)
        
        db.commit()
    
    def complete_alert(self, alert_id: int, slaughtered_rabbit_ids: Optional[list] = None) -> tuple:
        """
        Mark an alert as completed (DONE) and create the corresponding event
        
        Args:
            alert_id: Alert ID to complete
            slaughtered_rabbit_ids: Lista de IDs de conejos que fueron sacrificados (solo para alertas de sacrificio)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                from app.repositories.animal_repository import AnimalRepository
                from models import Animal
                
                repo = AlertRepository(Alert, db)
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                
                if not alert:
                    return not_found_response("Alert")
                
                if alert.status == AlertStatus.DONE:
                    return error_response("Alert is already completed", 400)
                
                # Si es una alerta de sacrificio, procesar los conejos seleccionados
                if alert.name == 'SLAUGHTER_REMINDER' and alert.animal_type == AnimalType.RABBIT:
                    if not slaughtered_rabbit_ids:
                        return error_response("Lista de conejos sacrificados es requerida para alertas de sacrificio", 400)
                    
                    # Obtener los IDs de conejos de la alerta
                    import json
                    alert_rabbit_ids = []
                    if hasattr(alert, 'rabbit_ids') and alert.rabbit_ids:
                        try:
                            alert_rabbit_ids = json.loads(alert.rabbit_ids)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    # Si la alerta no tiene rabbit_ids (alerta antigua), obtenerlos dinámicamente
                    if not alert_rabbit_ids:
                        from datetime import timedelta
                        from app.services.rabbit_alert_service import RabbitAlertService
                        
                        rabbit_alert_service = RabbitAlertService()
                        today = datetime.utcnow()
                        min_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MAX_DAYS)
                        max_birth_date = today - timedelta(days=rabbit_alert_service.SLAUGHTER_MIN_DAYS)
                        
                        query = db.query(Animal).filter(
                            Animal.species == AnimalType.RABBIT,
                            Animal.is_breeder == False,
                            Animal.discarded == False,
                            Animal.slaughtered == False,
                            Animal.birth_date >= min_birth_date,
                            Animal.birth_date <= max_birth_date
                        )
                        
                        if alert.animal_id:
                            query = query.filter(Animal.mother_id == alert.animal_id)
                        
                        rabbits_to_slaughter = query.all()
                        alert_rabbit_ids = [r.id for r in rabbits_to_slaughter]
                        
                        # Guardar los IDs en la alerta para futuras referencias
                        alert.rabbit_ids = json.dumps(alert_rabbit_ids)
                    
                    # Validar que los IDs proporcionados estén en la alerta
                    invalid_ids = [rid for rid in slaughtered_rabbit_ids if rid not in alert_rabbit_ids]
                    if invalid_ids:
                        return error_response(f"Algunos IDs de conejos no pertenecen a esta alerta: {invalid_ids}", 400)
                    
                    # Marcar conejos como sacrificados y en congelador
                    animal_repo = AnimalRepository(Animal, db)
                    slaughter_date = datetime.utcnow()
                    
                    for rabbit_id in slaughtered_rabbit_ids:
                        rabbit = animal_repo.get_by_id(rabbit_id)
                        if rabbit:
                            rabbit.slaughtered = True
                            rabbit.slaughtered_date = slaughter_date
                            rabbit.in_freezer = True  # Por defecto van al congelador
                            # NO marcar como discarded, porque no se perdió, está en congelador
                            
                            # Actualizar otras alertas que puedan incluir este conejo
                            self.update_alerts_for_slaughtered_rabbit(rabbit_id, db)
                    
                    # Crear eventos de sacrificio para cada conejo
                    from app.services.event_service import EventService
                    event_service = EventService()
                    
                    for rabbit_id in slaughtered_rabbit_ids:
                        event_data = {
                            'scope': 'INDIVIDUAL',
                            'animal_type': 'RABBIT',
                            'animal_id': rabbit_id,
                            'rabbit_event': 'SLAUGHTER',
                            'date': slaughter_date.isoformat(),
                            'description': f'Conejo sacrificado y almacenado en congelador'
                        }
                        event_service.create_event(event_data)
                
                # Crear evento correspondiente antes de marcar como completada (para otras alertas)
                if alert.name != 'SLAUGHTER_REMINDER':
                    event_created = self._create_event_from_alert(alert, db)
                    if event_created:
                        alert.event_id = event_created.id
                
                # Marcar alerta como completada
                alert.status = AlertStatus.DONE
                alert.resolved_at = datetime.utcnow()
                
                db.commit()
                
                return success_response(self._serialize(alert), "Alert completed successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def _create_event_from_alert(self, alert: Alert, db) -> Optional[Event]:
        """
        Crea un evento correspondiente a una alerta completada
        
        Args:
            alert: La alerta que se está completando
            db: Sesión de base de datos
            
        Returns:
            Event creado o None si no se puede crear
        """
        if not alert.animal_type:
            return None
        
        # Mapear tipos de alertas a tipos de eventos
        alert_to_event_mapping = {
            'DEWORMING_REMINDER': {
                'COW': CowEventType.DEWORMING,
                'SHEEP': SheepEventType.DEWORMING,
                'RABBIT': None,  # Los conejos no tienen evento de desparasitación individual
            },
            'PREGNANCY_DEWORMING': {
                'COW': CowEventType.DEWORMING,
            },
            'POST_BIRTH_CARE': {
                'COW': CowEventType.DEWORMING,  # Se crea evento de desparasitación, vitaminización se puede agregar después
            },
            'BREEDING_READY': {
                'RABBIT': RabbitEventType.PREGNANCY,
            },
            'BREEDING_REMINDER': {
                'COW': CowEventType.PREGNANCY,
            },
            'EXPECTED_BIRTH': {
                'COW': CowEventType.BIRTH,
                'RABBIT': None,  # El nacimiento de conejos se registra como camada, no como evento individual
            },
            'DRY_OFF_UDDER': {
                'COW': CowEventType.DRY_OFF,
            },
            'SEPARATE_LITTER': {
                'RABBIT': None,  # No es un evento, es una acción manual
            },
            'SLAUGHTER_REMINDER': {
                'RABBIT': RabbitEventType.SLAUGHTER,
            },
            'STOP_MINERAL_SALT': {
                'COW': None,  # No es un evento, es una acción
            },
            'PREPARTUM_FOOD': {
                'COW': None,  # No es un evento, es una acción
            },
            'REST_PERIOD': {
                'COW': None,  # No es un evento, es un período
            },
        }
        
        # Obtener el tipo de evento correspondiente
        event_type_mapping = alert_to_event_mapping.get(alert.name, {})
        event_type = event_type_mapping.get(alert.animal_type.name) if alert.animal_type else None
        
        if not event_type:
            # Esta alerta no requiere crear un evento
            return None
        
        # Determinar el scope
        scope = Scope.INDIVIDUAL if alert.animal_id else Scope.GROUP
        
        # Preparar datos del evento
        event_data = {
            'scope': scope.name,
            'animal_type': alert.animal_type.name,
            'date': datetime.utcnow().isoformat(),
            'description': f'Evento creado automáticamente al completar alerta: {alert.description}',
        }
        
        if scope == Scope.INDIVIDUAL and alert.animal_id:
            event_data['animal_id'] = alert.animal_id
        elif scope == Scope.GROUP and alert.corral_id:
            event_data['corral_id'] = alert.corral_id
        
        # Agregar el tipo de evento específico según la especie
        if alert.animal_type == AnimalType.COW:
            event_data['cow_event'] = event_type.value
        elif alert.animal_type == AnimalType.RABBIT:
            event_data['rabbit_event'] = event_type.value
        elif alert.animal_type == AnimalType.SHEEP:
            event_data['sheep_event'] = event_type.value
        
        # Verificar si ya existe un evento reciente del mismo tipo para evitar duplicados
        # (últimos 7 días)
        event_repo = EventRepository(Event, db)
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        existing_event_query = db.query(Event).filter(
            Event.animal_type == alert.animal_type,
            Event.date >= recent_date
        )
        
        if alert.animal_id:
            existing_event_query = existing_event_query.filter(Event.animal_id == alert.animal_id)
        elif alert.corral_id:
            existing_event_query = existing_event_query.filter(Event.corral_id == alert.corral_id)
        
        # Filtrar por tipo de evento específico
        if alert.animal_type == AnimalType.COW:
            existing_event_query = existing_event_query.filter(Event.cow_event == event_type)
        elif alert.animal_type == AnimalType.RABBIT:
            existing_event_query = existing_event_query.filter(Event.rabbit_event == event_type)
        elif alert.animal_type == AnimalType.SHEEP:
            existing_event_query = existing_event_query.filter(Event.sheep_event == event_type)
        
        existing_event = existing_event_query.first()
        if existing_event:
            # Ya existe un evento reciente, usar ese
            return existing_event
        
        # Crear el evento usando EventService
        try:
            event_service = EventService()
            response_data, status_code = event_service.create_event(event_data)
            
            if status_code == 201:
                # Obtener el evento creado desde la respuesta
                # La respuesta tiene formato: {'data': {...}, 'message': '...'}
                event_data_response = response_data.get('data') if isinstance(response_data, dict) else response_data
                if isinstance(event_data_response, dict):
                    event_id = event_data_response.get('id')
                else:
                    event_id = event_data_response.id if hasattr(event_data_response, 'id') else None
                
                if event_id:
                    # El ID del evento es un entero
                    event = db.query(Event).filter(Event.id == int(event_id)).first()
                    return event
        except Exception as e:
            # Si falla la creación del evento, no fallar la completación de la alerta
            # Solo registrar el error
            from app.utils.logger import Logger
            Logger.error(f"Error creating event from alert: {e}", exc_info=e)
        
        return None
    
    def decline_alert(self, alert_id: int, reason: str) -> tuple:
        """
        Decline an alert with a reason
        
        Args:
            alert_id: Alert ID to decline
            reason: Reason for declining the alert
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            if not reason or not reason.strip():
                return error_response("Reason is required for declining an alert", 400)
            
            with get_db_session() as db:
                repo = AlertRepository(Alert, db)
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                
                if not alert:
                    return not_found_response("Alert")
                
                if alert.status == AlertStatus.DONE:
                    return error_response("Cannot decline a completed alert", 400)
                
                # Mark as expired (declined)
                alert.status = AlertStatus.EXPIRED
                alert.declined_reason = reason.strip()
                alert.resolved_at = datetime.utcnow()
                db.commit()
                
                return success_response(self._serialize(alert), "Alert declined successfully")
        except Exception as e:
            return error_response(str(e), 500)

    def _serialize(self, a: Alert) -> Dict[str, Any]:
        import json
        rabbit_ids = None
        if hasattr(a, 'rabbit_ids') and a.rabbit_ids:
            try:
                rabbit_ids = json.loads(a.rabbit_ids)
            except (json.JSONDecodeError, TypeError):
                rabbit_ids = None
        
        return {
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'init_date': a.init_date.isoformat() if a.init_date else None,
            'max_date': a.max_date.isoformat() if a.max_date else None,
            'status': a.status.name if a.status else None,
            'priority': a.priority.name if a.priority else None,
            'animal_type': a.animal_type.name if a.animal_type else None,
            'animal_id': a.animal_id,
            'corral_id': a.corral_id,
            'event_id': a.event_id,
            'declined_reason': getattr(a, 'declined_reason', None),
            'rabbit_ids': rabbit_ids,  # Lista de IDs de conejos para alertas agrupadas
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'updated_at': a.updated_at.isoformat() if a.updated_at else None,
        }
