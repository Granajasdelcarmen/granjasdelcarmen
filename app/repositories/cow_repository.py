"""
Cow repository with specific cow operations
Uses the unified Animal model filtered by species=COW
"""
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import Animal, Gender, AnimalType

class CowRepository(BaseRepository[Animal]):
    """
    Cow repository with cow-specific operations
    Filters Animal table by species=COW
    """
    
    def __init__(self, model: Animal, db_session: Session):
        super().__init__(model, db_session)
        self.species = AnimalType.COW
    
    def _filter_by_species(self, query):
        """Helper to filter by COW species"""
        return query.filter(Animal.species == AnimalType.COW)
    
    def get_by_gender(self, gender: Gender) -> List[Animal]:
        """
        Get cows by gender
        
        Args:
            gender: Cow gender
            
        Returns:
            List of cow instances with the specified gender
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.gender == gender)
        ).all()
    
    def get_active_cows(self) -> List[Animal]:
        """
        Get all non-discarded cows
        
        Returns:
            List of active cow instances
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.discarded == False)
        ).all()
    
    def get_discarded_cows(self) -> List[Animal]:
        """
        Get all discarded cows
        
        Returns:
            List of discarded cow instances
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.discarded == True)
        ).all()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Animal]:
        """
        Get all cows
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of cow instances
        """
        query = self._filter_by_species(self.db.query(Animal))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_all_sorted(self, sort_by: Literal["asc", "desc"] = "asc") -> List[Animal]:
        """
        Get all cows sorted by birth date
        
        Args:
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            
        Returns:
            List of cow instances sorted by birth date
        """
        query = self._filter_by_species(self.db.query(Animal))
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def get_by_gender_sorted(self, gender: Gender, sort_by: Literal["asc", "desc"] = "asc") -> List[Animal]:
        """
        Get cows by gender sorted by birth date
        
        Args:
            gender: Cow gender
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            
        Returns:
            List of cow instances with the specified gender sorted by birth date
        """
        query = self._filter_by_species(
            self.db.query(Animal).filter(Animal.gender == gender)
        )
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def create(self, **kwargs) -> Animal:
        """
        Create a new cow (ensures species=COW)
        
        Args:
            **kwargs: Animal attributes
            
        Returns:
            Created animal instance
        """
        kwargs['species'] = AnimalType.COW
        return super().create(**kwargs)

