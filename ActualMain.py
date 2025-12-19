import pygame  #It draws all the graphics, handles mouse clicks
import sys     #used properly to shut down your application (like sys.exit())
import math    #It's used for all the distance and angle calculations
from queue import PriorityQueue #Brain behind A* it's a special to-do list that always knows the "best" grid square to check next, which makes the pathfinder super efficient
import uielements      
from uielements import horizontal_buttons
import weatherDisplay
from CoordConv import grid_to_latitude, grid_to_longitude, latitude_to_grid, longitude_to_grid, round_longitude, round_latitude
import storage
from heuristicRetriever import HeuristicRetriever
from intro_animation import play_intro_animation
import requests
import WindRetriever
import currentDirRetriever
from depthCells import retrieve_depth
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'navigation_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ShipNavigation')


class NavigationException(Exception):
    """Base exception for navigation errors"""
    pass

class PathNotFoundException(NavigationException):
    """Raised when no valid path exists"""
    pass

class InvalidCoordinatesException(NavigationException):
    """Raised when coordinates are invalid"""
    pass

class MapConfig:
    """Configuration for map display"""
    GRID_SIZE = 4
    GRID_WIDTH = 550
    GRID_HEIGHT = 600
    MAP_POSITION = (100, 70)
    
class Colors:
    """Color constants"""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 200)
    GREEN = (0, 150, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    GRAY = (128, 128, 128)
    DARK_GRAY = (50, 50, 50)
    LIGHT_BLUE = (100, 149, 237)
    PURPLE = (128, 0, 128)

class ShipProfile:
    """Ship profile configurations with different characteristics"""
    
    # Speed in knots for different ship types
    CARGO_SPEED = 12.0
    PASSENGER_SPEED = 18.0
    YACHT_SPEED = 20.0
    
    # Fuel consumption rates (tons per nautical mile)
    CARGO_FUEL_RATE = 0.15
    PASSENGER_FUEL_RATE = 0.25
    YACHT_FUEL_RATE = 0.35
    
    # Comfort factors (arbitrary scale 1-10)
    CARGO_COMFORT = 3
    PASSENGER_COMFORT = 8
    YACHT_COMFORT = 10
    
    @staticmethod
    def get_speed(is_cargo: bool, is_passenger: bool) -> float:
        if is_cargo:
            return ShipProfile.CARGO_SPEED
        elif is_passenger:
            return ShipProfile.PASSENGER_SPEED
        else:
            return ShipProfile.YACHT_SPEED
    
    @staticmethod
    def get_fuel_rate(is_cargo: bool, is_passenger: bool) -> float:
        if is_cargo:
            return ShipProfile.CARGO_FUEL_RATE
        elif is_passenger:
            return ShipProfile.PASSENGER_FUEL_RATE
        else:
            return ShipProfile.YACHT_FUEL_RATE
    
    @staticmethod
    def get_comfort(is_cargo: bool, is_passenger: bool) -> int:
        if is_cargo:
            return ShipProfile.CARGO_COMFORT
        elif is_passenger:
            return ShipProfile.PASSENGER_COMFORT
        else:
            return ShipProfile.YACHT_COMFORT
    
    @staticmethod
    def get_profile_name(is_cargo: bool, is_passenger: bool) -> str:
        if is_cargo:
            return "Cargo Ship"
        elif is_passenger:
            return "Passenger Ship"
        else:
            return "Yacht/Individual"

class AssetManager:
    """Manages and caches all game assets for better performance"""
    
    def __init__(self):
        logger.info("Loading assets...")
        try:
            self.india_map = pygame.image.load("India.jpeg")
            self.india_map = pygame.transform.scale(self.india_map, (MapConfig.GRID_WIDTH, MapConfig.GRID_HEIGHT))
            
            self.india_fore = pygame.image.load("IndiaFore3.png")
            self.india_fore = pygame.transform.scale(self.india_fore, (MapConfig.GRID_WIDTH, MapConfig.GRID_HEIGHT))
            
            self.background_image = pygame.image.load("background.jpg")
            
            logger.info("✓ Assets loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load assets: {e}")
            raise
    
    def draw_background(self, screen, position):
        screen.blit(self.india_map, position)
    
    def draw_foreground(self, screen, position):
        screen.blit(self.india_fore, position)
    
    def scale_background(self, screen_width, screen_height):
        return pygame.transform.scale(self.background_image, (screen_width, screen_height))

class GridRenderer:
    """Pre-renders the grid for better performance"""
    
    def __init__(self, grid_size, width, height):
        logger.info("Pre-rendering grid...")
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._render_grid(grid_size, width, height)
    
    def _render_grid(self, size, width, height):
        for x in range(0, width, size):
            pygame.draw.line(self.surface, Colors.BLUE, (x, 0), (x, height))
        
        for y in range(0, height, size):
            if y > 280:
                pygame.draw.line(self.surface, Colors.BLUE, (0, y), (width, y))
    
    def draw(self, screen, position):
        screen.blit(self.surface, position)

class CoordinateValidator:
    """Validates and sanitizes coordinate inputs"""
    
    @staticmethod
    def parse_coordinate(text: str) -> Tuple[float, str]:
        """
        Parse coordinate string that may include N/S/E/W and degree symbols
        Returns: (value, error_message)
        """
        if not text or not text.strip():
            return 0.0, "Empty coordinate"
        
        try:
            # Remove spaces
            text = text.strip().upper()
            
            # Track if negative
            multiplier = 1.0
            
            # Check for direction letters
            if 'S' in text or 'W' in text:
                multiplier = -1.0
            
            # Remove direction letters and degree symbols
            cleaned = text.replace('N', '').replace('S', '').replace('E', '').replace('W', '')
            cleaned = cleaned.replace('°', '').replace("'", '').replace('"', '')
            cleaned = cleaned.strip()
            
            # Convert to float
            value = float(cleaned) * multiplier
            return value, ""
            
        except ValueError:
            return 0.0, f"Invalid format: {text}"
    
    @staticmethod
    def validate_coordinates(lon: float, lat: float) -> Tuple[bool, str]:
        """
        Validate geographical coordinates with EXPANDED input bounds
        Coordinates outside grid range will be clamped but accepted
        Returns: (is_valid, error_message)
        """
        # Basic range check
        if not (-180 <= lon <= 180):
            return False, f"Longitude {lon:.2f}° out of range [-180°, 180°]"
        if not (-90 <= lat <= 90):
            return False, f"Latitude {lat:.2f}° out of range [-90°, 90°]"
        
        # EXPANDED input bounds
        valid_lon_range = (60 <= lon <= 100)
        valid_lat_range = (0 <= lat <= 40)

        # Check for valid coordinates
        if valid_lon_range and valid_lat_range:
            return True, ""

        # Check for *swapped* coordinates
        # (e.g., user entered lat in lon box and lon in lat box)
        swapped_lon_range = (60 <= lat <= 100) # Check if lat is in lon's range
        swapped_lat_range = (0 <= lon <= 40)   # Check if lon is in lat's range

        if swapped_lon_range and swapped_lat_range:
            return False, f"Possible swap? Lat/Lon seem reversed. Try Lon: {lat:.2f}, Lat: {lon:.2f}"

        # Original error message
        if not (valid_lon_range and valid_lat_range):
            return False, f"Coordinates ({lon:.2f}°E, {lat:.2f}°N) outside acceptable region (60-100°E, 0-40°N)"
        
        return True, ""
    
    @staticmethod
    def sanitize_coordinate_input(text: str) -> str:
        """Clean coordinate input string (legacy method)"""
        cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
        
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        
        if cleaned.count('-') > 1:
            cleaned = '-' + cleaned.replace('-', '')
        
        return cleaned

class ErrorDisplay:
    """Displays error messages on screen"""
    
    def __init__(self):
        self.message = ""
        self.timestamp = 0
        self.duration = 5000 # Increased duration for readability
        self.font = None
    
    def show_error(self, message: str):
        self.message = message
        self.timestamp = pygame.time.get_ticks()
        logger.error(message)
    
    def draw(self, screen):
        if not self.message:
            return
        
        current_time = pygame.time.get_ticks()
        if current_time - self.timestamp > self.duration:
            self.message = ""
            return
        
        if not self.font:
            self.font = pygame.font.Font(None, 28) # Slightly larger font
        
        text_surface = self.font.render(self.message, True, Colors.RED)
        text_rect = text_surface.get_rect(center=(screen.get_width()//2, 50))
        
        # Ensure text fits on screen, wrap if necessary (simple wrap)
        if text_rect.width > screen.get_width() - 40:
            # This is a simple implementation. For full wrapping, it's more complex.
            # For now, we'll just show the error on one line.
            # A better solution would be to split the message into multiple lines.
            pass

        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(screen, Colors.BLACK, bg_rect)
        pygame.draw.rect(screen, Colors.RED, bg_rect, 3)
        
        screen.blit(text_surface, text_rect)

class ETACalculator:
    """Calculate and display estimated arrival time"""
    
    def __init__(self):
        self.departure_time = None
        self.arrival_time = None
        self.font = pygame.font.Font(None, 20)
    
    def set_departure_time(self, custom_time=None):
        if custom_time:
            self.departure_time = custom_time
        else:
            self.departure_time = datetime.now()
    
    def calculate_eta(self, travel_hours):
        if self.departure_time:
            self.arrival_time = self.departure_time + timedelta(hours=travel_hours)
    
    def draw_eta_panel(self, screen):
        if not self.departure_time or not self.arrival_time:
            return
        
        # Positioned at bottom left, next to route info
        panel_x = 420
        panel_y = screen.get_height() - 200
        panel_width = 280
        panel_height = 90
        
        # Background
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        screen.blit(bg_surface, (panel_x, panel_y))
        pygame.draw.rect(screen, Colors.WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title_font = pygame.font.Font(None, 22)
        title = title_font.render("Journey Timeline", True, Colors.YELLOW)
        screen.blit(title, (panel_x + 10, panel_y + 5))
        
        # Content
        content_font = pygame.font.Font(None, 18)
        
        # Departure
        dep_text = f"Depart: {self.departure_time.strftime('%d %b, %H:%M')}"
        dep_surface = content_font.render(dep_text, True, Colors.GREEN)
        screen.blit(dep_surface, (panel_x + 10, panel_y + 30))
        
        # Arrival
        arr_text = f"Arrive: {self.arrival_time.strftime('%d %b, %H:%M')}"
        arr_surface = content_font.render(arr_text, True, Colors.ORANGE)
        screen.blit(arr_surface, (panel_x + 10, panel_y + 50))
        
        # Time remaining
        now = datetime.now()
        if self.arrival_time > now:
            remaining = self.arrival_time - now
            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            remaining_text = f"ETA: {days}d {hours}h {minutes}m"
            remaining_surface = content_font.render(remaining_text, True, Colors.LIGHT_BLUE)
            screen.blit(remaining_surface, (panel_x + 10, panel_y + 70))

class TripCostCalculator:
    """Calculate comprehensive trip costs"""
    
    def __init__(self):
        self.fuel_price_per_ton = 500  # USD
        self.crew_cost_per_day = 2000  # USD
        self.port_fees = 5000  # USD
        self.insurance_per_nm = 2  # USD
        self.font = pygame.font.Font(None, 20)
        self.costs = None
    
    def calculate_total_cost(self, distance_nm, travel_hours, fuel_tons):
        fuel_cost = fuel_tons * self.fuel_price_per_ton
        crew_cost = (travel_hours / 24) * self.crew_cost_per_day
        insurance_cost = distance_nm * self.insurance_per_nm
        
        self.costs = {
            'Fuel': fuel_cost,
            'Crew': crew_cost,
            'Port Fees': self.port_fees,
            'Insurance': insurance_cost,
            'Total': fuel_cost + crew_cost + self.port_fees + insurance_cost
        }
        return self.costs
    
    def draw_cost_breakdown(self, screen):
        if not self.costs:
            return
        
        # Positioned at bottom middle
        panel_x = 710
        panel_y = screen.get_height() - 200
        panel_width = 280
        panel_height = 180
        
        # Background
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        screen.blit(bg_surface, (panel_x, panel_y))
        pygame.draw.rect(screen, Colors.WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title_font = pygame.font.Font(None, 22)
        title = title_font.render("Cost Breakdown (USD)", True, Colors.YELLOW)
        screen.blit(title, (panel_x + 10, panel_y + 5))
        
        # Individual costs
        content_font = pygame.font.Font(None, 18)
        y = panel_y + 30
        for label, amount in self.costs.items():
            if label != 'Total':
                text = f"{label}: ${amount:,.0f}"
                surface = content_font.render(text, True, Colors.WHITE)
                screen.blit(surface, (panel_x + 15, y))
                y += 25
        
        # Separator line
        pygame.draw.line(screen, Colors.WHITE, (panel_x + 10, y + 5), (panel_x + panel_width - 10, y + 5), 1)
        
        # Total (highlighted)
        total_font = pygame.font.Font(None, 20)
        total_text = f"TOTAL: ${self.costs['Total']:,.0f}"
        total_surface = total_font.render(total_text, True, Colors.GREEN)
        screen.blit(total_surface, (panel_x + 15, y + 10))

class RouteExporter:
    """Export routes in various formats"""
    
    @staticmethod
    def export_to_gpx(path, filename):
        """Export as GPX for GPS devices"""
        gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="ShipNavigation">
  <trk>
    <name>Ship Route</name>
    <trkseg>
'''
        for x, y in path:
            lon = grid_to_longitude(x)
            lat = grid_to_latitude(y)
            gpx_content += f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"/>\n'
        
        gpx_content += '''    </trkseg>
  </trk>
</gpx>'''
        
        with open(filename, 'w') as f:
            f.write(gpx_content)
        logger.info(f"Exported route to GPX: {filename}")
    
    @staticmethod
    def export_to_kml(path, filename):
        """Export as KML for Google Earth"""
        kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Ship Route</name>
    <Placemark>
      <name>Route Path</name>
      <LineString>
        <coordinates>
'''
        for x, y in path:
            lon = grid_to_longitude(x)
            lat = grid_to_latitude(y)
            kml_content += f'          {lon:.6f},{lat:.6f},0\n'
        
        kml_content += '''        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>'''
        
        with open(filename, 'w') as f:
            f.write(kml_content)
        logger.info(f"Exported route to KML: {filename}")
    
    @staticmethod
    def export_to_csv(path, filename):
        """Export as CSV"""
        with open(filename, 'w') as f:
            f.write("Waypoint,Latitude,Longitude,Grid_X,Grid_Y\n")
            for i, (x, y) in enumerate(path, 1):
                lon = grid_to_longitude(x)
                lat = grid_to_latitude(y)
                f.write(f"WP{i},{lat:.6f},{lon:.6f},{x},{y}\n")
        logger.info(f"Exported route to CSV: {filename}")

class PathInfoPanel:
    """Displays information about the calculated path"""
    
    def __init__(self):
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 28)
        self.path = None
        self.distance_nm = 0
        self.estimated_time = 0
        self.waypoints = 0
        self.ship_speed = 15.0
        self.fuel_consumed = 0
        self.fuel_rate = 0.15
        self.profile_name = "Standard"
        self.is_cargo = False
        self.is_passenger = False
    
    def set_path(self, path: List[Tuple[int, int]], is_cargo: bool = False, is_passenger: bool = False):
        self.path = path
        self.waypoints = len(path)
        self.is_cargo = is_cargo
        self.is_passenger = is_passenger
        
        self.ship_speed = ShipProfile.get_speed(is_cargo, is_passenger)
        self.fuel_rate = ShipProfile.get_fuel_rate(is_cargo, is_passenger)
        self.profile_name = ShipProfile.get_profile_name(is_cargo, is_passenger)
        
        self.distance_nm = self._calculate_distance()
        self.estimated_time = self._calculate_time()
        self.fuel_consumed = self._calculate_fuel()
    
    def _calculate_distance(self) -> float:
        if not self.path or len(self.path) < 2:
            return 0.0
        
        total = 0
        for i in range(len(self.path) - 1):
            lon1 = grid_to_longitude(self.path[i][0])
            lat1 = grid_to_latitude(self.path[i][1])
            lon2 = grid_to_longitude(self.path[i+1][0])
            lat2 = grid_to_latitude(self.path[i+1][1])
            total += self._haversine(lat1, lon1, lat2, lon2)
        return total
    
    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        R = 3440.065
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def _calculate_time(self) -> float:
        return self.distance_nm / self.ship_speed if self.ship_speed > 0 else 0
    
    def _calculate_fuel(self) -> float:
        return self.distance_nm * self.fuel_rate
    
    def draw(self, screen):
        if not self.path:
            return
        
        # Positioned at bottom left corner
        panel_x = 10
        panel_y = screen.get_height() - 200
        panel_width = 400
        panel_height = 180
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))
        screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(screen, Colors.WHITE, panel_rect, 2)
        
        title = self.title_font.render(f"Route - {self.profile_name}", True, Colors.YELLOW)
        screen.blit(title, (panel_x + 10, panel_y + 5))
        
        info_texts = [
            f"Distance: {self.distance_nm:.1f} nm",
            f"Time: {self.estimated_time:.1f} hrs",
            f"Speed: {self.ship_speed:.1f} knots",
            f"Fuel: ~{self.fuel_consumed:.1f} tons",
            f"Waypoints: {self.waypoints}"
        ]
        
        y_offset = panel_y + 35
        for text in info_texts:
            surface = self.font.render(text, True, Colors.WHITE)
            screen.blit(surface, (panel_x + 15, y_offset))
            y_offset += 28

class ProgressBar:
    """Shows progress during pathfinding"""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.progress = 0.0
        self.active = False
        self.font = pygame.font.Font(None, 24)
    
    def start(self):
        self.active = True
        self.progress = 0.0
    
    def update(self, current, total):
        self.progress = current / total if total > 0 else 0
    
    def stop(self):
        self.active = False
    
    def draw(self, screen):
        if not self.active:
            return
        
        pygame.draw.rect(screen, Colors.DARK_GRAY, self.rect)
        pygame.draw.rect(screen, Colors.WHITE, self.rect, 2)
        
        progress_width = int(self.rect.width * self.progress)
        progress_rect = pygame.Rect(self.rect.x, self.rect.y, progress_width, self.rect.height)
        pygame.draw.rect(screen, Colors.GREEN, progress_rect)
        
        text = self.font.render(f"Finding path... {self.progress*100:.0f}%", True, Colors.WHITE)
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.centery))
        screen.blit(text, text_rect)

