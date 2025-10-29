"""
User repository with specific user operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from models import User

class UserRepository(BaseRepository[User]):
    """
    User repository with user-specific operations
    """
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users
        
        Returns:
            List of active user instances
        """
        return self.db.query(User).filter(User.is_active == True).all()
    
    def get_by_role(self, role: str) -> List[User]:
        """
        Get users by role
        
        Args:
            role: User role
            
        Returns:
            List of user instances with the specified role
        """
        return self.db.query(User).filter(User.role == role).all()
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
