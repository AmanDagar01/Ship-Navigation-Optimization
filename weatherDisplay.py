import pygame
import requests
import os
import threading
from dotenv import load_dotenv

# Initialize Pygame
pygame.init()

# Constants
WHITE = (255, 255, 255)
TEXT_COLOR = WHITE
BACKGROUND_COLOR = (30, 30, 30)
BORDER_COLOR = (128, 128, 128)
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLACK = (0, 0, 0)

# Fonts
def load_custom_font(size):
    return pygame.font.Font(None, size)  # Use a custom font path if desired.

# Load API Key
load_dotenv()
API_KEY = os.getenv("api_key")

# Global weather data storage
weather_data_departure = {}
weather_data_destination = {}

# Function to fetch weather data
def get_weather_data(latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)  # Set timeout to prevent blocking
        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": f"{data['main']['temp']}\u00b0C",
                "feels_like": f"{data['main']['feels_like']}\u00b0C",
                "humidity": f"{data['main']['humidity']}%",
                "wind_speed": f"{data['wind']['speed']} m/s",
                "description": data['weather'][0]['description'].capitalize()
            }
        else:
            return {"error": "Unable to fetch weather data"}
    except requests.RequestException:
        return {"error": "Request timed out"}

# Threaded weather data fetching
def fetch_weather_data(latitude, longitude, is_departure=True):
    global weather_data_departure, weather_data_destination
    weather_data = get_weather_data(latitude, longitude)
    if is_departure:
        weather_data_departure = weather_data
    else:
        weather_data_destination = weather_data

# Function to display weather for the first location (departure)
def weather(screen, latitude, longitude):
    global weather_data_departure

    # Start a thread if weather data is not yet fetched
    if not weather_data_departure:
        threading.Thread(target=fetch_weather_data, args=(latitude, longitude, True)).start()

    # Set up font and positioning
    weather_font = load_custom_font(24)
    label_font = load_custom_font(32)
    coord_font = load_custom_font(18)  # <-- NEW: Font for coordinates
    x_position = 700  # Aligned horizontally with destination box
    y_position = 480  # Same y-position as destination box

    # Box properties
    box_width, box_height = 240, 180

    # Text to display
    departure_label = label_font.render("Pref. Ship:", True, BLACK)
    screen.blit(departure_label, (x_position - 40, y_position - 160))

    parameters_label = label_font.render("Parameters:", True, BLACK)
    screen.blit(parameters_label, (x_position - 40, y_position - 100))

    departure_label = label_font.render("Departure", True, BLACK)
    screen.blit(departure_label, (x_position + (box_width // 2 - departure_label.get_width() // 2), y_position - 40))

    # Draw the weather box with a grey border
    pygame.draw.rect(screen, BORDER_COLOR, (x_position - 2, y_position - 1, box_width + 4, box_height + 4), border_radius=10)
    pygame.draw.rect(screen, BACKGROUND_COLOR, (x_position, y_position, box_width, box_height), border_radius=10)

    # <-- NEW: Render and display coordinates -->
    coord_text = f"Lat: {latitude:.3f}°, Lon: {longitude:.3f}°"
    coord_surface = coord_font.render(coord_text, True, TEXT_COLOR)
    screen.blit(coord_surface, (x_position + 10, y_position + 10))
    # <-- END OF NEW SECTION -->

    # Render weather data
    if "error" not in weather_data_departure:
        weather_text = [
            f"Temperature: {weather_data_departure.get('temperature', '...')}",
            f"Feels Like: {weather_data_departure.get('feels_like', '...')}",
            f"Humidity: {weather_data_departure.get('humidity', '...')}",
            f"Wind Speed: {weather_data_departure.get('wind_speed', '...')}",
            f"Description: {weather_data_departure.get('description', '...')}"
        ]
    else:
        weather_text = [weather_data_departure.get("error", "Loading...")]

    # Display weather information
    for i, text in enumerate(weather_text):
        label = weather_font.render(text, True, TEXT_COLOR)
        # <-- MODIFIED: Adjusted y-position from +20 to +35 to make space -->
        screen.blit(label, (x_position + 10, y_position + 35 + (i * 28))) # Adjusted spacing

# Function to display weather for the second location (destination)
def weatherTwo(screen, latitude, longitude):
    global weather_data_destination

    # Start a thread if weather data is not yet fetched
    if not weather_data_destination:
        threading.Thread(target=fetch_weather_data, args=(latitude, longitude, False)).start()

    # Set up font and positioning
    weather_font = load_custom_font(24)
    label_font = load_custom_font(32)
    coord_font = load_custom_font(18)  # <-- NEW: Font for coordinates
    x_position = 970  # Shift right by 240 pixels
    y_position = 480  # Adjust Y position for quadrant

    # Box properties
    box_width, box_height = 240, 180

    # Draw "Destination" label
    destination_label = label_font.render("Destination", True, BLACK)
    screen.blit(destination_label, (x_position + (box_width // 2 - destination_label.get_width() // 2), y_position - 40))

    # Draw the weather box with a grey border
    pygame.draw.rect(screen, BORDER_COLOR, (x_position - 2, y_position - 2, box_width + 4, box_height + 4), border_radius=10)
    pygame.draw.rect(screen, BACKGROUND_COLOR, (x_position, y_position, box_width, box_height), border_radius=10)

    # <-- NEW: Render and display coordinates -->
    coord_text = f"Lat: {latitude:.3f}°, Lon: {longitude:.3f}°"
    coord_surface = coord_font.render(coord_text, True, TEXT_COLOR)
    screen.blit(coord_surface, (x_position + 10, y_position + 10))
    # <-- END OF NEW SECTION -->

    # Render weather data
    if "error" not in weather_data_destination:
        weather_text = [
            f"Temperature: {weather_data_destination.get('temperature', '...')}",
            f"Feels Like: {weather_data_destination.get('feels_like', '...')}",
            f"Humidity: {weather_data_destination.get('humidity', '...')}",
            f"Wind Speed: {weather_data_destination.get('wind_speed', '...')}",
            f"Description: {weather_data_destination.get('description', '...')}"
        ]
    else:
        weather_text = [weather_data_destination.get("error", "Loading...")]

    # Display weather information
    for i, text in enumerate(weather_text):
        label = weather_font.render(text, True, TEXT_COLOR)
        # <-- MODIFIED: Adjusted y-position from +20 to +35 to make space -->
        screen.blit(label, (x_position + 10, y_position + 35 + (i * 28))) # Adjusted spacing

# Main program loop
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Weather Display")

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BACKGROUND_COLOR)

        # Display weather for departure and destination
        weather(screen, 28.7041, 77.1025)  # Example: Delhi
        weatherTwo(screen, 19.076, 72.8777)  # Example: Mumbai

        pygame.display.flip()
        clock.tick(60)  # Limit to 60 FPS

    pygame.quit()

# This check prevents the main() loop from running when imported by ActualMain.py
if __name__ == "__main__":
    main()