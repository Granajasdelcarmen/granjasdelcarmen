from typing import List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import Animal, AnimalType


class AnimalRepository(BaseRepository[Animal]):
    def __init__(self, model: Animal, db_session: Session):
        super().__init__(model, db_session)

    def list_by_species(self, species: AnimalType) -> List[Animal]:
        return self.query().filter(Animal.species == species).all()
