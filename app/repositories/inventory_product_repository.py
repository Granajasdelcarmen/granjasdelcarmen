"""
Inventory Product repository with specific operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import InventoryProduct, InventoryStatus, InventoryProductType


class InventoryProductRepository(BaseRepository[InventoryProduct]):
    """
    Repository for inventory products with specific operations
    """
    
    def get_by_status(self, status: InventoryStatus) -> List[InventoryProduct]:
        """Get all products by status"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.status == status
        ).all()
    
    def get_available_products(self) -> List[InventoryProduct]:
        """Get all available products (not sold, expired, or discarded)"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.status == InventoryStatus.AVAILABLE
        ).all()
    
    def get_by_product_type(self, product_type: InventoryProductType) -> List[InventoryProduct]:
        """Get all products of a specific type"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.product_type == product_type
        ).all()
    
    def get_by_animal_id(self, animal_id: str) -> List[InventoryProduct]:
        """Get all products related to a specific animal"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.animal_id == animal_id
        ).all()
    
    def get_expired_products(self) -> List[InventoryProduct]:
        """Get all expired products"""
        from datetime import datetime
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.expiration_date < datetime.utcnow(),
            InventoryProduct.status != InventoryStatus.EXPIRED,
            InventoryProduct.status != InventoryStatus.SOLD
        ).all()
    
    def get_by_location(self, location: str) -> List[InventoryProduct]:
        """Get all products in a specific location"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.location == location
        ).all()
    
    def search_products(self, search_term: str) -> List[InventoryProduct]:
        """Search products by name (case insensitive)"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.product_name.ilike(f'%{search_term}%')
        ).all()
    
    def get_low_stock_products(self, threshold: float = 0.0) -> List[InventoryProduct]:
        """Get products with quantity below threshold"""
        return self.db.query(InventoryProduct).filter(
            InventoryProduct.quantity <= threshold,
            InventoryProduct.status == InventoryStatus.AVAILABLE
        ).all()

