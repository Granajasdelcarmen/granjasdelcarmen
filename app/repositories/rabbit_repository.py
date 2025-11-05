"""
Rabbit repository with specific rabbit operations
Uses the unified Animal model filtered by species=RABBIT
"""
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import Animal, Gender, AnimalType

class RabbitRepository(BaseRepository[Animal]):
    """
    Rabbit repository with rabbit-specific operations
    Filters Animal table by species=RABBIT
    """
    
    def __init__(self, model: Animal, db_session: Session):
        super().__init__(model, db_session)
        self.species = AnimalType.RABBIT
    
    def _filter_by_species(self, query):
        """Helper to filter by RABBIT species"""
        return query.filter(Animal.species == AnimalType.RABBIT)
    
    def get_by_gender(self, gender: Gender) -> List[Animal]:
        """
        Get rabbits by gender
        
        Args:
            gender: Rabbit gender
            
        Returns:
            List of rabbit instances with the specified gender
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.gender == gender)
        ).all()
    
    def get_active_rabbits(self) -> List[Animal]:
        """
        Get all non-discarded rabbits
        
        Returns:
            List of active rabbit instances
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.discarded == False)
        ).all()
    
    def get_discarded_rabbits(self) -> List[Animal]:
        """
        Get all discarded rabbits
        
        Returns:
            List of discarded rabbit instances
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.discarded == True)
        ).all()
    
    def get_by_user(self, user_id: str) -> List[Animal]:
        """
        Get rabbits by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            List of rabbit instances owned by the user
        """
        return self._filter_by_species(
            self.db.query(Animal).filter(Animal.user_id == user_id)
        ).all()
    
    def discard_rabbit(self, rabbit_id: str, reason: str) -> bool:
        """
        Mark a rabbit as discarded (sold)
        
        Args:
            rabbit_id: Rabbit ID to discard
            reason: Reason for discarding (e.g., "Vendido")
            
        Returns:
            True if discarded, False if not found
        """
        rabbit = self.get_by_id(rabbit_id)
        if not rabbit or rabbit.species != AnimalType.RABBIT:
            return False
        
        rabbit.discarded = True
        rabbit.discarded_reason = reason
        self.db.commit()
        return True
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None, discarded: Optional[bool] = False) -> List[Animal]:
        """
        Get all rabbits
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of rabbit instances
        """
        query = self._filter_by_species(self.db.query(Animal))
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_all_sorted(self, sort_by: Literal["asc", "desc"] = "asc", discarded: Optional[bool] = False) -> List[Animal]:
        """
        Get all rabbits sorted by birth date
        
        Args:
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of rabbit instances sorted by birth date
        """
        query = self._filter_by_species(self.db.query(Animal))
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def get_by_gender(self, gender: Gender, discarded: Optional[bool] = False) -> List[Animal]:
        """
        Get rabbits by gender
        
        Args:
            gender: Rabbit gender
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of rabbit instances with the specified gender
        """
        query = self._filter_by_species(
            self.db.query(Animal).filter(Animal.gender == gender)
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        return query.all()
    
    def get_by_gender_sorted(self, gender: Gender, sort_by: Literal["asc", "desc"] = "asc", discarded: Optional[bool] = False) -> List[Animal]:
        """
        Get rabbits by gender sorted by birth date
        
        Args:
            gender: Rabbit gender
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of rabbit instances with the specified gender sorted by birth date
        """
        query = self._filter_by_species(
            self.db.query(Animal).filter(Animal.gender == gender)
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def create(self, **kwargs) -> Animal:
        """
        Create a new rabbit (ensures species=RABBIT)
        
        Args:
            **kwargs: Animal attributes
            
        Returns:
            Created animal instance
        """
        kwargs['species'] = AnimalType.RABBIT
        return super().create(**kwargs)
