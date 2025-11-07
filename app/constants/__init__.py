"""
Application Constants
Centralized constants for the application
"""
from models import AnimalType

# Animal Species Constants - Use enum values from models
ANIMAL_SPECIES = {
    'RABBIT': AnimalType.RABBIT,
    'COW': AnimalType.COW,
    'SHEEP': AnimalType.SHEEP,
    'CHICKEN': AnimalType.CHICKEN,
    'OTHER': AnimalType.OTHER
}

# Animal Species Labels for UI/API responses
ANIMAL_SPECIES_LABELS = {
    AnimalType.RABBIT: 'Conejos',
    AnimalType.COW: 'Vacas',
    AnimalType.SHEEP: 'Ovejas',
    AnimalType.CHICKEN: 'Pollos',
    AnimalType.OTHER: 'Otros'
}
