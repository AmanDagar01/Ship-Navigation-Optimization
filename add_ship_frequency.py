import pandas as pd
import numpy as np
import random

def add_ship_frequency_column(input_file, output_file):
    """
    Read the CSV file and add a ship_frequency column with meaningful values based on weather and location.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to save the output CSV file with ship frequency
    """
    print(f"Reading data from {input_file}...")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    print(f"Original data shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Generate meaningful ship frequency based on weather and location factors
    ship_frequency = generate_meaningful_ship_frequency(df)
    
    # Add the new column at the end
    df['ship_frequency'] = ship_frequency
    
    print(f"Added ship_frequency column with values ranging from {ship_frequency.min()} to {ship_frequency.max()}")
    print(f"Mean ship frequency: {ship_frequency.mean():.2f}")
    print(f"Standard deviation: {ship_frequency.std():.2f}")
    
    # Save the modified data
    df.to_csv(output_file, index=False)
    print(f"Saved modified data to {output_file}")
    print(f"Final data shape: {df.shape}")
    
    # Show correlation analysis
    print("\n=== CORRELATION ANALYSIS ===")
    feature_cols = ['Longitude', 'Latitude', 'U_Current', 'V_Current', 
                    'temperature_2m_min', 'temperature_2m_max', 'pressure_msl', 
                    'wind_direction_10m_dominant', 'precipitation_probability_max', 'TP']
    
    for col in feature_cols:
        if col in df.columns:
            corr = df[col].corr(df['ship_frequency'])
            print(f"{col}: {corr:.4f}")
    
    return df

def generate_meaningful_ship_frequency(df):
    """
    Generate meaningful ship frequency based on weather and location factors.
    The output is normalized to 0-50 using min-max scaling.
    """
    # Create separate components for each feature to ensure balanced importance
    precip_component = -5.0 * df['precipitation_probability_max']
    current_component = -4.0 * np.sqrt(df['U_Current']**2 + df['V_Current']**2)
    temp_range_component = -3.0 * (df['temperature_2m_max'] - df['temperature_2m_min'])
    pressure_component = 3.0 * (df['pressure_msl'] - 1013)
    wind_component = -4.0 * df['wind_direction_10m_dominant']
    tp_component = 2.0 * df['TP']
    temp_min_component = 2.0 * df['temperature_2m_min']
    temp_max_component = 2.0 * df['temperature_2m_max']
    u_current_component = 2.0 * df['U_Current']
    v_current_component = 2.0 * df['V_Current']
    
    score = (precip_component + current_component + temp_range_component + 
             pressure_component + wind_component + tp_component + 
             temp_min_component + temp_max_component + u_current_component + v_current_component)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        day_of_week = df['Date'].dt.dayofweek
        score += np.where(day_of_week >= 5, -10, 0)
    # Add noise
    score += np.random.normal(0, 35, len(df))
    # Min-max normalization to 0-50
    min_score = score.min()
    max_score = score.max()
    ship_frequency = 50 * (score - min_score) / (max_score - min_score)
    ship_frequency = np.clip(np.round(ship_frequency), 0, 50).astype(int)
    return ship_frequency

if __name__ == "__main__":
    input_file = "merged_data_20241211_20241216.csv"
    output_file = "merged_data_with_ship_frequency.csv"
    
    try:
        df = add_ship_frequency_column(input_file, output_file)
        print(f"\nSuccessfully generated meaningful ship_frequency values in {output_file}")
        print("The ship frequency now correlates with weather and location factors!")
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
    except Exception as e:
        print(f"Error: {e}") 