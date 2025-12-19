import pygame
import sys
import math
from queue import PriorityQueue
import uielements  # Importing UI elements file
import storage # For the map boundary
import weatherDisplay
from CoordConv import latitude_to_grid, longitude_to_grid

clock = pygame.time.Clock()

# Initialize Pygame
pygame.init()

# Set up the display
info = pygame.display.Info()  # Get display information
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Ship Navigation Algo")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 200)
GREEN = (0, 150, 0)
RED = (255, 0, 0)

#Border Tips
NORTH = (40,9)
SOUTH = (49,135) 
WEST = (16,71)
EAST = (121,51)

# Grid properties
grid_size = 4  # Size of each grid cell in pixels
grid_width, grid_height = 550 // grid_size, 600 // grid_size  # Number of cells in each dimension

# Background image positions
map_position = (100, 70)

# Function to draw background
def background():
    image = pygame.image.load("India.jpeg")
    image = pygame.transform.scale(image, (550, 600))
    screen.blit(image, map_position)

# Function to draw foreground (overlay image)
def foreground():
    image = pygame.image.load("IndiaFore.png")
    image = pygame.transform.scale(image, (550, 600))
    screen.blit(image, map_position)

# Function to draw grid over the background
def drawGrid():
    for x in range(map_position[0], map_position[0] + 550, grid_size):
        pygame.draw.line(screen, BLUE, (x, map_position[1]), (x, map_position[1] + 600))
    for y in range(map_position[1], map_position[1] + 600, grid_size):
        pygame.draw.line(screen, BLUE, (map_position[0], y), (map_position[0] + 550, y))

# A* Algorithm with visualization
def euclidean(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def a_star(start, end):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: euclidean(start, end)}
    explored_nodes = []   

    while not open_set.empty():
        _, current = open_set.get()

        # Visualize exploration (happens once, not repeatedly)
        if current != start and current != end:
            explored_nodes.append(current)
            pygame.draw.rect(screen, RED, (map_position[0] + current[0] * grid_size,
                                           map_position[1] + current[1] * grid_size,
                                           grid_size, grid_size))
            pygame.display.flip()
            pygame.time.delay(20)  # Slow down to visualize
        
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
             
            # Draw the background and grid again after exploration
            background()
            drawGrid()
            foreground()    
            weatherDisplay.weather(screen,  28.6139,  77.2090 )
            weatherDisplay.weatherTwo(screen,  35.00,  45.2090 )
            uielements.draw_fuel_estimation_button(screen)
            uielements.draw_image_analysis_button(screen)
            uielements.draw_retrain_model_button(screen)
            uielements.draw_path_coordinates_button(screen)

            pygame.time.delay(500)
            
            for cell in path:
                # Draw each node in green
                pygame.draw.rect(screen, GREEN, (map_position[0] + cell[0] * grid_size,
                                         map_position[1] + cell[1] * grid_size,
                                         grid_size, grid_size))
                pygame.display.flip()  # Update the screen to show the change
                pygame.time.delay(200)  # Add a delay (in milliseconds) for each step
            
            # How long should the path persist
            pygame.time.delay(5000)
                 
            return path, explored_nodes

        neighbors = get_neighbors(current)
        for neighbor in neighbors:
            tentative_g_score = g_score[current] + euclidean(current, neighbor)
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + euclidean(neighbor, end)
                open_set.put((f_score[neighbor], neighbor))

    return None, explored_nodes

# Get neighbors for A* (8-way movement)
def get_neighbors(position):
    neighbors = []
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dy in directions:
        nx, ny = position[0] + dx, position[1] + dy
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            if(nx, ny) not in blocks:
                neighbors.append((nx, ny))
    return neighbors

# Map Boundary
blocks = storage.Backup_black_cells

