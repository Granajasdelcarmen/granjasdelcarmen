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

# New enums for Events/Alerts
class AnimalType(enum.Enum):
    RABBIT = "RABBIT"
    COW = "COW"
    CHICKEN = "CHICKEN"
    SHEEP = "SHEEP"
    OTHER = "OTHER"

class GeneralEventType(enum.Enum):
    MAINTENANCE = "MAINTENANCE"
    VITAMINS = "VITAMINS"
    FENCING = "FENCING"
    OTHER = "OTHER"

# Per-species event enums
class RabbitEventType(enum.Enum):
    MAINTENANCE_CAGES = "MAINTENANCE_CAGES"
    MAINTENANCE_TANKS = "MAINTENANCE_TANKS"
    VITAMINS_CORRAL = "VITAMINS_CORRAL"
    SLAUGHTER = "SLAUGHTER"
    OTHER = "OTHER"

class ChickenEventType(enum.Enum):
    MAINTENANCE_FENCE = "MAINTENANCE_FENCE"
    VITAMINS_CORRAL = "VITAMINS_CORRAL"
    OTHER = "OTHER"

class CowEventType(enum.Enum):
    VITAMINS = "VITAMINS"
    DEWORMING = "DEWORMING"
    OTHER = "OTHER"

class SheepEventType(enum.Enum):
    VITAMINS = "VITAMINS"
    DEWORMING = "DEWORMING"
    OTHER = "OTHER"

class Scope(enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    GROUP = "GROUP"

class AlertStatus(enum.Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DONE = "DONE"
    EXPIRED = "EXPIRED"

class AlertPriority(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

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
    rabbit_sales = relationship("RabbitSales", back_populates="user")


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
    rabbit_sales = relationship("RabbitSales", back_populates="rabbit")


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



# ---------- NEW MODELS ----------
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Optional generic category for analytics/filtering
    name = Column(Enum(GeneralEventType), nullable=True)
    description = Column(Text)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Scope for FE filtering and logic
    scope = Column(Enum(Scope), nullable=False, default=Scope.INDIVIDUAL)

    # Per-species event types (only one should be non-null)
    rabbit_event = Column(Enum(RabbitEventType), nullable=True)
    chicken_event = Column(Enum(ChickenEventType), nullable=True)
    cow_event = Column(Enum(CowEventType), nullable=True)
    sheep_event = Column(Enum(SheepEventType), nullable=True)

    # Associations
    animal_type = Column(Enum(AnimalType), nullable=True)
    animal_id = Column(String, ForeignKey("animals.id"), nullable=True)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    init_date = Column(DateTime, nullable=False)
    max_date = Column(DateTime, nullable=False)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.PENDING)
    priority = Column(Enum(AlertPriority), nullable=False, default=AlertPriority.MEDIUM)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Association to an animal (optional)
    animal_type = Column(Enum(AnimalType), nullable=True)
    animal_id = Column(String, ForeignKey("animals.id"), nullable=True)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)

    # Optional link to an originating event
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Unified animals and corrals for grouping and filtering
class Animal(Base):
    __tablename__ = "animals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    species = Column(Enum(AnimalType), nullable=False)
    sex = Column(Enum(Gender), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Corral(Base):
    __tablename__ = "corrals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    species = Column(Enum(AnimalType), nullable=False)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