class RouteManager:
    """Saves and loads routes"""
    
    def __init__(self, save_dir="saved_routes"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    def save_route(self, path, start, end, metadata=None) -> str:
        try:
            route_data = {
                "timestamp": datetime.now().isoformat(),
                "start": {
                    "grid": start,
                    "coordinates": {
                        "longitude": grid_to_longitude(start[0]),
                        "latitude": grid_to_latitude(start[1])
                    }
                },
                "end": {
                    "grid": end,
                    "coordinates": {
                        "longitude": grid_to_longitude(end[0]),
                        "latitude": grid_to_latitude(end[1])
                    }
                },
                "path": path,
                "metadata": metadata or {},
                "waypoints": len(path)
            }
            
            filename = f"{self.save_dir}/route_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(filename, 'w') as f:
                json.dump(route_data, f, indent=2)
            
            logger.info(f"Route saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save route: {e}")
            return ""
    
    def load_route(self, filename: str) -> Optional[dict]:
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load route: {e}")
            return None
    
    def list_routes(self) -> List[str]:
        try:
            return sorted([f for f in os.listdir(self.save_dir) if f.endswith('.json')], reverse=True)
        except Exception as e:
            logger.error(f"Failed to list routes: {e}")
            return []

class PerformanceMonitor:
    """Monitors and displays performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'pathfinding_time': [],
            'nodes_explored': [],
            'cache_hits': 0,
            'cache_misses': 0,
            'frame_times': []
        }
        self.font = pygame.font.Font(None, 20)
        self.show_debug = False
    
    def record_pathfinding(self, duration, nodes_explored):
        self.metrics['pathfinding_time'].append(duration)
        self.metrics['nodes_explored'].append(nodes_explored)
    
    def record_cache_access(self, hit):
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def record_frame_time(self, duration):
        self.metrics['frame_times'].append(duration)
        if len(self.metrics['frame_times']) > 60:
            self.metrics['frame_times'].pop(0)
    
    def get_average_fps(self):
        if not self.metrics['frame_times']:
            return 0
        avg_frame_time = sum(self.metrics['frame_times']) / len(self.metrics['frame_times'])
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0
    
    def get_cache_hit_rate(self):
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        return self.metrics['cache_hits'] / total if total > 0 else 0
    
    def toggle_debug(self):
        self.show_debug = not self.show_debug
    
    def draw_debug_overlay(self, screen):
        if not self.show_debug:
            return
        
        y = 10
        stats = [
            f"FPS: {self.get_average_fps():.1f}",
            f"Cache Hit Rate: {self.get_cache_hit_rate()*100:.1f}%",
        ]
        
        if self.metrics['pathfinding_time']:
            recent_times = self.metrics['pathfinding_time'][-5:]
            avg_time = sum(recent_times) / len(recent_times)
            stats.append(f"Avg Pathfinding: {avg_time:.3f}s")
        
        max_width = max([self.font.size(s)[0] for s in stats]) + 20
        bg_rect = pygame.Rect(5, 5, max_width, len(stats) * 25 + 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))
        screen.blit(bg_surface, bg_rect)
        
        for stat in stats:
            text = self.font.render(stat, True, Colors.YELLOW)
            screen.blit(text, (10, y))
            y += 25

class KeyboardShortcutsHelp:
    """Display keyboard shortcuts"""
    
    def __init__(self):
        self.show_help = False
        self.font = pygame.font.Font(None, 20)
    
    def toggle(self):
        self.show_help = not self.show_help
    
    def draw(self, screen):
        if not self.show_help:
            return
        
        shortcuts = [
            "Keyboard Shortcuts:",
            "F1 - Toggle Performance Stats",
            "F2 - Toggle This Help",
            "Ctrl+S - Save Route",
            "Ctrl+R - Reset Selection",
            "Ctrl+E - Export Route (GPX)",
            "Ctrl+K - Export Route (KML)",
            "ESC - Exit Application"
        ]
        
        panel_width = 350
        panel_height = len(shortcuts) * 25 + 20
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2
        
        # Background
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 230))
        screen.blit(bg_surface, (panel_x, panel_y))
        pygame.draw.rect(screen, Colors.YELLOW, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Draw shortcuts
        y = panel_y + 10
        for i, shortcut in enumerate(shortcuts):
            color = Colors.YELLOW if i == 0 else Colors.WHITE
            text = self.font.render(shortcut, True, color)
            screen.blit(text, (panel_x + 15, y))
            y += 25

pygame.init()
clock = pygame.time.Clock()

heuristic_retriever = HeuristicRetriever()
intro_video_path = "./Countdown1.mp4"

info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Ship Navigation System - Enhanced")

try:
    play_intro_animation(screen, intro_video_path, screen_width, screen_height)
except Exception as e:
    logger.warning(f"Intro animation failed: {e}")

# Initialize all components
asset_manager = AssetManager()
background_image = asset_manager.scale_background(screen_width, screen_height)
grid_renderer = GridRenderer(MapConfig.GRID_SIZE, MapConfig.GRID_WIDTH, MapConfig.GRID_HEIGHT)
error_display = ErrorDisplay()
path_info_panel = PathInfoPanel()
progress_bar = ProgressBar(screen_width//2 - 200, screen_height//2 - 25, 400, 50)
route_manager = RouteManager()
perf_monitor = PerformanceMonitor()
eta_calculator = ETACalculator()
cost_calculator = TripCostCalculator()
keyboard_help = KeyboardShortcutsHelp()

NORTH = (40, 9)
SOUTH = (49, 135)
WEST = (16, 71)
EAST = (121, 51)

wind_cache = {}
current_cache = {}
heuristic_cache = {}
depth_cache = {}


def is_aligned_with_wind(long: int, lat: int, dx: int, dy: int) -> int:
    cache_key = (long, lat)
    if cache_key in wind_cache:
        wind_direction = wind_cache[cache_key]
        perf_monitor.record_cache_access(True)
    else:
        perf_monitor.record_cache_access(False)
        geo_latitude = round_latitude(grid_to_latitude(lat))
        geo_longitude = round_longitude(grid_to_longitude(long))
        
        retriever = WindRetriever.WindDirectionRetriever()
        wind_direction = retriever.retrieve_wind_direction(geo_longitude, geo_latitude)
        wind_cache[cache_key] = wind_direction
    
    movement_angle = round(math.degrees(math.atan2(dy, dx))) % 360
    
    lower_bound = (wind_direction - 25) % 360
    upper_bound = (wind_direction + 25) % 360
    
    if (lower_bound <= movement_angle <= upper_bound) or \
       (lower_bound > upper_bound and (movement_angle >= lower_bound or movement_angle <= upper_bound)):
        return 1
    return 0


def is_aligned_with_current(long: int, lat: int, dx: int, dy: int) -> int:
    cache_key = (long, lat)
    if cache_key in current_cache:
        current_direction = current_cache[cache_key]
        perf_monitor.record_cache_access(True)
    else:
        perf_monitor.record_cache_access(False)
        geo_latitude = round_latitude(grid_to_latitude(lat))
        geo_longitude = round_longitude(grid_to_longitude(long))
        
        retriever = currentDirRetriever.OceanCurrentRetriever()
        current_direction = retriever.retrieve_angle(geo_longitude, geo_latitude)
        current_cache[cache_key] = current_direction
    
    movement_angle = round(math.degrees(math.atan2(dy, dx))) % 360
    
    lower_bound = (current_direction - 25) % 360
    upper_bound = (current_direction + 25) % 360
    
    if (lower_bound <= movement_angle <= upper_bound) or \
       (lower_bound > upper_bound and (movement_angle >= lower_bound or movement_angle <= upper_bound)):
        return 1
    return 0


def euclidean(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def h_heuristic(node: Tuple[int, int]) -> float:
    if node in heuristic_cache:
        perf_monitor.record_cache_access(True)
        return heuristic_cache[node]
    
    perf_monitor.record_cache_access(False)
    grid_x, grid_y = node
    latitude = round_latitude(grid_to_latitude(grid_y))
    longitude = round_longitude(grid_to_longitude(grid_x))
    
    heuristic_value = heuristic_retriever.get_heuristic_value(latitude, longitude, "heuristics_data.pkl")
    heuristic_cache[node] = heuristic_value
    return heuristic_value


def calculate_fscore(
    g_score: float,
    current: Tuple[int, int],
    neighbor: Tuple[int, int],
    end: Tuple[int, int],
    is_first_box_green: bool,
    is_second_box_green: bool,
    wind_alignment: int,
    current_alignment: int
) -> float:
    f_score = 0
    
    if is_first_box_green:
        if horizontal_buttons[0]:
            f_score = 0.4 * g_score + 0.2 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[1]:
            f_score = 0.3 * g_score + 0.7 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[2]:
            f_score = 0.3 * g_score + 0.2 * euclidean(neighbor, end) + 1 * h_heuristic(neighbor)
        else:
            f_score = 0.3 * g_score + 0.7 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
    
    elif is_second_box_green:
        if horizontal_buttons[0]:
            f_score = 0.4 * g_score + 0.2 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[1]:
            f_score = 0.3 * g_score + 0.7 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[2]:
            f_score = 0.3 * g_score + 0.2 * euclidean(neighbor, end) + 1 * h_heuristic(neighbor)
        else:
            f_score = 0.3 * g_score + 0.2 * euclidean(neighbor, end) + 1 * h_heuristic(neighbor)
    
    else:
        if horizontal_buttons[0]:
            f_score = 0.4 * g_score + 0.2 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[1]:
            f_score = 0.3 * g_score + 0.7 * euclidean(neighbor, end) + 0.1 * h_heuristic(neighbor)
        elif horizontal_buttons[2]:
            f_score = 0.3 * g_score + 0.2 * euclidean(neighbor, end) + 1 * h_heuristic(neighbor)
        else:
            f_score = g_score + euclidean(neighbor, end)
    
    if wind_alignment == 1:
        f_score *= 0.9
    if current_alignment == 1:
        f_score *= 0.9
    
    return f_score


blocks = storage.Backup_black_cells


def get_neighbors(position: Tuple[int, int]) -> List[Tuple[Tuple[int, int], int, int]]:
    neighbors = []
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    
    max_x = MapConfig.GRID_WIDTH // MapConfig.GRID_SIZE
    max_y = MapConfig.GRID_HEIGHT // MapConfig.GRID_SIZE
    
    for dx, dy in directions:
        nx, ny = position[0] + dx, position[1] + dy
        
        if 0 <= nx < max_x and 0 <= ny < max_y:
            depth_key = (nx, ny)
            if depth_key not in depth_cache:
                depth_cache[depth_key] = retrieve_depth(nx, ny)
                perf_monitor.record_cache_access(False)
            else:
                perf_monitor.record_cache_access(True)
            
            if not is_black_pixel(nx, ny) and (nx, ny) not in blocks and depth_cache[depth_key] < -48:
                wind_alignment = is_aligned_with_wind(position[0]+dx, position[1]+dy, dx, dy)
                current_alignment = is_aligned_with_current(position[0]+dx, position[1]+dy, dx, dy)
                neighbors.append(((nx, ny), wind_alignment, current_alignment))
    
    return neighbors


def is_black_pixel(x: int, y: int) -> bool:
    pixel_x = MapConfig.MAP_POSITION[0] + x * MapConfig.GRID_SIZE + MapConfig.GRID_SIZE // 2
    pixel_y = MapConfig.MAP_POSITION[1] + y * MapConfig.GRID_SIZE + MapConfig.GRID_SIZE // 2
    
    if 0 <= pixel_x < screen_width and 0 <= pixel_y < screen_height:
        pixel_color = screen.get_at((pixel_x, pixel_y))
        return pixel_color == Colors.BLACK
    return True


def a_star(
    start: Tuple[int, int],
    end: Tuple[int, int],
    cargo: bool,
    passenger: bool,
    screen_ref,
    progress_bar_ref
) -> Tuple[Optional[List[Tuple[int, int]]], List[Tuple[int, int]]]:
    logger.info(f"Starting A* from {start} to {end}")
    start_time = pygame.time.get_ticks()
    
    open_set = PriorityQueue()
    counter = 0
    open_set.put((0, counter, start))
    counter += 1
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: euclidean(start, end)}
    
    closed_set = set()
    explored_nodes = []
    
    is_first_box_green = bool(cargo)
    is_second_box_green = bool(passenger)
    
    logger.info(f"Profile - Cargo: {is_first_box_green}, Passenger: {is_second_box_green}")
    logger.info(f"Optimizations - Fuel: {horizontal_buttons[0]}, Speed: {horizontal_buttons[1]}, Comfort: {horizontal_buttons[2]}")
    
    visualization_counter = 0
    max_nodes = 10000
    
    progress_bar_ref.start()
    
    while not open_set.empty():
        _, _, current = open_set.get()
        
        if current in closed_set:
            continue
        
        closed_set.add(current)
        explored_nodes.append(current)
        
        progress_bar_ref.update(len(explored_nodes), min(len(explored_nodes) + 100, max_nodes))
        
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            
            screen_ref.blit(background_image, (0, 0))
            asset_manager.draw_background(screen_ref, MapConfig.MAP_POSITION)
            grid_renderer.draw(screen_ref, MapConfig.MAP_POSITION)
            
            for cell in path:
                pygame.draw.rect(screen_ref, Colors.GREEN,
                                (MapConfig.MAP_POSITION[0] + cell[0] * MapConfig.GRID_SIZE,
                                 MapConfig.MAP_POSITION[1] + cell[1] * MapConfig.GRID_SIZE,
                                 MapConfig.GRID_SIZE, MapConfig.GRID_SIZE))
            
            asset_manager.draw_foreground(screen_ref, MapConfig.MAP_POSITION)
            
            path_info_panel.set_path(path, is_first_box_green, is_second_box_green)
            path_info_panel.draw(screen_ref)
            
            # Calculate ETA
            eta_calculator.set_departure_time()
            eta_calculator.calculate_eta(path_info_panel.estimated_time)
            eta_calculator.draw_eta_panel(screen_ref)
            
            # Calculate costs
            cost_calculator.calculate_total_cost(
                path_info_panel.distance_nm,
                path_info_panel.estimated_time,
                path_info_panel.fuel_consumed
            )
            cost_calculator.draw_cost_breakdown(screen_ref)
            
            
            pygame.display.flip()
            
            end_time = pygame.time.get_ticks()
            duration = (end_time - start_time) / 1000.0
            logger.info(f"✓ Path found! Length: {len(path)}, Explored: {len(explored_nodes)}, Time: {duration:.2f}s")
            perf_monitor.record_pathfinding(duration, len(explored_nodes))
            
            progress_bar_ref.stop()
            pygame.time.delay(3000)
            
            return path, explored_nodes
        
        visualization_counter += 1
        if visualization_counter % 10 == 0:
            screen_ref.blit(background_image, (0, 0))
            asset_manager.draw_background(screen_ref, MapConfig.MAP_POSITION)
            grid_renderer.draw(screen_ref, MapConfig.MAP_POSITION)
            
            for node in explored_nodes:
                pygame.draw.rect(screen_ref, Colors.RED,
                                (MapConfig.MAP_POSITION[0] + node[0] * MapConfig.GRID_SIZE,
                                 MapConfig.MAP_POSITION[1] + node[1] * MapConfig.GRID_SIZE,
                                 MapConfig.GRID_SIZE, MapConfig.GRID_SIZE))
            
            asset_manager.draw_foreground(screen_ref, MapConfig.MAP_POSITION)
            progress_bar_ref.draw(screen_ref)
            pygame.display.flip()
            pygame.time.delay(5)
        
        neighbors = get_neighbors(current)
        for neighbor, wind_alignment, current_alignment in neighbors:
            if neighbor in closed_set:
                continue
            
            tentative_g_score = g_score[current] + euclidean(current, neighbor)
            tentative_f_score = calculate_fscore(
                tentative_g_score, current, neighbor, end,
                is_first_box_green, is_second_box_green,
                wind_alignment, current_alignment
            )
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_f_score
                open_set.put((f_score[neighbor], counter, neighbor))
                counter += 1
    
    progress_bar_ref.stop()
    logger.warning("No path found!")
    return None, explored_nodes


def main():
    """Main game loop with enhanced features"""
    global selected_start, selected_end, start_x, start_y, end_x, end_y
    
    running = True
    path_found = False
    show_input_boxes = False
    start_button_clicked = False
    exploration_done = False
    selected_start = None
    selected_end = None
    current_path = None
    
    start_x = 77.2090
    start_y = 28.6139
    end_x = 88.3639
    end_y = 22.5726
    
    logger.info("Application started with enhanced features")
    
    while running:
        frame_start = pygame.time.get_ticks()
        
        # ========== EVENT HANDLING ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    perf_monitor.toggle_debug()
                elif event.key == pygame.K_F2:
                    keyboard_help.toggle()
                elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    selected_start, selected_end = None, None
                    path_found = False
                    current_path = None
                    logger.info("Selection reset")
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if path_found and current_path:
                        cargo, passenger = uielements.new_input_boxes[0], uielements.new_input_boxes[1]
                        filename = route_manager.save_route(
                            current_path,
                            selected_start or (0, 0),
                            selected_end or (0, 0),
                            {"cargo": cargo, "passenger": passenger}
                        )
                        if filename:
                            error_display.message = f"✓ Route saved!"
                            error_display.timestamp = pygame.time.get_ticks()
                elif event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if path_found and current_path:
                        RouteExporter.export_to_gpx(current_path, "route_export.gpx")
                        error_display.message = f"✓ Exported to GPX!"
                        error_display.timestamp = pygame.time.get_ticks()
                elif event.key == pygame.K_k and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if path_found and current_path:
                        RouteExporter.export_to_kml(current_path, "route_export.kml")
                        error_display.message = f"✓ Exported to KML!"
                        error_display.timestamp = pygame.time.get_ticks()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if uielements.draw_button(screen, show_input_boxes).collidepoint(event.pos):
                    show_input_boxes = not show_input_boxes
                elif uielements.draw_start_button(screen).collidepoint(event.pos):
                    start_button_clicked = True
                    exploration_done = False
                    wind_cache.clear()
                    current_cache.clear()
                    heuristic_cache.clear()
                    logger.info("Start button clicked - caches cleared")
                
                mouse_x, mouse_y = event.pos
                if (MapConfig.MAP_POSITION[0] <= mouse_x < MapConfig.MAP_POSITION[0] + MapConfig.GRID_WIDTH and
                    MapConfig.MAP_POSITION[1] <= mouse_y < MapConfig.MAP_POSITION[1] + MapConfig.GRID_HEIGHT):
                    
                    grid_x = (mouse_x - MapConfig.MAP_POSITION[0]) // MapConfig.GRID_SIZE
                    grid_y = (mouse_y - MapConfig.MAP_POSITION[1]) // MapConfig.GRID_SIZE
                    
                    if selected_start is None:
                        if not is_black_pixel(grid_x, grid_y) and grid_y > 78:
                            selected_start = (grid_x, grid_y)
                            start_y = grid_to_latitude(grid_y)
                            start_x = grid_to_longitude(grid_x)
                            weatherDisplay.weather_data_departure = {}
                            logger.info(f"✓ Start selected: ({start_x:.3f}°E, {start_y:.3f}°N)")
                        else:
                            error_display.show_error("Invalid start point - select ocean area")
                    
                    elif selected_end is None:
                        if not is_black_pixel(grid_x, grid_y) and grid_y > 78:
                            selected_end = (grid_x, grid_y)
                            end_y = grid_to_latitude(grid_y)
                            end_x = grid_to_longitude(grid_x)
                            weatherDisplay.weather_data_destination = {}
                            logger.info(f"✓ End selected: ({end_x:.3f}°E, {end_y:.3f}°N)")
                        else:
                            error_display.show_error("Invalid end point - select ocean area")
                    
                    else:
                        selected_start, selected_end = None, None
                        start_x, start_y = 77.2090, 28.6139
                        end_x, end_y = 88.3639, 22.5726
                        weatherDisplay.weather_data_departure = {}
                        weatherDisplay.weather_data_destination = {}
                        path_found = False
                        current_path = None
                        logger.info("Points reset")
                
                uielements.handle_mouse_click(event)
            
            if show_input_boxes:
                uielements.handle_input(event)
                uielements.handle_dir_input(event)
        
        if show_input_boxes:
            try:
                # Try to parse all four boxes
                start_longitude_manual, err1 = CoordinateValidator.parse_coordinate(uielements.input_boxes[0])
                start_latitude_manual, err2 = CoordinateValidator.parse_coordinate(uielements.input_boxes[1])
                end_longitude_manual, err3 = CoordinateValidator.parse_coordinate(uielements.input_boxes[2])
                end_latitude_manual, err4 = CoordinateValidator.parse_coordinate(uielements.input_boxes[3])
                
                # Check if all parsing was successful (no errors)
                if not err1 and not err2 and not err3 and not err4:
                    # Check if the coordinates have actually changed from the last value
                    if (start_longitude_manual != start_x or
                        start_latitude_manual != start_y or
                        end_longitude_manual != end_x or
                        end_latitude_manual != end_y):
                        
                        logger.info("Manual coordinates updated. Fetching new weather.")
                        
                        # Update the global coordinates
                        start_x = start_longitude_manual
                        start_y = start_latitude_manual
                        end_x = end_longitude_manual
                        end_y = end_latitude_manual
                        
                        # Clear the weather cache to force a re-fetch
                        weatherDisplay.weather_data_departure = {}
                        weatherDisplay.weather_data_destination = {}
                            
            except Exception as e:
                # This will catch errors if input_boxes are empty, etc.
                # We can safely ignore these, as it just means the user isn't done typing.
                pass
 
        screen.blit(background_image, (0, 0))
        asset_manager.draw_background(screen, MapConfig.MAP_POSITION)
        grid_renderer.draw(screen, MapConfig.MAP_POSITION)
        
        if selected_start:
            pygame.draw.rect(screen, Colors.GREEN,
                           (MapConfig.MAP_POSITION[0] + selected_start[0] * MapConfig.GRID_SIZE,
                            MapConfig.MAP_POSITION[1] + selected_start[1] * MapConfig.GRID_SIZE,
                            MapConfig.GRID_SIZE, MapConfig.GRID_SIZE))
        if selected_end:
            pygame.draw.rect(screen, Colors.RED,
                           (MapConfig.MAP_POSITION[0] + selected_end[0] * MapConfig.GRID_SIZE,
                            MapConfig.MAP_POSITION[1] + selected_end[1] * MapConfig.GRID_SIZE,
                            MapConfig.GRID_SIZE, MapConfig.GRID_SIZE))
        
        asset_manager.draw_foreground(screen, MapConfig.MAP_POSITION)
        
        weatherDisplay.weather(screen, start_y, start_x)
        weatherDisplay.weatherTwo(screen, end_y, end_x)
        
        uielements.draw_fuel_estimation_button(screen)
        uielements.draw_image_analysis_button(screen)
        uielements.draw_retrain_model_button(screen)
        uielements.draw_path_coordinates_button(screen)
        
        uielements.draw_start_button(screen)
        uielements.draw_button(screen, show_input_boxes)
        
        if show_input_boxes:
            uielements.draw_input_boxes(screen)
        
        uielements.draw_new_input_boxes(screen)
        cargo, passenger = uielements.new_input_boxes[0], uielements.new_input_boxes[1]
        
        error_display.draw(screen)
        progress_bar.draw(screen)
        
        if path_found:
            path_info_panel.draw(screen)
            eta_calculator.draw_eta_panel(screen)
            cost_calculator.draw_cost_breakdown(screen)
        
        perf_monitor.draw_debug_overlay(screen)
        keyboard_help.draw(screen)
        
        # ========== PATHFINDING LOGIC ==========
        if start_button_clicked and not exploration_done:
            manual_mode_ready = show_input_boxes and all(box and box.strip() != "" for box in uielements.input_boxes)
            click_mode_ready = not show_input_boxes and (selected_start is not None and selected_end is not None)
            
            if manual_mode_ready or click_mode_ready:
                try:
                    if manual_mode_ready:
                        logger.info("Using MANUAL input mode")
                        
                        # Parse coordinates with new parser that handles N/S/E/W
                        try:
                            # Parse each coordinate
                            # Note: start_x, start_y etc are already set by the new live-update block
                            # We just re-parse here for validation.
                            start_longitude, err1 = CoordinateValidator.parse_coordinate(uielements.input_boxes[0])
                            start_latitude, err2 = CoordinateValidator.parse_coordinate(uielements.input_boxes[1])
                            end_longitude, err3 = CoordinateValidator.parse_coordinate(uielements.input_boxes[2])
                            end_latitude, err4 = CoordinateValidator.parse_coordinate(uielements.input_boxes[3])
                            
                            # Check for parsing errors
                            if err1:
                                error_display.show_error(f"Start Lon: {err1}")
                                start_button_clicked = False
                                exploration_done = True
                                continue
                            if err2:
                                error_display.show_error(f"Start Lat: {err2}")
                                start_button_clicked = False
                                exploration_done = True
                                continue
                            if err3:
                                error_display.show_error(f"End Lon: {err3}")
                                start_button_clicked = False
                                exploration_done = True
                                continue
                            if err4:
                                error_display.show_error(f"End Lat: {err4}")
                                start_button_clicked = False
                                exploration_done = True
                                continue
                            
                            logger.info(f"Parsed coordinates: Start({start_longitude:.4f}°E, {start_latitude:.4f}°N) End({end_longitude:.4f}°E, {end_latitude:.4f}°N)")
                            
                        except Exception as e:
                            error_display.show_error(f"Parse error: {str(e)}")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        # Validate start coordinates
                        valid, msg = CoordinateValidator.validate_coordinates(start_longitude, start_latitude)
                        if not valid:
                            error_display.show_error(f"Start: {msg}")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        # Validate end coordinates
                        valid, msg = CoordinateValidator.validate_coordinates(end_longitude, end_latitude)
                        if not valid:
                            error_display.show_error(f"End: {msg}")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        # Convert to grid coordinates
                        start = (longitude_to_grid(start_longitude), latitude_to_grid(start_latitude))
                        end = (longitude_to_grid(end_longitude), latitude_to_grid(end_latitude))
                        
                        logger.info(f"Grid coordinates: Start {start}, End {end}")
                        
                        # Validate grid bounds
                        max_x = MapConfig.GRID_WIDTH // MapConfig.GRID_SIZE
                        max_y = MapConfig.GRID_HEIGHT // MapConfig.GRID_SIZE
                        
                        if not (0 <= start[0] < max_x and 0 <= start[1] < max_y):
                            error_display.show_error(f"Start grid {start} outside bounds")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        if not (0 <= end[0] < max_x and 0 <= end[1] < max_y):
                            error_display.show_error(f"End grid {end} outside bounds")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        # Check if points are on ocean
                        if is_black_pixel(start[0], start[1]):
                            error_display.show_error("Start point is on land - select ocean")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        if is_black_pixel(end[0], end[1]):
                            error_display.show_error("End point is on land - select ocean")
                            start_button_clicked = False
                            exploration_done = True
                            continue
                        
                        # Update selected points for visualization
                        selected_start = start
                        selected_end = end
                        
                        # Run A* algorithm
                        logger.info("Starting pathfinding...")
                        path, explored_nodes = a_star(start, end, cargo, passenger, screen, progress_bar)
                        
                        if path:
                            path_found = True
                            current_path = path
                            logger.info(f"Success! Path has {len(path)} waypoints")
                        else:
                            error_display.show_error("No path found between points")
                        exploration_done = True
                    
                    else:  # Click mode
                        logger.info("Using CLICK input mode")
                        start = selected_start
                        end = selected_end
                        
                        path, explored_nodes = a_star(start, end, cargo, passenger, screen, progress_bar)
                        if path:
                            path_found = True
                            current_path = path
                        else:
                            error_display.show_error("No path found between points")
                        exploration_done = True
                
                except ValueError as e:
                    error_display.show_error(f"Invalid input: {str(e)}")
                    logger.error(f"ValueError: {e}")
                    start_button_clicked = False
                    exploration_done = True
                except Exception as e:
                    error_display.show_error("Unexpected error occurred")
                    logger.exception(f"Unexpected error: {e}")
                    start_button_clicked = False
                    exploration_done = True
            else:
                if show_input_boxes:
                    error_display.show_error("Please fill all coordinate boxes")
                else:
                    error_display.show_error("Please select start and end points")
                start_button_clicked = False
                exploration_done = True
        
        pygame.display.flip()
        frame_time = (pygame.time.get_ticks() - frame_start) / 1000.0
        perf_monitor.record_frame_time(frame_time)
        clock.tick(30)
    
    logger.info("Application closing")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error in main loop")
        pygame.quit()
        sys.exit(1)