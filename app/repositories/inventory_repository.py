"""
Inventory repository with specific inventory operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import Inventory

class InventoryRepository(BaseRepository[Inventory]):
    """
    Inventory repository with inventory-specific operations
    """
    
    def get_by_item(self, item: str) -> Optional[Inventory]:
        """
        Get inventory item by name
        
        Args:
            item: Item name
            
        Returns:
            Inventory instance or None if not found
        """
        return self.db.query(Inventory).filter(Inventory.item == item).first()
    
    def get_low_stock_items(self, threshold: int = 10) -> List[Inventory]:
        """
        Get items with low stock
        
        Args:
            threshold: Minimum quantity threshold
            
        Returns:
            List of inventory items with quantity below threshold
        """
        return self.db.query(Inventory).filter(Inventory.quantity <= threshold).all()
    
    def get_high_stock_items(self, threshold: int = 100) -> List[Inventory]:
        """
        Get items with high stock
        
        Args:
            threshold: Maximum quantity threshold
            
        Returns:
            List of inventory items with quantity above threshold
        """
        return self.db.query(Inventory).filter(Inventory.quantity >= threshold).all()
    
    def search_items(self, search_term: str) -> List[Inventory]:
        """
        Search inventory items by name (case insensitive)
        
        Args:
            search_term: Search term
            
        Returns:
            List of matching inventory items
        """
        return self.db.query(Inventory).filter(
            Inventory.item.ilike(f'%{search_term}%')
        ).all()
    
    def update_quantity(self, item_id: str, new_quantity: int) -> bool:
        """
        Update item quantity
        
        Args:
            item_id: Item ID
            new_quantity: New quantity value
            
        Returns:
            True if updated, False if not found
        """
        item = self.get_by_id(item_id)
        if not item:
            return False
        
        item.quantity = new_quantity
        self.db.commit()
        return True
    
    def add_quantity(self, item_id: str, amount: int) -> bool:
        """
        Add quantity to existing item
        
        Args:
            item_id: Item ID
            amount: Amount to add
            
        Returns:
            True if updated, False if not found
        """
        item = self.get_by_id(item_id)
        if not item:
            return False
        
        item.quantity += amount
        self.db.commit()
        return True
    
    def subtract_quantity(self, item_id: str, amount: int) -> bool:
        """
        Subtract quantity from existing item
        
        Args:
            item_id: Item ID
            amount: Amount to subtract
            
        Returns:
            True if updated, False if not found or insufficient stock
        """
        item = self.get_by_id(item_id)
        if not item or item.quantity < amount:
            return False
        
        item.quantity -= amount
        self.db.commit()
        return True
