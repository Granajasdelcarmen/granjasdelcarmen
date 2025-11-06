"""
Expense repository with specific expense operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import Expense, ExpenseCategory

class ExpenseRepository(BaseRepository[Expense]):
    """
    Expense repository with expense-specific operations
    """
    
    def get_all_sorted(self, sort_by: Optional[str] = None) -> List[Expense]:
        """
        Get all expenses with optional sorting
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by expense_date)
            
        Returns:
            List of expense instances
        """
        query = self.db.query(Expense)
        
        if sort_by == 'asc':
            query = query.order_by(asc(Expense.expense_date))
        elif sort_by == 'desc':
            query = query.order_by(desc(Expense.expense_date))
        
        return query.all()
    
    def get_by_category(self, category: ExpenseCategory) -> List[Expense]:
        """
        Get expenses by category
        
        Args:
            category: Expense category
            
        Returns:
            List of expense instances
        """
        return self.db.query(Expense).filter(Expense.category == category).all()
    
    def get_by_created_by(self, created_by: str) -> List[Expense]:
        """
        Get expenses by creator (user ID)
        
        Args:
            created_by: User ID who created the expense
            
        Returns:
            List of expense instances
        """
        return self.db.query(Expense).filter(Expense.created_by == created_by).all()

