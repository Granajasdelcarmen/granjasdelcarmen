"""
Animal Sale Repository - Generic repository for animal sales
Handles sales for all animal types
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import AnimalSale, AnimalType


class AnimalSaleRepository(BaseRepository[AnimalSale]):
    """
    Repository for animal sales operations
    """
    
    def __init__(self, model: AnimalSale, db_session: Session):
        super().__init__(model, db_session)
    
    def get_sales_by_animal_id(self, animal_id: str) -> List[AnimalSale]:
        """
        Get all sales for a specific animal
        
        Args:
            animal_id: Animal ID
            
        Returns:
            List of sale instances for the animal
        """
        return self.db.query(AnimalSale).filter(AnimalSale.animal_id == animal_id).all()
    
    def get_sales_by_species(self, species: AnimalType) -> List[AnimalSale]:
        """
        Get all sales for a specific animal species
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            
        Returns:
            List of sale instances for the species
        """
        return self.db.query(AnimalSale).filter(AnimalSale.animal_type == species).all()
    
    def get_sales_by_seller(self, sold_by: str) -> List[AnimalSale]:
        """
        Get all sales made by a specific user
        
        Args:
            sold_by: User ID who made the sale
            
        Returns:
            List of sale instances
        """
        return self.db.query(AnimalSale).filter(AnimalSale.sold_by == sold_by).all()
    
    def get_all_sorted(self, sort_by: Optional[str] = None) -> List[AnimalSale]:
        """
        Get all animal sales with optional sorting
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by created_at)
            
        Returns:
            List of sale instances
        """
        query = self.db.query(AnimalSale)
        
        if sort_by == 'asc':
            query = query.order_by(asc(AnimalSale.created_at))
        elif sort_by == 'desc':
            query = query.order_by(desc(AnimalSale.created_at))
        
        return query.all()

