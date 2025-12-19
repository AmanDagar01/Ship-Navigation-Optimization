"""
Coordinate Conversion Module - Updated for Expanded Bounds
Maintains original grid mapping but expands validation to support wider region
"""

# ============================================================================
# ORIGINAL GRID MAPPING (PRESERVED)
# These are the actual grid-to-coordinate mappings for your map
# ============================================================================
NORTHERNMOST_LATITUDE = 37.1
NORTHERNMOST_GRID_Y = 9
SOUTHERNMOST_LATITUDE = 8.1
SOUTHERNMOST_GRID_Y = 135

WESTERNMOST_LONGITUDE = 68.1167
EASTERNMOST_LONGITUDE = 97.4167
WESTERNMOST_GRID_X = 16
EASTERNMOST_GRID_X = 121

# ============================================================================
# EXPANDED VALIDATION BOUNDS (For accepting wider input range)
# These allow coordinates from neighboring regions
# ============================================================================
MIN_LONGITUDE_INPUT = 60.0   # Expanded to include Arabian Sea approaches
MAX_LONGITUDE_INPUT = 100.0  # Expanded to include Andaman Sea
MIN_LATITUDE_INPUT = 0.0     # Expanded to include southern Indian Ocean
MAX_LATITUDE_INPUT = 40.0    # Expanded to include northern regions

# Grid configuration
GRID_WIDTH = 550
GRID_HEIGHT = 600
GRID_SIZE = 4


def grid_to_latitude(grid_y):
    """
    Convert grid Y coordinate to latitude
    Original mapping preserved for accuracy
    """
    latitude_per_cell = (NORTHERNMOST_LATITUDE - SOUTHERNMOST_LATITUDE) / (NORTHERNMOST_GRID_Y - SOUTHERNMOST_GRID_Y)
    latitude = NORTHERNMOST_LATITUDE + (grid_y - NORTHERNMOST_GRID_Y) * latitude_per_cell
    latitude = round(latitude / 0.250) * 0.250
    return round(latitude, 3)


def grid_to_longitude(grid_x):
    """
    Convert grid X coordinate to longitude
    Original mapping preserved for accuracy
    """
    longitude_per_cell = (EASTERNMOST_LONGITUDE - WESTERNMOST_LONGITUDE) / (EASTERNMOST_GRID_X - WESTERNMOST_GRID_X)
    longitude = WESTERNMOST_LONGITUDE + (grid_x - WESTERNMOST_GRID_X) * longitude_per_cell
    # Modify rounding for longitude to nearest multiple of 0.250 starting from 0.125
    longitude = round((longitude - 0.125) / 0.250) * 0.250 + 0.125
    return round(longitude, 3)


def latitude_to_grid(latitude):
    """
    Convert latitude to grid Y coordinate
    Now handles wider input range with bounds checking
    """
    # Clamp latitude to valid grid range
    if latitude > NORTHERNMOST_LATITUDE:
        print(f"Warning: Latitude {latitude} clamped to {NORTHERNMOST_LATITUDE}")
        latitude = NORTHERNMOST_LATITUDE
    elif latitude < SOUTHERNMOST_LATITUDE:
        print(f"Warning: Latitude {latitude} clamped to {SOUTHERNMOST_LATITUDE}")
        latitude = SOUTHERNMOST_LATITUDE
    
    latitude_per_cell = (NORTHERNMOST_LATITUDE - SOUTHERNMOST_LATITUDE) / (NORTHERNMOST_GRID_Y - SOUTHERNMOST_GRID_Y)
    grid_y = NORTHERNMOST_GRID_Y + (latitude - NORTHERNMOST_LATITUDE) / latitude_per_cell
    grid_y = round(grid_y)
    
    # Ensure grid_y is within valid bounds
    grid_y = max(NORTHERNMOST_GRID_Y, min(grid_y, SOUTHERNMOST_GRID_Y))
    
    return grid_y


