from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.repositories.event_repository import EventRepository
from app.repositories.alert_repository import AlertRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required_fields
from models import (
    Event,
    Alert,
    Animal,
    AnimalType,
    Scope,
    RabbitEventType,
    ChickenEventType,
    CowEventType,
    SheepEventType,
    AlertStatus,
    AlertPriority,
)


class EventService:
    def create_event(self, data: Dict[str, Any]) -> tuple:
        try:
            validate_required_fields(data, ['scope'])

            scope = Scope(data['scope']) if isinstance(data['scope'], str) else data['scope']
            species = data.get('animal_type')
            date = data.get('date')

            event_date = datetime.fromisoformat(date) if isinstance(date, str) else (date or datetime.utcnow())

            with get_db_session() as db:
                event_repo = EventRepository(Event, db)
                alert_repo = AlertRepository(Alert, db)

                payload = {
                    'scope': scope,
                    'animal_type': AnimalType(species) if isinstance(species, str) and species else None,
                    'date': event_date,
                    'description': data.get('description'),
                    'name': data.get('name'),
                }

                if scope == Scope.INDIVIDUAL:
                    validate_required_fields(data, ['animal_id'])
                    payload['animal_id'] = data['animal_id']
                if scope == Scope.GROUP:
                    validate_required_fields(data, ['corral_id'])
                    payload['corral_id'] = data['corral_id']

                if species == 'RABBIT':
                    if scope == Scope.GROUP and data.get('rabbit_event') != 'VITAMINS_CORRAL':
                        return error_response('RABBIT group events only allowed for VITAMINS_CORRAL', 400)
                    if 'rabbit_event' in data:
                        payload['rabbit_event'] = RabbitEventType(data['rabbit_event']) if isinstance(data['rabbit_event'], str) else data['rabbit_event']
                elif species == 'CHICKEN':
                    if scope != Scope.GROUP:
                        return error_response('CHICKEN events must be GROUP (corral)', 400)
                    if 'chicken_event' in data:
                        payload['chicken_event'] = ChickenEventType(data['chicken_event']) if isinstance(data['chicken_event'], str) else data['chicken_event']
                elif species == 'COW':
                    if 'cow_event' in data:
                        payload['cow_event'] = CowEventType(data['cow_event']) if isinstance(data['cow_event'], str) else data['cow_event']
                elif species == 'SHEEP':
                    if 'sheep_event' in data:
                        payload['sheep_event'] = SheepEventType(data['sheep_event']) if isinstance(data['sheep_event'], str) else data['sheep_event']

                event = event_repo.create(**payload)

                # Manejar alertas automáticas según el tipo de evento
                if species == 'COW':
                    ev = payload.get('cow_event')
                    animal_id = payload.get('animal_id')
                    
                    if ev and animal_id:
                        from app.services.cow_alert_service import CowAlertService
                        cow_alert_service = CowAlertService()
                        
                        # Si es evento de preñez, crear alertas de gestación
                        if str(ev) in ('CowEventType.PREGNANCY', 'PREGNANCY'):
                            cow_alert_service.create_pregnancy_alerts(animal_id, event_date)
                        
                        # Si es evento de desparasitación, crear alerta para próxima desparasitación (cada 3 meses)
                        elif str(ev) in ('CowEventType.DEWORMING', 'DEWORMING'):
                            cow_alert_service.create_periodic_deworming_alert(animal_id, event_date)
                
                elif species == 'RABBIT':
                    ev = payload.get('rabbit_event')
                    animal_id = payload.get('animal_id')
                    
                    if ev and animal_id:
                        from app.services.rabbit_alert_service import RabbitAlertService
                        rabbit_alert_service = RabbitAlertService()
                        
                        # Si es evento de preñez, crear alertas de gestación
                        if str(ev) in ('RabbitEventType.PREGNANCY', 'PREGNANCY'):
                            rabbit_alert_service.create_pregnancy_alerts(animal_id, event_date)
                
                elif species == 'SHEEP':
                    # Mantener lógica antigua para ovejas (180 días)
                    ev = payload.get('sheep_event')
                    if str(ev) in ('SheepEventType.DEWORMING', 'DEWORMING') or ev in ('DEWORMING',):
                        init = event_date + timedelta(days=180 - 7)
                        maxd = event_date + timedelta(days=180 + 7)
                        
                        # Obtener nombre del animal si es individual
                        animal_name = ""
                        if payload.get('animal_id'):
                            from app.repositories.animal_repository import AnimalRepository
                            animal_repo = AnimalRepository(Animal, db)
                            animal = animal_repo.get_by_id(payload.get('animal_id'))
                            if animal:
                                animal_name = f' "{animal.name}"'
                        
                        alert_repo.create(
                            name='DEWORMING_REMINDER',
                            description=f'Desparasitación pendiente para oveja{animal_name}',
                            init_date=init,
                            max_date=maxd,
                            status=AlertStatus.PENDING,
                            priority=AlertPriority.MEDIUM,
                            animal_type=payload.get('animal_type'),
                            animal_id=payload.get('animal_id'),
                            corral_id=payload.get('corral_id'),
                            event_id=event.id,
                        )

                return success_response(self._serialize_event(event), 'Event created', 201)

        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)

    def list_events(self, params: Dict[str, Any]) -> tuple:
        try:
            with get_db_session() as db:
                repo = EventRepository(Event, db)
                events = repo.filter(
                    species=AnimalType(params['species']) if params.get('species') else None,
                    scope=Scope(params['scope']) if params.get('scope') else None,
                    from_date=params.get('from'),
                    to_date=params.get('to'),
                    animal_id=params.get('animal_id'),
                    corral_id=params.get('corral_id'),
                )
                return success_response([self._serialize_event(e) for e in events])
        except Exception as e:
            return error_response(str(e), 500)

    def _serialize_event(self, e: Event) -> Dict[str, Any]:
        return {
            'id': e.id,
            'name': e.name.name if e.name else None,
            'description': e.description,
            'date': e.date.isoformat() if e.date else None,
            'scope': e.scope.name if e.scope else None,
            'animal_type': e.animal_type.name if e.animal_type else None,
            'animal_id': e.animal_id,
            'corral_id': e.corral_id,
            'rabbit_event': e.rabbit_event.name if e.rabbit_event else None,
            'chicken_event': e.chicken_event.name if e.chicken_event else None,
            'cow_event': e.cow_event.name if e.cow_event else None,
            'sheep_event': e.sheep_event.name if e.sheep_event else None,
            'created_at': e.created_at.isoformat() if e.created_at else None,
            'updated_at': e.updated_at.isoformat() if e.updated_at else None,
        }
