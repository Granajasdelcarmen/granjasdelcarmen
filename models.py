
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
    TRABAJADOR = "trabajador"  # Persona que trabaja en la finca

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
    animal_sales = relationship("AnimalSale", back_populates="user")


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



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


# ---------- UNIFIED ANIMAL MODEL ----------
# Tabla única para todos los animales (conejos, vacas, ovejas, gallinas, etc.)
class Animal(Base):
    __tablename__ = "animals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    species = Column(Enum(AnimalType), nullable=False)  # RABBIT, COW, SHEEP, CHICKEN, etc.
    image = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(Enum(Gender), nullable=True)  # MALE, FEMALE
    
    # Estado de descarte/venta
    # discarded = True significa que el animal fue vendido o descartado
    # discarded_reason contiene la razón (ej: "Vendido", "Sacrificado", etc.)
    discarded = Column(Boolean, default=False)
    discarded_reason = Column(Text, nullable=True)
    
    # Propietario/Responsable
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Corral (opcional, para agrupación)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    animal_sales = relationship("AnimalSale", back_populates="animal")
    owner = relationship("User", foreign_keys=[user_id])


# ---------- ANIMAL SALES ----------
# Tabla genérica para ventas de cualquier tipo de animal
class AnimalSale(Base):
    __tablename__ = "animal_sales"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    animal_id = Column(String, ForeignKey("animals.id"), nullable=False)
    animal_type = Column(Enum(AnimalType), nullable=False)  # Para facilitar consultas/filtros
    
    # Información de venta
    price = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)  # Peso al momento de la venta (opcional)
    height = Column(Float, nullable=True)  # Altura (para conejos, etc.)
    
    # Información adicional
    notes = Column(Text, nullable=True)  # Notas adicionales sobre la venta
    
    # Usuario que registró la venta (debe existir en users table con id = Auth0 sub)
    sold_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    animal = relationship("Animal", back_populates="animal_sales")
    user = relationship("User", foreign_keys=[sold_by], back_populates="animal_sales")


# ---------- CORRALS ----------
class Corral(Base):
    __tablename__ = "corrals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    species = Column(Enum(AnimalType), nullable=False)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

