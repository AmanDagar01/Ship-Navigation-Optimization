import pickle
from Data_Training import WeatherHeuristicTrainer
from datetime import datetime

def save_heuristics(heuristics_dict, wind_deviation_dict, filename="heuristics_data.pkl"):
    """Save the heuristics and wind deviation dictionaries to a file using pickle"""
    with open(filename, "wb") as f:
        pickle.dump({"heuristics": heuristics_dict, "wind_deviation": wind_deviation_dict}, f)

def load_heuristics(filename="heuristics_data.pkl"):
    """Load the heuristics and wind deviation dictionaries from a pickle file"""
    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
            return data["heuristics"], data["wind_deviation"]
    except FileNotFoundError:
        print("No saved heuristics data found.")
        return None, None

def main():
    # Check if heuristics are already saved
    heuristics_dict, wind_deviation_dict = load_heuristics()

    if heuristics_dict is None or wind_deviation_dict is None:
        # If no saved data, process and generate heuristics
        trainer = WeatherHeuristicTrainer()
        # Modify the date range if the training files dates are changed
        start_date = datetime(2024, 8, 29)
        end_date = datetime(2024, 9, 3)
        heuristics_dict, wind_deviation_dict = trainer.process_all_days(start_date, end_date)
        
        # Save the new data
        save_heuristics(heuristics_dict, wind_deviation_dict)
        print("New heuristics data processed and saved.")

    # Print the stored heuristics dictionary
    print("Stored Heuristics Dictionary:")
    print(heuristics_dict)
    print("\nStored Wind Deviation Dictionary:")
    print(wind_deviation_dict)

if __name__ == "__main__":
    main()
