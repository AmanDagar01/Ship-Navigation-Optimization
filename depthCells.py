import csv
import pickle
import os

# Function to convert latitude to grid y-coordinate
def latitude_to_grid(latitude):
    northernmost_latitude = 37.1
    northernmost_grid_y = 9
    southernmost_latitude = 8.1
    southernmost_grid_y = 135
    latitude_per_cell = (northernmost_latitude - southernmost_latitude) / (northernmost_grid_y - southernmost_grid_y)
    grid_y = northernmost_grid_y + (latitude - northernmost_latitude) / latitude_per_cell
    grid_y = round(grid_y)
    return grid_y

# Function to convert longitude to grid x-coordinate
def longitude_to_grid(longitude):
    westernmost_longitude = 68.1167
    easternmost_longitude = 97.4167
    westernmost_grid_x = 16
    easternmost_grid_x = 121
    longitude_per_cell = (easternmost_longitude - westernmost_longitude) / (easternmost_grid_x - westernmost_grid_x)
    grid_x = westernmost_grid_x + (longitude - westernmost_longitude) / longitude_per_cell
    grid_x = round(grid_x)
    return grid_x

# Function to round latitude to the nearest multiple of 0.250
def round_latitude(latitude):
    rounded_latitude = round(latitude / 0.250) * 0.250
    return round(rounded_latitude, 3)

# Function to round longitude to the nearest multiple of 0.250, starting from 0.125
def round_longitude(longitude):
    rounded_longitude = round((longitude - 0.125) / 0.250) * 0.250 + 0.125
    return round(rounded_longitude, 3)

# Function to process the CSV and filter by depth, storing results persistently in a pickle file
def process_csv(file_path, storage_file="lat_long_data.pkl"):
    # Check if the data is already saved in the pickle file
    if os.path.exists(storage_file):
        # Load the pre-calculated data from the pickle file
        with open(storage_file, 'rb') as file:
            lat_long_dict = pickle.load(file)
        print("Loaded data from pickle file.")
    else:
        # Initialize a dictionary to store the latitude and longitude
        lat_long_dict = {}

        # Open the CSV file and read its contents
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header line

            # Iterate through the rows in the CSV file
            for row in reader:
                latitude = float(row[0])  # Convert latitude to float
                longitude = float(row[1])  # Convert longitude to float
                depth = float(row[2])  # Convert depth to float

                # If depth is greater than -40, store the lat/long in the dictionary
                if depth > -40:
                    # Round and convert latitude and longitude to grid coordinates
                    rounded_lat = round_latitude(latitude)
                    rounded_long = round_longitude(longitude)

                    grid_y = latitude_to_grid(rounded_lat)
                    grid_x = longitude_to_grid(rounded_long)

                    # Create a unique key using grid coordinates
                    coordinate_key = f"{grid_x},{grid_y}"

                    # Store the depth in the dictionary using grid coordinates as the key
                    lat_long_dict[coordinate_key] = depth

        # After processing, save the data to a pickle file for future use
        with open(storage_file, 'wb') as file:
            pickle.dump(lat_long_dict, file)
        print("Data processed and saved to pickle file.")

    return lat_long_dict

# Retriever function: Get the depth for a specific grid coordinate
def retrieve_depth(grid_x, grid_y, storage_file="lat_long_data.pkl"):
    # Check if the data is available in the pickle file
    if os.path.exists(storage_file):
        with open(storage_file, 'rb') as file:
            lat_long_dict = pickle.load(file)
        
        # Create the key for the coordinate
        coordinate_key = f"{grid_x},{grid_y}"
        
        # Retrieve the depth for the specified coordinates
        if coordinate_key in lat_long_dict:
            return lat_long_dict[coordinate_key]
        else:
            return -50  # No depth data found for the coordinate
    else:
        print("No data found. Please process the CSV first.")
        return -50

# Specify the file path for the CSV
file_path = "output_depth_data.csv"  # Update with your CSV file path

# Process the CSV and get the dictionary of latitudes and longitudes
lat_long_dict = process_csv(file_path)

# Example: Access the depth value for a specific grid coordinate (grid_x, grid_y)
grid_x = 56
grid_y = 125   
depth_value = retrieve_depth(grid_x, grid_y)

if depth_value is not None:
    print(f"Depth at ({grid_x}, {grid_y}): {depth_value}")
else:
    print(f"No depth data found for grid coordinates ({grid_x}, {grid_y})")