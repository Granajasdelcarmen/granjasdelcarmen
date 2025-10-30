from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import Event, AnimalType, Scope


class EventRepository(BaseRepository[Event]):
    def __init__(self, model: Event, db_session: Session):
        super().__init__(model, db_session)

    def filter(
        self,
        *,
        species: Optional[AnimalType] = None,
        scope: Optional[Scope] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        animal_id: Optional[str] = None,
        corral_id: Optional[str] = None,
    ) -> List[Event]:
        query = self.query()

        if species:
            query = query.filter(Event.animal_type == species)
        if scope:
            query = query.filter(Event.scope == scope)
        if from_date:
            query = query.filter(Event.date >= from_date)
        if to_date:
            query = query.filter(Event.date <= to_date)
        if animal_id:
            query = query.filter(Event.animal_id == animal_id)
        if corral_id:
            query = query.filter(Event.corral_id == corral_id)

        return query.order_by(Event.date.desc()).all()
