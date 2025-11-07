
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
    PREGNANCY = "PREGNANCY"  # Registro de preñez
    SLAUGHTER = "SLAUGHTER"
    OTHER = "OTHER"

class ChickenEventType(enum.Enum):
    MAINTENANCE_FENCE = "MAINTENANCE_FENCE"
    VITAMINS_CORRAL = "VITAMINS_CORRAL"
    OTHER = "OTHER"

class CowEventType(enum.Enum):
    VITAMINS = "VITAMINS"
    DEWORMING = "DEWORMING"
    PREGNANCY = "PREGNANCY"  # Registro de preñez
    BIRTH = "BIRTH"  # Nacimiento de ternero
    DRY_OFF = "DRY_OFF"  # Secado de ubre
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

class AnimalOrigin(enum.Enum):
    BORN = "BORN"  # Nacido en la granja
    PURCHASED = "PURCHASED"  # Comprado

# Enums para Inventario
class InventoryProductType(enum.Enum):
    MEAT_RABBIT = "MEAT_RABBIT"  # Carne de conejo
    MEAT_CHICKEN = "MEAT_CHICKEN"  # Carne de pollo
    MEAT_COW = "MEAT_COW"  # Carne de res
    MEAT_SHEEP = "MEAT_SHEEP"  # Carne de oveja
    EGGS = "EGGS"  # Huevos
    MILK = "MILK"  # Leche
    CHEESE = "CHEESE"  # Queso
    BUTTER = "BUTTER"  # Mantequilla
    WOOL = "WOOL"  # Lana
    HONEY = "HONEY"  # Miel
    WAX = "WAX"  # Cera
    OTHER = "OTHER"  # Otros productos

class InventoryUnit(enum.Enum):
    KG = "KG"  # Kilogramos
    GRAMS = "GRAMS"  # Gramos
    LITERS = "LITERS"  # Litros
    UNITS = "UNITS"  # Unidades
    DOZENS = "DOZENS"  # Docenas

class InventoryStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"  # Disponible para venta
    RESERVED = "RESERVED"  # Reservado para una venta
    SOLD = "SOLD"  # Vendido
    EXPIRED = "EXPIRED"  # Vencido
    DISCARDED = "DISCARDED"  # Descartado

class InventoryTransactionType(enum.Enum):
    ENTRY = "ENTRY"  # Entrada (producción/sacrificio)
    EXIT = "EXIT"  # Salida (venta)
    ADJUSTMENT = "ADJUSTMENT"  # Ajuste (corrección de inventario)

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
    declined_reason = Column(Text, nullable=True)  # Razón por la que se declinó la alerta

    # Association to an animal (optional)
    animal_type = Column(Enum(AnimalType), nullable=True)
    animal_id = Column(String, ForeignKey("animals.id"), nullable=True)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)

    # Optional link to an originating event
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    
    # Para alertas agrupadas (especialmente sacrificio de conejos)
    # Almacena JSON array de IDs de animales involucrados
    rabbit_ids = Column(Text, nullable=True)  # JSON: ["id1", "id2", "id3"]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------- UNIFIED ANIMAL MODEL ----------
# Tabla única para todos los animales (conejos, vacas, ovejas, gallinas, etc.)
class  Animal(Base):
    __tablename__ = "animals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    species = Column(Enum(AnimalType), nullable=False)  # RABBIT, COW, SHEEP, CHICKEN, etc.
    image = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(Enum(Gender), nullable=True)  # MALE, FEMALE
    
    # Origen del animal
    origin = Column(Enum(AnimalOrigin), nullable=False, default=AnimalOrigin.PURCHASED)  # BORN o PURCHASED
    
    # Relaciones padre-hijo (self-referential)
    mother_id = Column(String, ForeignKey("animals.id"), nullable=True)  # Madre del animal
    father_id = Column(String, ForeignKey("animals.id"), nullable=True)  # Padre del animal
    
    # Información de compra (solo si origin = PURCHASED)
    purchase_date = Column(DateTime, nullable=True)  # Fecha de compra
    purchase_price = Column(Float, nullable=True)  # Precio de compra
    purchase_vendor = Column(String, nullable=True)  # Vendedor/Proveedor
    
    # Estado de descarte/venta
    # discarded = True significa que el animal fue vendido o descartado
    # discarded_reason contiene la razón (ej: "Vendido", "Sacrificado", etc.)
    discarded = Column(Boolean, default=False)
    discarded_reason = Column(Text, nullable=True)
    
    # Estado de sacrificio (especialmente para conejos)
    # Un animal sacrificado no es lo mismo que descartado:
    # - Sacrificado: fue procesado pero puede estar en congelador esperando venta
    # - Descarte: se perdió o murió sin ser procesado
    slaughtered = Column(Boolean, default=False)  # True si fue sacrificado
    slaughtered_date = Column(DateTime, nullable=True)  # Fecha de sacrificio
    in_freezer = Column(Boolean, default=False)  # True si está en congelador esperando venta
    
    # Propietario/Responsable
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Corral (opcional, para agrupación)
    corral_id = Column(String, ForeignKey("corrals.id"), nullable=True)
    
    # Reproductor (especialmente para conejos)
    is_breeder = Column(Boolean, default=False)  # True si es reproductor con genética apropiada
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    animal_sales = relationship("AnimalSale", back_populates="animal")
    owner = relationship("User", foreign_keys=[user_id])
    
    # Relaciones padre-hijo (self-referential)
    mother = relationship("Animal", foreign_keys=[mother_id], remote_side=[id], backref="children_by_mother")
    father = relationship("Animal", foreign_keys=[father_id], remote_side=[id], backref="children_by_father")


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


