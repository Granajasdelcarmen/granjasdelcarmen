"""
Generic Animal Repository - Unified repository for all animal types
Uses the unified Animal model with species filtering
"""
from typing import List, Optional, Literal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import Animal, Gender, AnimalType


class AnimalRepository(BaseRepository[Animal]):
    """
    Generic animal repository with operations for all animal types
    Filters Animal table by species parameter
    """
    
    def __init__(self, model: Animal, db_session: Session):
        super().__init__(model, db_session)
    
    def _filter_by_species(self, query, species: AnimalType):
        """Helper to filter by species"""
        return query.filter(Animal.species == species)
    
    def get_all_by_species(
        self, 
        species: AnimalType,
        limit: Optional[int] = None, 
        offset: Optional[int] = None, 
        discarded: Optional[bool] = False
    ) -> List[Animal]:
        """
        Get all animals of a specific species with eager loading of parent relationships
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            limit: Maximum number of records to return
            offset: Number of records to skip
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of animal instances with parent relationships loaded
        """
        query = self._filter_by_species(
            self.db.query(Animal)
            .options(
                joinedload(Animal.mother),
                joinedload(Animal.father)
            ),
            species
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_all_sorted_by_species(
        self, 
        species: AnimalType,
        sort_by: Literal["asc", "desc"] = "asc", 
        discarded: Optional[bool] = False
    ) -> List[Animal]:
        """
        Get all animals of a specific species sorted by birth date with eager loading of parent relationships
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of animal instances sorted by birth date with parent relationships loaded
        """
        query = self._filter_by_species(
            self.db.query(Animal)
            .options(
                joinedload(Animal.mother),
                joinedload(Animal.father)
            ),
            species
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def get_by_gender_and_species(
        self, 
        species: AnimalType,
        gender: Gender, 
        discarded: Optional[bool] = False
    ) -> List[Animal]:
        """
        Get animals by gender and species with eager loading of parent relationships
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            gender: Animal gender
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of animal instances with the specified gender and species with parent relationships loaded
        """
        query = self._filter_by_species(
            self.db.query(Animal)
            .filter(Animal.gender == gender)
            .options(
                joinedload(Animal.mother),
                joinedload(Animal.father)
            ),
            species
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        return query.all()
    
    def get_by_gender_and_species_sorted(
        self, 
        species: AnimalType,
        gender: Gender, 
        sort_by: Literal["asc", "desc"] = "asc", 
        discarded: Optional[bool] = False
    ) -> List[Animal]:
        """
        Get animals by gender and species sorted by birth date with eager loading of parent relationships
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            gender: Animal gender
            sort_by: Sort order - "asc" for ascending, "desc" for descending
            discarded: Filter by discarded status (False = active, True = discarded, None = all)
            
        Returns:
            List of animal instances with the specified gender and species sorted by birth date with parent relationships loaded
        """
        query = self._filter_by_species(
            self.db.query(Animal)
            .filter(Animal.gender == gender)
            .options(
                joinedload(Animal.mother),
                joinedload(Animal.father)
            ),
            species
        )
        
        # Filter by discarded status if specified
        if discarded is not None:
            query = query.filter(Animal.discarded == discarded)
        
        if sort_by == "desc":
            return query.order_by(desc(Animal.birth_date)).all()
        else:
            return query.order_by(asc(Animal.birth_date)).all()
    
    def discard_animal(self, species: AnimalType, animal_id: str, reason: str) -> bool:
        """
        Mark an animal as discarded (sold)
        
        Args:
            species: Animal species to validate
            animal_id: Animal ID to discard
            reason: Reason for discarding (e.g., "Vendido")
            
        Returns:
            True if discarded, False if not found or wrong species
        """
        animal = self.get_by_id(animal_id)
        if not animal or animal.species != species:
            return False
        
        animal.discarded = True
        animal.discarded_reason = reason
        self.db.commit()
        return True
    
    def create_with_species(self, species: AnimalType, **kwargs) -> Animal:
        """
        Create a new animal with specified species
        
        Args:
            species: Animal species (RABBIT, COW, SHEEP, CHICKEN, etc.)
            **kwargs: Animal attributes
            
        Returns:
            Created animal instance
        """
        kwargs['species'] = species
        return super().create(**kwargs)
    
    def get_by_id(self, id: str, load_parents: bool = False) -> Optional[Animal]:
        """
        Get record by ID with optional eager loading of parent relationships
        
        Args:
            id: Record ID
            load_parents: Whether to eager load parent relationships (default: False)
            
        Returns:
            Model instance or None if not found
        """
        query = self.db.query(Animal).filter(Animal.id == id)
        if load_parents:
            query = query.options(
                joinedload(Animal.mother),
                joinedload(Animal.father)
            )
        return query.first()
    
    def list_by_species(self, species: AnimalType) -> List[Animal]:
        """Legacy method - use get_all_by_species instead"""
        return self.get_all_by_species(species)
