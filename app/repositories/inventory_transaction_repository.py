"""
Inventory Transaction repository with specific operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import InventoryTransaction, InventoryTransactionType
from datetime import datetime, timedelta


class InventoryTransactionRepository(BaseRepository[InventoryTransaction]):
    """
    Repository for inventory transactions with specific operations
    """
    
    def get_by_product_id(self, product_id: str) -> List[InventoryTransaction]:
        """Get all transactions for a specific product"""
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.product_id == product_id
        ).order_by(InventoryTransaction.created_at.desc()).all()
    
    def get_by_transaction_type(self, transaction_type: InventoryTransactionType) -> List[InventoryTransaction]:
        """Get all transactions of a specific type"""
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.transaction_type == transaction_type
        ).order_by(InventoryTransaction.created_at.desc()).all()
    
    def get_by_user_id(self, user_id: str) -> List[InventoryTransaction]:
        """Get all transactions by a specific user"""
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.user_id == user_id
        ).order_by(InventoryTransaction.created_at.desc()).all()
    
    def get_recent_transactions(self, days: int = 30) -> List[InventoryTransaction]:
        """Get transactions from the last N days"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.created_at >= since_date
        ).order_by(InventoryTransaction.created_at.desc()).all()
    
    def get_by_sale_id(self, sale_id: str) -> List[InventoryTransaction]:
        """Get all transactions related to a sale"""
        return self.db.query(InventoryTransaction).filter(
            InventoryTransaction.sale_id == sale_id
        ).all()