# ---------- FINANCIAL MODULE ----------
# Enums para módulo financiero
class ProductType(enum.Enum):
    MIEL = "miel"
    HUEVOS = "huevos"
    LECHE = "leche"
    OTROS = "otros"

class ExpenseCategory(enum.Enum):
    ALIMENTACION = "alimentacion"
    MEDICAMENTOS = "medicamentos"
    MANTENIMIENTO = "mantenimiento"
    PERSONAL = "personal"
    SERVICIOS = "servicios"
    EQUIPOS = "equipos"
    OTROS = "otros"

# Ventas de productos no-animales (miel, huevos, leche, etc.)
class ProductSale(Base):
    __tablename__ = "product_sales"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_type = Column(Enum(ProductType), nullable=False)
    quantity = Column(Float, nullable=False)  # Cantidad vendida (kg, docenas, litros, etc.)
    unit_price = Column(Float, nullable=False)  # Precio por unidad
    total_price = Column(Float, nullable=False)  # quantity * unit_price (calculado automáticamente)
    sale_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    customer_name = Column(String, nullable=True)  # Cliente (opcional)
    notes = Column(Text, nullable=True)
    sold_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", foreign_keys=[sold_by])

# Gastos de la finca
class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(Enum(ExpenseCategory), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    vendor = Column(String, nullable=True)  # Proveedor/Vendedor (opcional)
    notes = Column(Text, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", foreign_keys=[created_by])


# ---------- DEAD OFFSPRING (CRÍAS MUERTAS) ----------
# Tabla para registrar crías que nacieron muertas (especialmente para conejos)
class DeadOffspring(Base):
    __tablename__ = "dead_offspring"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mother_id = Column(String, ForeignKey("animals.id"), nullable=False)  # Madre de la cría muerta
    father_id = Column(String, ForeignKey("animals.id"), nullable=True)  # Padre (opcional)
    
    # Información de la cría muerta
    birth_date = Column(DateTime, nullable=False)  # Fecha de nacimiento (cuando nació muerta)
    death_date = Column(DateTime, nullable=False, default=datetime.utcnow)  # Fecha de registro de muerte
    species = Column(Enum(AnimalType), nullable=False, default=AnimalType.RABBIT)  # Especie (principalmente conejos)
    
    # Información adicional
    count = Column(Integer, nullable=False, default=1)  # Cantidad de crías muertas en este evento
    notes = Column(Text, nullable=True)  # Notas sobre posibles causas (enfermedad, déficit vitamínico, etc.)
    suspected_cause = Column(String, nullable=True)  # Causa sospechada (ej: "enfermedad", "déficit vitamínico", "alimento")
    
    # Usuario que registró
    recorded_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    mother = relationship("Animal", foreign_keys=[mother_id])
    father = relationship("Animal", foreign_keys=[father_id])
    recorder = relationship("User", foreign_keys=[recorded_by])


# ---------- INVENTORY MODELS ----------
class InventoryProduct(Base):
    """
    Modelo para productos en inventario (miel, lana, huevos, conejos sacrificados, etc.)
    """
    __tablename__ = "inventory_products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Tipo y nombre del producto
    product_type = Column(Enum(InventoryProductType), nullable=False)
    product_name = Column(String, nullable=False)  # Nombre descriptivo (ej: "Conejo - SitoSito 8")
    
    # Cantidad y unidad
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(Enum(InventoryUnit), nullable=False)
    
    # Fechas importantes
    production_date = Column(DateTime, nullable=False, default=datetime.utcnow)  # Fecha de producción/sacrificio
    expiration_date = Column(DateTime, nullable=True)  # Fecha de vencimiento (opcional)
    
    # Ubicación
    location = Column(String, nullable=True)  # "congelador", "almacen", "refrigerador", etc.
    
    # Precio
    unit_price = Column(Float, nullable=True)  # Precio por unidad (opcional, puede establecerse después)
    
    # Estado
    status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.AVAILABLE)
    
    # Relación con animal (si proviene de un animal específico)
    animal_id = Column(String, ForeignKey("animals.id"), nullable=True)
    
    # Usuario que creó el registro
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Notas adicionales
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    animal = relationship("Animal", foreign_keys=[animal_id])
    creator = relationship("User", foreign_keys=[created_by])
    transactions = relationship("InventoryTransaction", back_populates="product")


class InventoryTransaction(Base):
    """
    Modelo para registrar movimientos de inventario (entradas, salidas, ajustes)
    """
    __tablename__ = "inventory_transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Producto relacionado
    product_id = Column(String, ForeignKey("inventory_products.id"), nullable=False)
    
    # Tipo de transacción
    transaction_type = Column(Enum(InventoryTransactionType), nullable=False)
    
    # Cantidad (positiva para entrada, negativa para salida)
    quantity = Column(Float, nullable=False)
    
    # Razón/motivo
    reason = Column(String, nullable=True)  # "Producción diaria", "Venta", "Ajuste de inventario", etc.
    
    # Relación con venta (si es una salida por venta)
    sale_id = Column(String, ForeignKey("product_sales.id"), nullable=True)
    
    # Usuario que realizó la transacción
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Notas adicionales
    notes = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    product = relationship("InventoryProduct", back_populates="transactions")
    user = relationship("User", foreign_keys=[user_id])
    sale = relationship("ProductSale", foreign_keys=[sale_id])

