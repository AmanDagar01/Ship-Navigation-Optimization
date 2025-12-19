# Example function that calls get_heuristic_value
from heuristicRetriever import get_heuristic_value

def another_function():
    latitude = 8.750
    longitude = 82.125
    heuristic_value = get_heuristic_value(latitude, longitude)
    print(f"Heuristic value for ({latitude}, {longitude}): {heuristic_value}")

# Call the example function
another_function()
