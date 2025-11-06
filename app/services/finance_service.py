"""
Finance service for consolidated financial operations
Combines product sales and animal sales into total sales
"""
from typing import List, Dict, Any, Optional
from app.repositories.product_sale_repository import ProductSaleRepository
from app.repositories.animal_sale_repository import AnimalSaleRepository
from app.utils.database import get_db_session
from app.utils.response import success_response, error_response
from models import ProductSale, AnimalSale


class FinanceService:
    """
    Finance service handling consolidated financial operations
    """
    
    def get_total_sales(self, sort_by: Optional[str] = None) -> tuple:
        """
        Get all sales (products + animals) consolidated
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by sale date/created_at)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with get_db_session() as db:
                # Get product sales
                product_repo = ProductSaleRepository(ProductSale, db)
                product_sales = product_repo.get_all_sorted(sort_by)
                
                # Get animal sales with animal relationship loaded
                from sqlalchemy.orm import joinedload
                from sqlalchemy import asc, desc
                from models import AnimalSale as AnimalSaleModel
                
                query = db.query(AnimalSaleModel).options(joinedload(AnimalSaleModel.animal))
                
                if sort_by == 'asc':
                    query = query.order_by(asc(AnimalSaleModel.created_at))
                elif sort_by == 'desc':
                    query = query.order_by(desc(AnimalSaleModel.created_at))
                
                animal_sales = query.all()
                
                # Serialize and combine
                total_sales = []
                
                # Add product sales
                for sale in product_sales:
                    sale_data = self._serialize_product_sale(sale)
                    sale_data['sale_type'] = 'product'
                    total_sales.append(sale_data)
                
                # Add animal sales
                for sale in animal_sales:
                    sale_data = self._serialize_animal_sale(sale, db)
                    sale_data['sale_type'] = 'animal'
                    total_sales.append(sale_data)
                
                # Sort combined list if needed
                if sort_by:
                    reverse = sort_by == 'desc'
                    total_sales.sort(
                        key=lambda x: x.get('sale_date') or x.get('created_at') or '',
                        reverse=reverse
                    )
                
                return success_response(
                    total_sales,
                    "Total sales retrieved successfully"
                )
        except Exception as e:
            return error_response(str(e), 500)
    
    def _serialize_product_sale(self, sale: ProductSale) -> Dict[str, Any]:
        """
        Serialize product sale to dictionary
        
        Args:
            sale: ProductSale instance
            
        Returns:
            Dictionary representation
        """
        return {
            'id': sale.id,
            'sale_type': 'product',  # Will be overwritten but kept for consistency
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
    
    def _serialize_animal_sale(self, sale: AnimalSale, db_session) -> Dict[str, Any]:
        """
        Serialize animal sale to dictionary
        
        Args:
            sale: AnimalSale instance
            db_session: Database session for querying animal
            
        Returns:
            Dictionary representation
        """
        # Get animal name if available
        animal_name = None
        if sale.animal:
            animal_name = sale.animal.name
        else:
            # Try to load animal if not already loaded
            try:
                from models import Animal
                animal = db_session.query(Animal).filter(Animal.id == sale.animal_id).first()
                if animal:
                    animal_name = animal.name
            except:
                pass
        
        return {
            'id': sale.id,
            'sale_type': 'animal',  # Will be overwritten but kept for consistency
            'animal_id': sale.animal_id,
            'animal_type': sale.animal_type.value if sale.animal_type else None,
            'animal_name': animal_name,
            'price': sale.price,
            'total_price': sale.price,  # For consistency with product sales
            'weight': sale.weight,
            'height': sale.height,
            'notes': sale.notes,
            'sold_by': sale.sold_by,
            'sale_date': sale.created_at.isoformat() if sale.created_at else None,  # Use created_at as sale_date
            'created_at': sale.created_at.isoformat() if sale.created_at else None,
            'updated_at': sale.updated_at.isoformat() if sale.updated_at else None
        }

