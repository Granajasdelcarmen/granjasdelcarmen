"""
Rabbit repository with specific rabbit operations
"""
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import Rabbit, Gender

class RabbitRepository(BaseRepository[Rabbit]):
    """
    Rabbit repository with rabbit-specific operations
    """
    
    def get_by_gender(self, gender: Gender) -> List[Rabbit]:
        """
        Get rabbits by gender
        
        Args:
            gender: Rabbit gender
            
        Returns:
            List of rabbit instances with the specified gender
        """
        return self.db.query(Rabbit).filter(Rabbit.gender == gender).all()
    
    def get_active_rabbits(self) -> List[Rabbit]:
        """
        Get all non-discarded rabbits
        
        Returns:
            List of active rabbit instances
        """
        return self.db.query(Rabbit).filter(Rabbit.discarded == False).all()
    
    def get_discarded_rabbits(self) -> List[Rabbit]:
        """
        Get all discarded rabbits
        
        Returns:
            List of discarded rabbit instances
        """
        return self.db.query(Rabbit).filter(Rabbit.discarded == True).all()
    
    def get_by_user(self, user_id: str) -> List[Rabbit]:
        """
        Get rabbits by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            List of rabbit instances owned by the user
        """
        return self.db.query(Rabbit).filter(Rabbit.user_id == user_id).all()
    
    def discard_rabbit(self, rabbit_id: str, reason: str) -> bool:
        """
        Mark a rabbit as discarded
        
        Args:
            rabbit_id: Rabbit ID to discard
            reason: Reason for discarding
            
        Returns:
            True if discarded, False if not found
        """
        rabbit = self.get_by_id(rabbit_id)
        if not rabbit:
            return False
        
        rabbit.discarded = True
        rabbit.discarded_reason = reason
        self.db.commit()
        return True
    
    def get_all_sorted(self, sort_by: Literal["asc", "desc"] = "asc") -> List[Rabbit]:
        """
        Get all rabbits sorted by birth date
        
        Args:
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            
        Returns:
            List of rabbit instances sorted by birth date
        """
        query = self.db.query(Rabbit)
        
        if sort_by == "desc":
            return query.order_by(desc(Rabbit.birth_date)).all()
        else:
            return query.order_by(asc(Rabbit.birth_date)).all()
    
    def get_by_gender_sorted(self, gender: Gender, sort_by: Literal["asc", "desc"] = "asc") -> List[Rabbit]:
        """
        Get rabbits by gender sorted by birth date
        
        Args:
            gender: Rabbit gender
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            
        Returns:
            List of rabbit instances with the specified gender sorted by birth date
        """
        query = self.db.query(Rabbit).filter(Rabbit.gender == gender)
        
        if sort_by == "desc":
            return query.order_by(desc(Rabbit.birth_date)).all()
        else:
            return query.order_by(asc(Rabbit.birth_date)).all()