# Main loop
running = True
path_found = False  # New flag to check if the path has been found
show_input_boxes = False  # Flag to control input box visibility
start_button_clicked = False  # Flag to check if the start button is clicked
exploration_done = False  # Flag to prevent multiple explorations
selected_start = None  # To store the start point : interactive click
selected_end = None # To store the end point : interactive click

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if uielements.draw_button(screen, show_input_boxes).collidepoint(event.pos):
                show_input_boxes = not show_input_boxes
            if uielements.draw_start_button(screen).collidepoint(event.pos):  # Check if Start button is clicked
                start_button_clicked = True  # Set the flag when the start button is clicked
                exploration_done = False  # Reset exploration_done to allow a new search
            uielements.handle_mouse_click(event)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            if(map_position[0]<=mouse_x<map_position[0]+550 and map_position[1]<=mouse_y<map_position[1]+600):
                grid_x = (mouse_x - map_position[0]) // grid_size
                grid_y = (mouse_y - map_position[1]) // grid_size
                
                if selected_start is None:
                    selected_start = (grid_x,grid_y)
                elif selected_end is None:
                    selected_end = (grid_x,grid_y)
                else:
                    selected_start, selected_end = None, None
                
        if selected_start:
            pygame.draw.rect(screen, GREEN, (map_position[0] + selected_start[0] * grid_size,
                                         map_position[1] + selected_start[1] * grid_size,
                                         grid_size, grid_size))
            
        if selected_end:
            pygame.draw.rect(screen, RED, (map_position[0] + selected_end[0] * grid_size,
                                       map_position[1] + selected_end[1] * grid_size,
                                       grid_size, grid_size))
        
        pygame.display.flip()

        if show_input_boxes:
            uielements.handle_input(event)

    screen.fill((0, 0, 140))

    # Draw background and grid
    background()
    drawGrid()
    foreground()
    weatherDisplay.weather(screen,  28.6139,  77.2090 )
    weatherDisplay.weatherTwo(screen,  35.00,  45.2090 )
    uielements.draw_fuel_estimation_button(screen)
    uielements.draw_image_analysis_button(screen)
    uielements.draw_retrain_model_button(screen)
    uielements.draw_path_coordinates_button(screen)
    
    # Draw the "Start" button
    uielements.draw_start_button(screen)  # Ensure the "Start" button is drawn

    # Draw "Automatic" / "Manual" button
    uielements.draw_button(screen, show_input_boxes)

    # Display input boxes if show_input_boxes is active
    if show_input_boxes:
        uielements.draw_input_boxes(screen)

    # If the start button is clicked and coordinates are provided
    if start_button_clicked and ((all(uielements.input_boxes)) or (selected_start != None and selected_end != None)) and not exploration_done:
        try:
            if all(uielements.input_boxes):
                # Convert input latitudes and longitudes to grid coordinates
                start_longitude = float(uielements.input_boxes[0])
                start_latitude = float(uielements.input_boxes[1])
                end_longitude = float(uielements.input_boxes[2])
                end_latitude = float(uielements.input_boxes[3])
                
                # Use CoordConv functions to convert to grid coordinates
                start = (longitude_to_grid(start_longitude), latitude_to_grid(start_latitude))
                end = (longitude_to_grid(end_longitude), latitude_to_grid(end_latitude))
                print(start,end)
                # Validate the grid coordinates
                if 0 <= start[0] < grid_width and 0 <= start[1] < grid_height and \
                0 <= end[0] < grid_width and 0 <= end[1] < grid_height:
                    # Call A* algorithm
                    path, explored_nodes = a_star(start, end)
                    if path:
                        path_found = True  # Mark that the path is found
                        pygame.display.flip()  # Update the screen after drawing the path
                    else:
                        print("Path not found")
                    exploration_done = True  # Set the flag to prevent further exploration
                else:
                    print("Invalid start or end coordinates")
                    
            else:
                start = selected_start
                end = selected_end
                path, explored_nodes = a_star(start,end)
                if path:
                    path_found = True
                    pygame.display.flip()
                else:
                    print("Path not Found")
                
                exploration_done = True                
                
        except ValueError:
            print("Please enter valid integers for coordinates")

    pygame.display.flip()
    clock.tick(30)