def longitude_to_grid(longitude):
    """
    Convert longitude to grid X coordinate
    Now handles wider input range with bounds checking
    """
    # Clamp longitude to valid grid range
    if longitude < WESTERNMOST_LONGITUDE:
        print(f"Warning: Longitude {longitude} clamped to {WESTERNMOST_LONGITUDE}")
        longitude = WESTERNMOST_LONGITUDE
    elif longitude > EASTERNMOST_LONGITUDE:
        print(f"Warning: Longitude {longitude} clamped to {EASTERNMOST_LONGITUDE}")
        longitude = EASTERNMOST_LONGITUDE
    
    longitude_per_cell = (EASTERNMOST_LONGITUDE - WESTERNMOST_LONGITUDE) / (EASTERNMOST_GRID_X - WESTERNMOST_GRID_X)
    grid_x = WESTERNMOST_GRID_X + (longitude - WESTERNMOST_LONGITUDE) / longitude_per_cell
    grid_x = round(grid_x)
    
    # Ensure grid_x is within valid bounds
    grid_x = max(WESTERNMOST_GRID_X, min(grid_x, EASTERNMOST_GRID_X))
    
    return grid_x


def round_latitude(latitude):
    """
    Rounds a latitude to the nearest multiple of 0.250.
    """
    rounded_latitude = round(latitude / 0.250) * 0.250
    return round(rounded_latitude, 3)


def round_longitude(longitude):
    """
    Rounds a longitude to the nearest multiple of 0.250, starting from 0.125.
    """
    rounded_longitude = round((longitude - 0.125) / 0.250) * 0.250 + 0.125
    return round(rounded_longitude, 3)


def is_within_input_bounds(longitude, latitude):
    """
    Check if coordinates are within expanded input bounds
    This allows wider coordinate entry but they'll be clamped to actual grid range
    """
    return (MIN_LONGITUDE_INPUT <= longitude <= MAX_LONGITUDE_INPUT and
            MIN_LATITUDE_INPUT <= latitude <= MAX_LATITUDE_INPUT)


def is_within_grid_bounds(longitude, latitude):
    """
    Check if coordinates are within actual grid mapping range
    """
    return (WESTERNMOST_LONGITUDE <= longitude <= EASTERNMOST_LONGITUDE and
            SOUTHERNMOST_LATITUDE <= latitude <= NORTHERNMOST_LATITUDE)


def get_bounds_info():
    """
    Get information about coordinate bounds
    """
    return {
        'input_validation': {
            'longitude': f"{MIN_LONGITUDE_INPUT}°E to {MAX_LONGITUDE_INPUT}°E",
            'latitude': f"{MIN_LATITUDE_INPUT}°N to {MAX_LATITUDE_INPUT}°N",
            'description': 'Expanded bounds for validation (coordinates will be clamped to grid range)'
        },
        'grid_mapping': {
            'longitude': f"{WESTERNMOST_LONGITUDE}°E to {EASTERNMOST_LONGITUDE}°E",
            'latitude': f"{SOUTHERNMOST_LATITUDE}°N to {NORTHERNMOST_LATITUDE}°N",
            'grid_x': f"{WESTERNMOST_GRID_X} to {EASTERNMOST_GRID_X}",
            'grid_y': f"{NORTHERNMOST_GRID_Y} to {SOUTHERNMOST_GRID_Y}",
            'description': 'Actual grid coordinate range on your map'
        }
    }


# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_conversions():
    """Test coordinate conversions with known locations"""
    print("=" * 70)
    print("COORDINATE CONVERSION TEST - UPDATED BOUNDS")
    print("=" * 70)
    
    # Test with your original test values
    print("\n📍 Original Test Values:")
    print("-" * 70)
    
    print("\nTest 1: Grid to Coordinates")
    print(f"  Grid Y=123 → Latitude = {grid_to_latitude(123)}°N")
    print(f"  Grid X=103 → Longitude = {grid_to_longitude(103)}°E")
    
    print("\nTest 2: Coordinates to Grid")
    print(f"  Latitude 10.80°N → Grid Y = {latitude_to_grid(10.80)}")
    print(f"  Longitude 92.41°E → Grid X = {longitude_to_grid(92.41)}")
    
    print("\nTest 3: Rounding Functions")
    print(f"  round_latitude(101.134) = {round_latitude(101.134)}")
    print(f"  round_longitude(101.134) = {round_longitude(101.134)}")
    
    # Test with major Indian ports
    print("\n\n📍 Testing Major Indian Ports:")
    print("-" * 70)
    
    test_locations = [
        ("Mumbai", 72.82, 18.93),
        ("Chennai", 80.27, 13.08),
        ("Kochi", 76.27, 9.93),
        ("Visakhapatnam", 83.28, 17.69),
    ]
    
    for name, lon, lat in test_locations:
        # Check if within input bounds
        within_input = is_within_input_bounds(lon, lat)
        within_grid = is_within_grid_bounds(lon, lat)
        
        print(f"\n{name}: {lon}°E, {lat}°N")
        print(f"  Within input bounds: {'✅ Yes' if within_input else '❌ No'}")
        print(f"  Within grid bounds: {'✅ Yes' if within_grid else '❌ No'}")
        
        if within_input:
            # Convert to grid
            grid_x = longitude_to_grid(lon)
            grid_y = latitude_to_grid(lat)
            
            # Convert back
            back_lon = grid_to_longitude(grid_x)
            back_lat = grid_to_latitude(grid_y)
            
            print(f"  Grid: ({grid_x}, {grid_y})")
            print(f"  Converted back: {back_lon}°E, {back_lat}°N")
    
    # Test edge cases (coordinates outside grid but within input bounds)
    print("\n\n📍 Testing Edge Cases (Outside Grid, Within Input):")
    print("-" * 70)
    
    edge_cases = [
        ("West of grid", 65.0, 15.0),  # West of WESTERNMOST_LONGITUDE
        ("East of grid", 99.0, 15.0),  # East of EASTERNMOST_LONGITUDE
        ("South of grid", 75.0, 5.0),  # South of SOUTHERNMOST_LATITUDE
        ("North of grid", 75.0, 39.0), # North of NORTHERNMOST_LATITUDE
    ]
    
    for name, lon, lat in edge_cases:
        within_input = is_within_input_bounds(lon, lat)
        within_grid = is_within_grid_bounds(lon, lat)
        
        print(f"\n{name}: {lon}°E, {lat}°N")
        print(f"  Within input bounds: {'✅ Yes' if within_input else '❌ No'}")
        print(f"  Within grid bounds: {'✅ Yes' if within_grid else '❌ No'}")
        
        if within_input:
            grid_x = longitude_to_grid(lon)
            grid_y = latitude_to_grid(lat)
            back_lon = grid_to_longitude(grid_x)
            back_lat = grid_to_latitude(grid_y)
            
            print(f"  Grid (clamped): ({grid_x}, {grid_y})")
            print(f"  Converted back: {back_lon}°E, {back_lat}°N")
            print(f"  Note: Coordinate was clamped to grid range")
    
    # Display bounds info
    print("\n" + "=" * 70)
    print("BOUNDS INFORMATION:")
    print("-" * 70)
    bounds = get_bounds_info()
    
    print("\n📥 Input Validation Bounds (What you can enter):")
    print(f"  Longitude: {bounds['input_validation']['longitude']}")
    print(f"  Latitude: {bounds['input_validation']['latitude']}")
    print(f"  {bounds['input_validation']['description']}")
    
    print("\n🗺️  Grid Mapping Bounds (Actual map coverage):")
    print(f"  Longitude: {bounds['grid_mapping']['longitude']}")
    print(f"  Latitude: {bounds['grid_mapping']['latitude']}")
    print(f"  Grid X: {bounds['grid_mapping']['grid_x']}")
    print(f"  Grid Y: {bounds['grid_mapping']['grid_y']}")
    print(f"  {bounds['grid_mapping']['description']}")
    
    print("=" * 70)


running = True

if __name__ == "__main__":
    test_conversions()
    
    # Original test code (commented out)
    # while running:
    #     # Testing grid to latitude and longitude
    #     print("Latitude = ", grid_to_latitude(123))
    #     print("Longitude = ", grid_to_longitude(103))
    #
    #     # Testing latitude and longitude to grid
    #     print("Grid Y for latitude =", latitude_to_grid(10.80))
    #     print("Grid X for longitude = ", longitude_to_grid(92.41))
    #     
    #     # Testing rounding functions
    #     print(round_latitude(101.134))
    #     print(round_longitude(101.134))
    #     running = False
