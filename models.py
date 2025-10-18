"""Database models for Granjas del Carmen"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

Base = declarative_base()

# ---------- ENUMS ----------
class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    
class Role(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

# ---------- MODELOS ----------
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)
    address = Column(Text)
    role = Column(Enum(Role), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   
   
class Rabbit(Base):
    __tablename__ = "rabbits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    image = Column(String)
    birth_date = Column(DateTime)
    gender = Column(Enum(Gender))
    discarded = Column(Boolean, default=False)
    discarded_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones


class RabbitSales(Base):
    __tablename__ = "rabbit_sales"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rabbit_id = Column(String, ForeignKey("rabbits.id"))
    price = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, ForeignKey("users.id"))


    # Relaciones
    rabbit = relationship("Rabbit", back_populates="rabbit_sales")
    user = relationship("User", back_populates="rabbit_sales")


