"""
Product sale repository with specific product sale operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.repositories.base import BaseRepository
from models import ProductSale, ProductType

class ProductSaleRepository(BaseRepository[ProductSale]):
    """
    Product sale repository with product sale-specific operations
    """
    
    def get_all_sorted(self, sort_by: Optional[str] = None) -> List[ProductSale]:
        """
        Get all product sales with optional sorting
        
        Args:
            sort_by: Sort order ('asc' or 'desc' by sale_date)
            
        Returns:
            List of product sale instances
        """
        query = self.db.query(ProductSale)
        
        if sort_by == 'asc':
            query = query.order_by(asc(ProductSale.sale_date))
        elif sort_by == 'desc':
            query = query.order_by(desc(ProductSale.sale_date))
        
        return query.all()
    
    def get_by_product_type(self, product_type: ProductType) -> List[ProductSale]:
        """
        Get product sales by product type
        
        Args:
            product_type: Product type (miel, huevos, leche, otros)
            
        Returns:
            List of product sale instances
        """
        return self.db.query(ProductSale).filter(ProductSale.product_type == product_type).all()
    
    def get_by_sold_by(self, sold_by: str) -> List[ProductSale]:
        """
        Get product sales by seller (user ID)
        
        Args:
            sold_by: User ID who made the sale
            
        Returns:
            List of product sale instances
        """
        return self.db.query(ProductSale).filter(ProductSale.sold_by == sold_by).all()

