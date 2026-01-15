import math

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

def check_geofence(lat, lng, geofence_config):
    """
    Check if device location is within or outside geofence
    
    Args:
        lat: Device latitude
        lng: Device longitude
        geofence_config: Dict with 'center_lat', 'center_lng', 'radius_km'
    
    Returns:
        tuple: (is_inside, distance_from_center_km)
    """
    if not geofence_config or 'center_lat' not in geofence_config:
        return None, None
    
    center_lat = geofence_config['center_lat']
    center_lng = geofence_config['center_lng']
    radius_km = geofence_config.get('radius_km', 5.0)
    
    distance = calculate_distance(lat, lng, center_lat, center_lng)
    is_inside = distance <= radius_km
    
    return is_inside, distance

def is_geofence_breach(lat, lng, geofence_config, previous_inside=None):
    """
    Check if device has breached geofence (left safe zone)
    
    Args:
        lat: Current device latitude
        lng: Current device longitude
        geofence_config: Geofence configuration
        previous_inside: Previous geofence status (True if was inside)
    
    Returns:
        bool: True if breach detected (was inside, now outside)
    """
    if not geofence_config:
        return False
    
    is_inside, distance = check_geofence(lat, lng, geofence_config)
    
    # Breach if was inside before and now outside
    if previous_inside is True and not is_inside:
        return True
    
    return False

