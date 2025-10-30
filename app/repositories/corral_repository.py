from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import Corral


class CorralRepository(BaseRepository[Corral]):
    def __init__(self, model: Corral, db_session: Session):
        super().__init__(model, db_session)

    def get_by_name(self, name: str) -> Optional[Corral]:
        return self.query().filter(Corral.name == name).first()
