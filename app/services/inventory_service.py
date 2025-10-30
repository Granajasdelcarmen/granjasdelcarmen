"""
Inventory service with business logic
"""
from typing import List, Dict, Any, Optional
from app.repositories.inventory_repository import InventoryRepository
from app.utils.database import get_db_session
from app.utils.validators import validate_required_fields, validate_positive_integer
from app.utils.response import success_response, error_response, not_found_response
from models import Inventory
import uuid

class InventoryService:
    """
    Inventory service handling inventory business logic
    """
    
    def get_all_items(self) -> tuple:
        """
        Get all inventory items
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            print("get_all_items")
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                items = repo.get_all()
                
                items_data = []
                for item in items:
                    items_data.append(self._serialize_item(item))
                
                return success_response(items_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_item_by_id(self, item_id: str) -> tuple:
        """
        Get inventory item by ID
        
        Args:
            item_id: Item ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                item = repo.get_by_id(item_id)
                
                if not item:
                    return not_found_response("Inventory item")
                
                return success_response(self._serialize_item(item))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_item(self, item_data: Dict[str, Any]) -> tuple:
        """
        Create a new inventory item
        
        Args:
            item_data: Item data dictionary
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            validate_required_fields(item_data, ['item', 'quantity'])
            
            # Validate quantity is positive
            validate_positive_integer(item_data['quantity'], 'quantity')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                # Check if item already exists
                existing_item = repo.get_by_item(item_data['item'])
                if existing_item:
                    return error_response("Item with this name already exists", 409)
                
                # Create item
                item_data['id'] = str(uuid.uuid4())
                item = repo.create(**item_data)
                
                return success_response(self._serialize_item(item), "Inventory item created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_item(self, item_id: str, item_data: Dict[str, Any]) -> tuple:
        """
        Update inventory item
        
        Args:
            item_id: Item ID
            item_data: Updated item data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate quantity if provided
            if 'quantity' in item_data:
                validate_positive_integer(item_data['quantity'], 'quantity')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                # Check if item exists
                if not repo.exists(item_id):
                    return not_found_response("Inventory item")
                
                # Update item
                updated_item = repo.update(item_id, **item_data)
                
                return success_response(self._serialize_item(updated_item), "Inventory item updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_item(self, item_id: str) -> tuple:
        """
        Delete inventory item
        
        Args:
            item_id: Item ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                if not repo.exists(item_id):
                    return not_found_response("Inventory item")
                
                repo.delete(item_id)
                return success_response(None, "Inventory item deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def search_items(self, search_term: str) -> tuple:
        """
        Search inventory items by name
        
        Args:
            search_term: Search term
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            if not search_term or len(search_term.strip()) < 2:
                return error_response("Search term must be at least 2 characters long", 400)
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                items = repo.search_items(search_term.strip())
                
                items_data = []
                for item in items:
                    items_data.append(self._serialize_item(item))
                
                return success_response(items_data)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_low_stock_items(self, threshold: int = 10) -> tuple:
        """
        Get items with low stock
        
        Args:
            threshold: Minimum quantity threshold
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_positive_integer(threshold, 'threshold')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                items = repo.get_low_stock_items(threshold)
                
                items_data = []
                for item in items:
                    items_data.append(self._serialize_item(item))
                
                return success_response(items_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_high_stock_items(self, threshold: int = 100) -> tuple:
        """
        Get items with high stock
        
        Args:
            threshold: Maximum quantity threshold
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_positive_integer(threshold, 'threshold')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                items = repo.get_high_stock_items(threshold)
                
                items_data = []
                for item in items:
                    items_data.append(self._serialize_item(item))
                
                return success_response(items_data)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_quantity(self, item_id: str, new_quantity: int) -> tuple:
        """
        Update item quantity
        
        Args:
            item_id: Item ID
            new_quantity: New quantity value
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_positive_integer(new_quantity, 'quantity')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                if not repo.exists(item_id):
                    return not_found_response("Inventory item")
                
                success = repo.update_quantity(item_id, new_quantity)
                if not success:
                    return error_response("Failed to update quantity", 500)
                
                # Get updated item
                updated_item = repo.get_by_id(item_id)
                return success_response(self._serialize_item(updated_item), "Quantity updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def add_quantity(self, item_id: str, amount: int) -> tuple:
        """
        Add quantity to existing item
        
        Args:
            item_id: Item ID
            amount: Amount to add
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_positive_integer(amount, 'amount')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                if not repo.exists(item_id):
                    return not_found_response("Inventory item")
                
                success = repo.add_quantity(item_id, amount)
                if not success:
                    return error_response("Failed to add quantity", 500)
                
                # Get updated item
                updated_item = repo.get_by_id(item_id)
                return success_response(self._serialize_item(updated_item), "Quantity added successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def subtract_quantity(self, item_id: str, amount: int) -> tuple:
        """
        Subtract quantity from existing item
        
        Args:
            item_id: Item ID
            amount: Amount to subtract
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            validate_positive_integer(amount, 'amount')
            
            with get_db_session() as db:
                repo = InventoryRepository(Inventory, db)
                
                if not repo.exists(item_id):
                    return not_found_response("Inventory item")
                
                success = repo.subtract_quantity(item_id, amount)
                if not success:
                    return error_response("Insufficient stock or item not found", 400)
                
                # Get updated item
                updated_item = repo.get_by_id(item_id)
                return success_response(self._serialize_item(updated_item), "Quantity subtracted successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def seed_test_items(self) -> tuple:
        """
        Create test inventory items for development
        
        Returns:
            Tuple of (response_data, status_code)
        """
        test_items = [
            {
                'item': 'Rabbit Feed - Premium',
                'quantity': 50
            },
            {
                'item': 'Rabbit Feed - Standard',
                'quantity': 25
            },
            {
                'item': 'Water Bottles',
                'quantity': 100
            },
            {
                'item': 'Cages - Small',
                'quantity': 15
            },
            {
                'item': 'Cages - Large',
                'quantity': 8
            },
            {
                'item': 'Hay Bales',
                'quantity': 30
            },
            {
                'item': 'Vaccines - Rabbit',
                'quantity': 5
            },
            {
                'item': 'Cleaning Supplies',
                'quantity': 20
            }
        ]
        
        created_items = []
        for item_data in test_items:
            response, status = self.create_item(item_data)
            if status == 201:
                created_items.append(response.get('data'))
        
        return success_response(created_items, f"Created {len(created_items)} test inventory items")
    
    def _serialize_item(self, item: Inventory) -> Dict[str, Any]:
        """
        Serialize inventory item model to dictionary
        
        Args:
            item: Inventory model instance
            
        Returns:
            Serialized item data
        """
        return {
            'id': item.id,
            'item': item.item,
            'quantity': item.quantity,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None
        }
