"""
Expense service with business logic for expenses
"""
from typing import List, Dict, Any, Optional
from app.repositories.expense_repository import ExpenseRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response, not_found_response
from models import Expense, ExpenseCategory

class ExpenseService:
    """
    Expense service handling expense business logic
    """
    
    def get_all_expenses(self, sort_by: Optional[str] = None) -> tuple:
        """
        Get all expenses
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by expense_date)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ExpenseRepository(Expense, db)
                expenses = repo.get_all_sorted(sort_by)
                
                return success_response(
                    [self._serialize_expense(expense) for expense in expenses],
                    "Expenses retrieved successfully"
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_expense_by_id(self, expense_id: str) -> tuple:
        """
        Get expense by ID
        
        Args:
            expense_id: Expense ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ExpenseRepository(Expense, db)
                expense = repo.get_by_id(expense_id)
                
                if not expense:
                    return not_found_response("Expense")
                
                return success_response(self._serialize_expense(expense), "Expense retrieved successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_expense(self, expense_data: Dict[str, Any], user_id: str) -> tuple:
        """
        Create a new expense (admin only)
        
        Args:
            expense_data: Expense data dictionary
            user_id: User ID who is creating the expense
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            required_fields = ['category', 'description', 'amount', 'expense_date']
            for field in required_fields:
                if field not in expense_data:
                    return error_response(f"{field} is required", 400)
            
            # Validate category
            category_str = expense_data['category'].lower()
            category_mapping = {
                'alimentacion': ExpenseCategory.ALIMENTACION,
                'medicamentos': ExpenseCategory.MEDICAMENTOS,
                'mantenimiento': ExpenseCategory.MANTENIMIENTO,
                'personal': ExpenseCategory.PERSONAL,
                'servicios': ExpenseCategory.SERVICIOS,
                'equipos': ExpenseCategory.EQUIPOS,
                'otros': ExpenseCategory.OTROS
            }
            
            if category_str not in category_mapping:
                return error_response(f"Invalid category: {expense_data['category']}. Valid categories are: alimentacion, medicamentos, mantenimiento, personal, servicios, equipos, otros", 400)
            
            # Validate amount
            amount = float(expense_data['amount'])
            if amount <= 0:
                return error_response("amount must be greater than 0", 400)
            
            with get_db_session() as db:
                repo = ExpenseRepository(Expense, db)
                
                # Create expense
                expense = repo.create(
                    category=category_mapping[category_str],
                    description=expense_data['description'],
                    amount=amount,
                    expense_date=expense_data['expense_date'],
                    vendor=expense_data.get('vendor'),
                    notes=expense_data.get('notes'),
                    created_by=user_id
                )
                
                return success_response(self._serialize_expense(expense), "Expense created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_expense(self, expense_id: str, expense_data: Dict[str, Any]) -> tuple:
        """
        Update expense (admin only)
        
        Args:
            expense_id: Expense ID
            expense_data: Updated expense data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ExpenseRepository(Expense, db)
                
                # Check if expense exists
                expense = repo.get_by_id(expense_id)
                if not expense:
                    return not_found_response("Expense")
                
                # Update fields if provided
                update_data = {}
                
                if 'category' in expense_data:
                    category_str = expense_data['category'].lower()
                    category_mapping = {
                        'alimentacion': ExpenseCategory.ALIMENTACION,
                        'medicamentos': ExpenseCategory.MEDICAMENTOS,
                        'mantenimiento': ExpenseCategory.MANTENIMIENTO,
                        'personal': ExpenseCategory.PERSONAL,
                        'servicios': ExpenseCategory.SERVICIOS,
                        'equipos': ExpenseCategory.EQUIPOS,
                        'otros': ExpenseCategory.OTROS
                    }
                    if category_str not in category_mapping:
                        return error_response(f"Invalid category: {expense_data['category']}", 400)
                    update_data['category'] = category_mapping[category_str]
                
                if 'description' in expense_data:
                    update_data['description'] = expense_data['description']
                
                if 'amount' in expense_data:
                    amount = float(expense_data['amount'])
                    if amount <= 0:
                        return error_response("amount must be greater than 0", 400)
                    update_data['amount'] = amount
                
                if 'expense_date' in expense_data:
                    update_data['expense_date'] = expense_data['expense_date']
                
                if 'vendor' in expense_data:
                    update_data['vendor'] = expense_data['vendor']
                
                if 'notes' in expense_data:
                    update_data['notes'] = expense_data['notes']
                
                # Update expense
                updated_expense = repo.update(expense_id, **update_data)
                
                return success_response(self._serialize_expense(updated_expense), "Expense updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_expense(self, expense_id: str) -> tuple:
        """
        Delete expense (admin only)
        
        Args:
            expense_id: Expense ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ExpenseRepository(Expense, db)
                
                # Check if expense exists
                if not repo.exists(expense_id):
                    return not_found_response("Expense")
                
                # Delete expense
                repo.delete(expense_id)
                
                return success_response(None, "Expense deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_expense(self, expense: Expense) -> Dict[str, Any]:
        """
        Serialize expense model to dictionary
        
        Args:
            expense: Expense instance
            
        Returns:
            Dictionary representation of expense
        """
        return {
            'id': expense.id,
            'category': expense.category.value if expense.category else None,
            'description': expense.description,
            'amount': expense.amount,
            'expense_date': expense.expense_date.isoformat() if expense.expense_date else None,
            'vendor': expense.vendor,
            'notes': expense.notes,
            'created_by': expense.created_by,
            'created_at': expense.created_at.isoformat() if expense.created_at else None,
            'updated_at': expense.updated_at.isoformat() if expense.updated_at else None
        }

