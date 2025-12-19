# Ship Navigation Algorithm

A sophisticated ship navigation system that optimizes maritime routes by considering multiple environmental and operational factors.

## 🌟 Features

- **Intelligent Path Planning**: Implements A* algorithm with multiple heuristic functions for optimal route calculation
- **Environmental Factors Integration**:
  - Wind direction and speed analysis
  - Ocean current patterns
  - Depth considerations
- **Multiple Optimization Modes**:
  - Fuel efficiency optimization
  - Speed optimization
  - Cargo-specific routing
  - Passenger-specific routing
- **Interactive UI**: 
  - Real-time visualization
  - Customizable route parameters
  - Dynamic map display

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Pygame
- Required Python packages (install via pip):
  ```bash
  pip install pygame numpy pandas
  ```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AmanDagar01/Ship-Navigation-Optimization.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python ActualMain.py
   ```

## 🗺️ Usage

1. Launch the application
2. Select optimization mode:
   - Fuel efficiency
   - Speed
   - Cargo routing
   - Passenger routing
3. Set start and end points on the map
4. View the calculated optimal route

## 📁 Project Structure

- `ActualMain.py`: Main application file
- `CoordConv.py`: Coordinate conversion utilities
- `Data_PreProcessing.py`: Data preprocessing modules
- `Data_Training.py`: Machine learning model training
- `depthCells.py`: Depth analysis module
- `fuelGenerator.py` & `fuelRetriever.py`: Fuel efficiency calculations
- `WindRetriever.py` & `Wind_generator.py`: Wind data processing
- `currentDirRetriever.py` & `currentDirGenerator.py`: Ocean current analysis
- `uielements.py`: UI components
- `weatherDisplay.py`: Weather visualization

## 🔧 Technical Details

The system uses a combination of:
- A* pathfinding algorithm
- Machine learning model - XGBoost for prediction
- Real-time environmental data processing
- Interactive visualization using Pygame

## 📊 Data Files

- `lat_long_data.pkl`: Geographic coordinate data
- `filtered_data_with_angle.pkl`: Processed angle data
- Various prediction files for different dates
- Feature importance visualizations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
