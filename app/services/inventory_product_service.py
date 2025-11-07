"""
Inventory Product Service with business logic
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.repositories.inventory_product_repository import InventoryProductRepository
from app.repositories.inventory_transaction_repository import InventoryTransactionRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response, not_found_response
from models import (
    InventoryProduct, InventoryTransaction, InventoryProductType, 
    InventoryUnit, InventoryStatus, InventoryTransactionType
)


class InventoryProductService:
    """
    Service for managing inventory products with business logic
    """
    
    def list_products(
        self, 
        status: Optional[InventoryStatus] = None,
        product_type: Optional[InventoryProductType] = None,
        location: Optional[str] = None
    ) -> tuple:
        """List all inventory products with optional filters"""
        try:
            with get_db_session() as db:
                repo = InventoryProductRepository(InventoryProduct, db)
                
                if status:
                    products = repo.get_by_status(status)
                elif product_type:
                    products = repo.get_by_product_type(product_type)
                elif location:
                    products = repo.get_by_location(location)
                else:
                    products = repo.get_available_products()
                
                return success_response([self._serialize_product(p) for p in products])
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_product(self, product_id: str) -> tuple:
        """Get a single product by ID"""
        try:
            with get_db_session() as db:
                repo = InventoryProductRepository(InventoryProduct, db)
                product = repo.get_by_id(product_id)
                
                if not product:
                    return not_found_response("Product")
                
                return success_response(self._serialize_product(product))
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_product(self, product_data: Dict[str, Any], user_id: str) -> tuple:
        """
        Create a new inventory product
        
        Args:
            product_data: Product data dictionary
            user_id: ID of user creating the product
        """
        try:
            # Validate required fields
            required_fields = ['product_type', 'product_name', 'quantity', 'unit']
            for field in required_fields:
                if field not in product_data:
                    return error_response(f"Field '{field}' is required", 400)
            
            # Validate quantity
            if product_data['quantity'] <= 0:
                return error_response("Quantity must be greater than 0", 400)
            
            with get_db_session() as db:
                product_repo = InventoryProductRepository(InventoryProduct, db)
                transaction_repo = InventoryTransactionRepository(InventoryTransaction, db)
                
                # Create product
                product_data['created_by'] = user_id
                product_data['status'] = InventoryStatus.AVAILABLE
                if 'production_date' not in product_data:
                    product_data['production_date'] = datetime.utcnow()
                
                product = product_repo.create(**product_data)
                
                # Create initial transaction (ENTRY)
                transaction_repo.create(
                    product_id=product.id,
                    transaction_type=InventoryTransactionType.ENTRY,
                    quantity=product_data['quantity'],
                    reason=product_data.get('reason', 'Initial entry'),
                    user_id=user_id,
                    notes=product_data.get('notes')
                )
                
                return success_response(
                    self._serialize_product(product),
                    "Product created successfully",
                    201
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> tuple:
        """Update an inventory product"""
        try:
            with get_db_session() as db:
                repo = InventoryProductRepository(InventoryProduct, db)
                product = repo.get_by_id(product_id)
                
                if not product:
                    return not_found_response("Product")
                
                # Don't allow updating status directly (use specific methods)
                if 'status' in product_data:
                    product_data.pop('status')
                
                updated_product = repo.update(product_id, **product_data)
                return success_response(
                    self._serialize_product(updated_product),
                    "Product updated successfully"
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def mark_as_sold(self, product_id: str, quantity: float, user_id: str, sale_id: Optional[str] = None) -> tuple:
        """
        Mark product (or part of it) as sold
        
        Args:
            product_id: Product ID
            quantity: Quantity to mark as sold
            user_id: User ID performing the sale
            sale_id: Optional sale ID if linked to a sale record
        """
        try:
            with get_db_session() as db:
                product_repo = InventoryProductRepository(InventoryProduct, db)
                transaction_repo = InventoryTransactionRepository(InventoryTransaction, db)
                
                product = product_repo.get_by_id(product_id)
                if not product:
                    return not_found_response("Product")
                
                if product.status != InventoryStatus.AVAILABLE:
                    return error_response("Product is not available for sale", 400)
                
                if quantity > product.quantity:
                    return error_response("Insufficient quantity", 400)
                
                # Update product quantity and status
                new_quantity = product.quantity - quantity
                if new_quantity == 0:
                    product.status = InventoryStatus.SOLD
                    product.quantity = 0
                else:
                    product.quantity = new_quantity
                
                # Create transaction (EXIT)
                transaction_repo.create(
                    product_id=product.id,
                    transaction_type=InventoryTransactionType.EXIT,
                    quantity=-quantity,  # Negative for exit
                    reason="Sale",
                    sale_id=sale_id,
                    user_id=user_id
                )
                
                db.commit()
                db.refresh(product)
                
                return success_response(
                    self._serialize_product(product),
                    "Product marked as sold successfully"
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_expired_products(self) -> tuple:
        """Get all expired products"""
        try:
            with get_db_session() as db:
                repo = InventoryProductRepository(InventoryProduct, db)
                expired = repo.get_expired_products()
                
                # Mark as expired
                for product in expired:
                    product.status = InventoryStatus.EXPIRED
                db.commit()
                
                return success_response([self._serialize_product(p) for p in expired])
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_transactions(self, product_id: str) -> tuple:
        """Get all transactions for a product"""
        try:
            with get_db_session() as db:
                transaction_repo = InventoryTransactionRepository(InventoryTransaction, db)
                transactions = transaction_repo.get_by_product_id(product_id)
                
                return success_response([self._serialize_transaction(t) for t in transactions])
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_product(self, product: InventoryProduct) -> Dict[str, Any]:
        """Serialize product to dictionary"""
        return {
            'id': product.id,
            'product_type': product.product_type.name if product.product_type else None,
            'product_name': product.product_name,
            'quantity': product.quantity,
            'unit': product.unit.name if product.unit else None,
            'production_date': product.production_date.isoformat() if product.production_date else None,
            'expiration_date': product.expiration_date.isoformat() if product.expiration_date else None,
            'location': product.location,
            'unit_price': product.unit_price,
            'status': product.status.name if product.status else None,
            'animal_id': product.animal_id,
            'created_by': product.created_by,
            'notes': product.notes,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
        }
    
    def _serialize_transaction(self, transaction: InventoryTransaction) -> Dict[str, Any]:
        """Serialize transaction to dictionary"""
        return {
            'id': transaction.id,
            'product_id': transaction.product_id,
            'transaction_type': transaction.transaction_type.name if transaction.transaction_type else None,
            'quantity': transaction.quantity,
            'reason': transaction.reason,
            'sale_id': transaction.sale_id,
            'user_id': transaction.user_id,
            'notes': transaction.notes,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
        }

