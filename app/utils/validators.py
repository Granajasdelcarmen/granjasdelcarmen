"""
Common validation utilities
"""
from datetime import datetime
from typing import Optional, Dict, Any

def validate_date_format(date_string: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
    """
    Validate and parse date string
    
    Args:
        date_string: Date string to validate
        format: Expected date format
        
    Returns:
        Parsed datetime object or None if invalid
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, format)
    except ValueError:
        raise ValueError(f"Invalid date format. Expected {format}")

def validate_gender(gender: str) -> bool:
    """
    Validate gender value
    
    Args:
        gender: Gender string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return gender in ["MALE", "FEMALE"]

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in data
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required field is missing
    """
    if not data:
        raise ValueError("No data provided")
    
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_enum_value(value: str, valid_values: list, field_name: str) -> None:
    """
    Validate that value is in the list of valid values
    
    Args:
        value: Value to validate
        valid_values: List of valid values
        field_name: Name of the field for error message
        
    Raises:
        ValueError: If value is not valid
    """
    if value and value not in valid_values:
        raise ValueError(f"{field_name} must be one of: {', '.join(valid_values)}")

def validate_positive_integer(value: int, field_name: str) -> None:
    """
    Validate that value is a positive integer
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        
    Raises:
        ValueError: If value is not a positive integer
    """
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")