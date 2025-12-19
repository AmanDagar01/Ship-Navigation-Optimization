import pickle
import pandas as pd

class OceanCurrentRetriever:
    def __init__(self, pkl_file='filtered_data_with_angle.pkl'):
        """
        Initialize the retriever and load the data from the provided pickle file.

        Args:
        pkl_file (str): Path to the pickle file containing the ocean current data.
        """
        # Load the data once during initialization
        with open(pkl_file, 'rb') as f:
            self.data = pickle.load(f)

    def retrieve_angle(self, longitude, latitude):
        """
        Retrieve the Angle based on latitude and longitude.

        Args:
        longitude (float): Longitude value to search for.
        latitude (float): Latitude value to search for.

        Returns:
        float: The Angle value if found, otherwise returns 0.
        """
        # Filter the data based on the provided longitude and latitude
        result = self.data[(self.data['Longitude'] == longitude) & (self.data['Latitude'] == latitude)]

        # Check if data is found and return the Angle or default to 0
        if not result.empty:
            return result['Angle'].values[0]
        else:
            return 0  # Default value

# Instantiate the retriever
ocean_retriever = OceanCurrentRetriever()

# Example usage
longitude = 68.5
latitude = 5.0
angle = ocean_retriever.retrieve_angle(longitude, latitude)

print(f"Angle for Longitude: {longitude}, Latitude: {latitude}: {angle}°")
