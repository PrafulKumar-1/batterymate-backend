import re
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, ""
    return False, "Invalid email format"

def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """Validate latitude and longitude"""
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return True, ""
    return False, "Invalid coordinates"

def validate_battery(battery: float) -> Tuple[bool, str]:
    """Validate battery percentage"""
    if 0 <= battery <= 100:
        return True, ""
    return False, "Battery must be between 0-100%"

def validate_distance(distance: float) -> Tuple[bool, str]:
    """Validate distance"""
    if distance > 0:
        return True, ""
    return False, "Distance must be positive"

def validate_vehicle_year(year: int) -> Tuple[bool, str]:
    """Validate vehicle year"""
    from datetime import datetime
    current_year = datetime.now().year
    if 2010 <= year <= current_year:
        return True, ""
    return False, "Invalid vehicle year"
