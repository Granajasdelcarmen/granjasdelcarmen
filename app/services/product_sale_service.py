"""
Product sale service with business logic for product sales
"""
from typing import List, Dict, Any, Optional
from app.repositories.product_sale_repository import ProductSaleRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response, not_found_response
from models import ProductSale, ProductType

class ProductSaleService:
    """
    Product sale service handling product sale business logic
    """
    
    def get_all_product_sales(self, sort_by: Optional[str] = None) -> tuple:
        """
        Get all product sales
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by sale_date)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ProductSaleRepository(ProductSale, db)
                product_sales = repo.get_all_sorted(sort_by)
                
                return success_response(
                    [self._serialize_product_sale(sale) for sale in product_sales],
                    "Product sales retrieved successfully"
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def get_product_sale_by_id(self, sale_id: str) -> tuple:
        """
        Get product sale by ID
        
        Args:
            sale_id: Product sale ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ProductSaleRepository(ProductSale, db)
                sale = repo.get_by_id(sale_id)
                
                if not sale:
                    return not_found_response("Product sale")
                
                return success_response(self._serialize_product_sale(sale), "Product sale retrieved successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def create_product_sale(self, sale_data: Dict[str, Any], user_id: str) -> tuple:
        """
        Create a new product sale (admin only)
        
        Args:
            sale_data: Product sale data dictionary
            user_id: User ID who is creating the sale
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate required fields
            required_fields = ['product_type', 'quantity', 'unit_price', 'sale_date']
            for field in required_fields:
                if field not in sale_data:
                    return error_response(f"{field} is required", 400)
            
            # Validate product type
            product_type_str = sale_data['product_type'].lower()
            product_type_mapping = {
                'miel': ProductType.MIEL,
                'huevos': ProductType.HUEVOS,
                'leche': ProductType.LECHE,
                'otros': ProductType.OTROS
            }
            
            if product_type_str not in product_type_mapping:
                return error_response(f"Invalid product_type: {sale_data['product_type']}. Valid types are: miel, huevos, leche, otros", 400)
            
            # Calculate total price
            quantity = float(sale_data['quantity'])
            unit_price = float(sale_data['unit_price'])
            total_price = quantity * unit_price
            
            # Validate positive values
            if quantity <= 0:
                return error_response("quantity must be greater than 0", 400)
            if unit_price <= 0:
                return error_response("unit_price must be greater than 0", 400)
            
            with get_db_session() as db:
                repo = ProductSaleRepository(ProductSale, db)
                
                # Create product sale
                sale = repo.create(
                    product_type=product_type_mapping[product_type_str],
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    sale_date=sale_data['sale_date'],
                    customer_name=sale_data.get('customer_name'),
                    notes=sale_data.get('notes'),
                    sold_by=user_id
                )
                
                return success_response(self._serialize_product_sale(sale), "Product sale created successfully", 201)
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def update_product_sale(self, sale_id: str, sale_data: Dict[str, Any]) -> tuple:
        """
        Update product sale (admin only)
        
        Args:
            sale_id: Product sale ID
            sale_data: Updated product sale data
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ProductSaleRepository(ProductSale, db)
                
                # Check if sale exists
                sale = repo.get_by_id(sale_id)
                if not sale:
                    return not_found_response("Product sale")
                
                # Update fields if provided
                update_data = {}
                
                if 'product_type' in sale_data:
                    product_type_str = sale_data['product_type'].lower()
                    product_type_mapping = {
                        'miel': ProductType.MIEL,
                        'huevos': ProductType.HUEVOS,
                        'leche': ProductType.LECHE,
                        'otros': ProductType.OTROS
                    }
                    if product_type_str not in product_type_mapping:
                        return error_response(f"Invalid product_type: {sale_data['product_type']}", 400)
                    update_data['product_type'] = product_type_mapping[product_type_str]
                
                if 'quantity' in sale_data:
                    update_data['quantity'] = float(sale_data['quantity'])
                    if update_data['quantity'] <= 0:
                        return error_response("quantity must be greater than 0", 400)
                
                if 'unit_price' in sale_data:
                    update_data['unit_price'] = float(sale_data['unit_price'])
                    if update_data['unit_price'] <= 0:
                        return error_response("unit_price must be greater than 0", 400)
                
                # Recalculate total_price if quantity or unit_price changed
                if 'quantity' in update_data or 'unit_price' in update_data:
                    quantity = update_data.get('quantity', sale.quantity)
                    unit_price = update_data.get('unit_price', sale.unit_price)
                    update_data['total_price'] = quantity * unit_price
                
                if 'sale_date' in sale_data:
                    update_data['sale_date'] = sale_data['sale_date']
                
                if 'customer_name' in sale_data:
                    update_data['customer_name'] = sale_data['customer_name']
                
                if 'notes' in sale_data:
                    update_data['notes'] = sale_data['notes']
                
                # Update sale
                updated_sale = repo.update(sale_id, **update_data)
                
                return success_response(self._serialize_product_sale(updated_sale), "Product sale updated successfully")
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(str(e), 500)
    
    def delete_product_sale(self, sale_id: str) -> tuple:
        """
        Delete product sale (admin only)
        
        Args:
            sale_id: Product sale ID
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                repo = ProductSaleRepository(ProductSale, db)
                
                # Check if sale exists
                if not repo.exists(sale_id):
                    return not_found_response("Product sale")
                
                # Delete sale
                repo.delete(sale_id)
                
                return success_response(None, "Product sale deleted successfully")
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_product_sale(self, sale: ProductSale) -> Dict[str, Any]:
        """
        Serialize product sale model to dictionary
        
        Args:
            sale: ProductSale instance
            
        Returns:
            Dictionary representation of product sale
        """
        return {
            'id': sale.id,
            'product_type': sale.product_type.value if sale.product_type else None,
            'quantity': sale.quantity,
            'unit_price': sale.unit_price,
            'total_price': sale.total_price,
            'sale_date': sale.sale_date.isoformat() if sale.sale_date else None,
            'customer_name': sale.customer_name,
            'notes': sale.notes,
            'sold_by': sale.sold_by,
            'created_at': sale.created_at.isoformat() if sale.created_at else None,
            'updated_at': sale.updated_at.isoformat() if sale.updated_at else None
        }

