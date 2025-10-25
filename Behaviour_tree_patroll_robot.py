import pygame
import sys
import random
import math

# ==== KONFIG ====
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
FPS = 60

# Warna - Modern Color Palette
WHITE = (248, 248, 248)
BLACK = (30, 30, 30)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (220, 220, 220)
ACCENT_BLUE = (65, 105, 225)
ACCENT_GREEN = (50, 205, 50)
ACCENT_RED = (220, 20, 60)
ACCENT_ORANGE = (255, 140, 0)
ACCENT_YELLOW = (255, 215, 0)
ACCENT_PURPLE = (147, 112, 219)
BACKGROUND = (240, 245, 255)
GRID_COLOR = (230, 230, 230)

# ==== BEHAVIOR TREE STATES ====
class BTState:
    PATROL = "PATROL"
    CHASE_INTRUDER = "CHASE_INTRUDER"
    AVOID_OBSTACLE = "AVOID_OBSTACLE"
    GO_CHARGE = "GO_CHARGE"
    IDLE = "IDLE"

# ==== ROBOT ====
class Robot:
    def __init__(self, waypoints, obstacles, charging_station):
        self.pos = list(waypoints[0])
        self.waypoints = waypoints
        self.target_index = 1
        self.speed = 2.5
        self.state = BTState.PATROL
        self.patrol_count = 0
        self.intruder_pos = None
        self.trail = [self.pos.copy()]
        self.paused = False
        self.obstacles = obstacles
        self.charging_station = charging_station
        self.low_battery = False
        self.avoid_direction = None
        self.avoid_timer = 0
        self.battery_level = 100
        self.last_battery_decrease = 0
        self.max_patrol_before_idle = 3  # Patroli 5x baru idle (jika battery masih tinggi)

    def distance(self, a, b):
        return math.hypot(a[0]-b[0], a[1]-b[1])

    # ==== BT Logic ====
    def behavior_tree_update(self):
        if self.paused:
            return

        # Update battery - HANYA berkurang saat bergerak
        current_time = pygame.time.get_ticks()
        if current_time - self.last_battery_decrease > 800:  # Setiap 0.8 detik
            if self.state != BTState.IDLE:  # Hanya kurangi battery jika tidak idle
                self.battery_level = max(0, self.battery_level - 5.0)  #--
                self.last_battery_decrease = current_time

        # Logika low battery YANG BENAR
        if self.battery_level <= 20:  # Threshold 20%
            self.low_battery = True
        elif self.battery_level >= 90:  # Reset low battery jika sudah terisi
            self.low_battery = False

        # Charge battery ketika di station DAN low battery
        if (self.distance(self.pos, self.charging_station) < 10 and 
            self.state == BTState.GO_CHARGE):
            self.battery_level = min(100, self.battery_level + 3)  # Charge lebih cepat

        if self.check_obstacle():
            self.state = BTState.AVOID_OBSTACLE
            self.avoid_obstacle()
        elif self.intruder_pos:
            self.state = BTState.CHASE_INTRUDER
            self.chase_intruder()
        elif self.low_battery:
            self.state = BTState.GO_CHARGE
            self.go_charge()
        elif self.patrol_count >= self.max_patrol_before_idle and self.battery_level > 50:
            # IDLE HANYA jika sudah patroli banyak DAN battery masih tinggi
            self.state = BTState.IDLE
            self.idle()
        else:
            # PATROLI TERUS sampai battery low atau ada intruder
            self.state = BTState.PATROL
            self.patrol()

        self.trail.append(self.pos.copy())
        
        if self.avoid_timer > 0:
            self.avoid_timer -= 1

    # ==== ACTIONS ====
    def patrol(self):
        target = self.waypoints[self.target_index]
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < 8:
            self.target_index = (self.target_index + 1) % len(self.waypoints)
            if self.target_index == 0:
                self.patrol_count += 1
                print(f"Patrol cycle completed! Count: {self.patrol_count}, Battery: {self.battery_level:.1f}%")
                
        self.pos[0] += dx/dist * self.speed
        self.pos[1] += dy/dist * self.speed

    def idle(self):
        # Robot diam, tidak melakukan apa-apa
        # Battery tidak berkurang saat idle
        pass

    def chase_intruder(self):
        if self.intruder_pos:
            dx = self.intruder_pos[0] - self.pos[0]
            dy = self.intruder_pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            
            if dist > 8:
                self.pos[0] += dx/dist * self.speed
                self.pos[1] += dy/dist * self.speed
            else:
                self.intruder_pos = None

    def check_obstacle(self):
        for obs in self.obstacles:
            if self.distance(self.pos, obs.center) < 70:
                return True
        return False

    def avoid_obstacle(self):
        closest_obs = None
        min_dist = float('inf')
        for obs in self.obstacles:
            d = self.distance(self.pos, obs.center)
            if d < min_dist:
                min_dist = d
                closest_obs = obs

        if closest_obs:
            if self.avoid_direction is None or self.avoid_timer <= 0:
                if self.intruder_pos:
                    target_x, target_y = self.intruder_pos
                elif self.low_battery:
                    target_x, target_y = self.charging_station
                else:
                    target_x, target_y = self.waypoints[self.target_index]
                
                to_target_x = target_x - self.pos[0]
                to_target_y = target_y - self.pos[1]
                to_obs_x = closest_obs.center[0] - self.pos[0]
                to_obs_y = closest_obs.center[1] - self.pos[1]
                
                cross_product = to_target_x * to_obs_y - to_target_y * to_obs_x
                
                if cross_product > 0:
                    avoid_x = to_obs_y
                    avoid_y = -to_obs_x
                else:
                    avoid_x = -to_obs_y
                    avoid_y = to_obs_x
                
                length = math.hypot(avoid_x, avoid_y)
                if length > 0:
                    self.avoid_direction = (avoid_x/length, avoid_y/length)
                else:
                    self.avoid_direction = (1, 0)
                
                self.avoid_timer = 25
            
            avoid_strength = self.speed * 1.5
            self.pos[0] += self.avoid_direction[0] * avoid_strength
            self.pos[1] += self.avoid_direction[1] * avoid_strength
            
            away_x = self.pos[0] - closest_obs.center[0]
            away_y = self.pos[1] - closest_obs.center[1]
            away_dist = math.hypot(away_x, away_y)
            if away_dist > 0:
                away_strength = min(1.0, (70 - away_dist) / 30)
                self.pos[0] += (away_x/away_dist) * self.speed * away_strength
                self.pos[1] += (away_y/away_dist) * self.speed * away_strength

    def go_charge(self):
        # HANYA pergi charge jika benar-benar low battery
        if not self.low_battery:
            self.state = BTState.PATROL  # Kembali patroli jika tidak low battery
            return
            
        target = self.charging_station
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist > 8:
            self.pos[0] += dx/dist * self.speed
            self.pos[1] += dy/dist * self.speed
        else:
            # Reset patrol count HANYA setelah charging selesai
            if self.battery_level >= 90:  # Tunggu sampai battery cukup penuh
                self.patrol_count = 0  # Reset counter patroli
                self.target_index = 1
                self.avoid_direction = None
                print("Charging completed! Resuming patrol...")

    def reset(self):
        self.pos = list(self.waypoints[0])
        self.target_index = 1
        self.patrol_count = 0
        self.intruder_pos = None
        self.trail = [self.pos.copy()]
        self.state = BTState.PATROL
        self.paused = False
        self.low_battery = False
        self.avoid_direction = None
        self.avoid_timer = 0
        self.battery_level = 100
        print("Simulation reset!")

# ==== UI COMPONENTS ====
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=12)
        
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# ==== PYGAME INIT ====
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("🤖 Fixed Patrol Robot - Continuous Patrol Until Battery Low")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont("arial", 32, bold=True)
header_font = pygame.font.SysFont("arial", 24, bold=True)
normal_font = pygame.font.SysFont("arial", 20)
small_font = pygame.font.SysFont("arial", 16)

# Arena grid
GRID_SIZE = 50

# Waypoints
waypoints = [[150, 150], [650, 150], [400, 550]]
waypoint_labels = ["A", "B", "C"]

# Obstacles
obstacles = [
    pygame.Rect(300, 300, 80, 80),
    pygame.Rect(500, 400, 80, 80),
    pygame.Rect(200, 450, 80, 80)
]

# Charging station
charging_station = [75, 75]

# Robot
robot = Robot(waypoints, obstacles, charging_station)

# UI Buttons
reset_button = Button(750, 320, 120, 40, "Reset", ACCENT_RED, (200, 50, 80))
pause_button = Button(750, 380, 120, 40, "Pause/Resume", ACCENT_BLUE, (80, 130, 255))

# Load robot PNG atau buat placeholder
try:
    robot_image = pygame.image.load("robot.png").convert_alpha()
    ROBOT_SIZE = 50
    robot_image = pygame.transform.scale(robot_image, (ROBOT_SIZE, ROBOT_SIZE))
    print("✓ Robot PNG loaded successfully")
except:
    print("✗ Robot PNG not found, creating placeholder")
    robot_image = pygame.Surface((50, 50), pygame.SRCALPHA)
    for i in range(25):
        radius = 25 - i
        alpha = 200 - i * 6
        color = (65, 105, 225, alpha)
        pygame.draw.circle(robot_image, color, (25, 25), radius)
    pygame.draw.circle(robot_image, WHITE, (25, 25), 25, 3)
    pygame.draw.circle(robot_image, WHITE, (25, 25), 8)
    pygame.draw.circle(robot_image, ACCENT_BLUE, (25, 25), 5)
    pygame.draw.polygon(robot_image, ACCENT_YELLOW, [(25, 10), (20, 20), (30, 20)])

# Create obstacle graphic
def create_obstacle_surface(width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(width):
            dist_from_center = math.sqrt((x - width/2)**2 + (y - height/2)**2)
            intensity = max(0, 200 - dist_from_center * 3)
            surf.set_at((x, y), (40, 40, 60, intensity))
    pygame.draw.rect(surf, (80, 80, 100), surf.get_rect(), 3)
    for i in range(3):
        for j in range(3):
            x = width//6 + i * width//3
            y = height//6 + j * height//3
            pygame.draw.rect(surf, (100, 100, 120), (x-2, y-2, 4, 4))
    return surf

obstacle_image = create_obstacle_surface(80, 80)

# ===== LOOP UTAMA =====
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if reset_button.is_clicked(mouse_pos, event):
                robot.reset()
            elif pause_button.is_clicked(mouse_pos, event):
                robot.paused = not robot.paused
            else:
                if mouse_pos[0] < 700:
                    robot.intruder_pos = list(mouse_pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                robot.paused = not robot.paused
            elif event.key == pygame.K_r:
                robot.reset()

    reset_button.check_hover(mouse_pos)
    pause_button.check_hover(mouse_pos)
    robot.behavior_tree_update()

    # ==== DRAWING ====
    screen.fill(BACKGROUND)
    
    # Grid
    for x in range(0, 700, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, 700), 1)
    for y in range(0, 700, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (700, y), 1)
    
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, 700, 700), 3)
    
    # Draw obstacles
    for obs in obstacles:
        screen.blit(obstacle_image, obs)
    
    # Draw trail
    for i, pos in enumerate(robot.trail[-80:]):
        alpha = int(150 * (i/80))
        size = max(2, 6 * (i/80))
        trail_color = (100, 150, 255, alpha)
        trail_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(trail_surf, trail_color, (size, size), size)
        screen.blit(trail_surf, (pos[0]-size, pos[1]-size))
    
    # Draw waypoints
    for i, wp in enumerate(waypoints):
        for r in range(20, 15, -2):
            alpha = 100 - (20 - r) * 20
            pygame.draw.circle(screen, (255, 215, 0, alpha), (int(wp[0]), int(wp[1])), r)
        pygame.draw.circle(screen, ACCENT_YELLOW, (int(wp[0]), int(wp[1])), 18)
        pygame.draw.circle(screen, WHITE, (int(wp[0]), int(wp[1])), 18, 3)
        label = header_font.render(waypoint_labels[i], True, BLACK)
        screen.blit(label, (wp[0]-10, wp[1]-12))

    # Draw charging station
    charge_glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 10
    pygame.draw.circle(screen, (255, 140, 0, 100), charging_station, 25 + charge_glow)
    pygame.draw.circle(screen, ACCENT_GREEN, charging_station, 20)
    pygame.draw.circle(screen, WHITE, charging_station, 20, 3)
    charge_text = header_font.render("⚡", True, WHITE)
    screen.blit(charge_text, (charging_station[0]-12, charging_station[1]-15))

    # Draw intruder
    if robot.intruder_pos:
        if pygame.time.get_ticks() % 400 < 200:
            pygame.draw.circle(screen, ACCENT_RED, robot.intruder_pos, 20)
            pygame.draw.circle(screen, WHITE, robot.intruder_pos, 20, 3)
            intruder_text = header_font.render("!", True, WHITE)
            screen.blit(intruder_text, (robot.intruder_pos[0]-6, robot.intruder_pos[1]-12))

    # Draw robot dengan shadow
    shadow_offset = 4
    shadow_surf = robot_image.copy()
    shadow_surf.fill((0, 0, 0, 80), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(shadow_surf, (robot.pos[0]-25 + shadow_offset, robot.pos[1]-25 + shadow_offset))
    screen.blit(robot_image, (robot.pos[0]-25, robot.pos[1]-25))

    # ==== SIDEBAR UI ====
    sidebar_rect = pygame.Rect(700, 0, 200, WINDOW_HEIGHT)
    pygame.draw.rect(screen, DARK_GRAY, sidebar_rect)
    pygame.draw.rect(screen, WHITE, sidebar_rect, 2)
    
    title_text = title_font.render("BT ROBOT", True, WHITE)
    screen.blit(title_text, (800 - title_text.get_width()//2, 30))
    
    subtitle_text = small_font.render("Continuous Patrol", True, LIGHT_GRAY)
    screen.blit(subtitle_text, (800 - subtitle_text.get_width()//2, 70))
    
    # Status Panel
    status_rect = pygame.Rect(720, 120, 160, 200)
    pygame.draw.rect(screen, BLACK, status_rect, border_radius=10)
    pygame.draw.rect(screen, ACCENT_BLUE, status_rect, 2, border_radius=10)
    
    status_title = header_font.render("STATUS", True, WHITE)
    screen.blit(status_title, (800 - status_title.get_width()//2, 135))
    
    state_colors = {
        BTState.PATROL: ACCENT_GREEN,
        BTState.CHASE_INTRUDER: ACCENT_RED,
        BTState.AVOID_OBSTACLE: ACCENT_ORANGE,
        BTState.GO_CHARGE: ACCENT_YELLOW,
        BTState.IDLE: LIGHT_GRAY
    }
    
    state_color = state_colors.get(robot.state, WHITE)
    state_text = normal_font.render(f"State: {robot.state}", True, state_color)
    screen.blit(state_text, (730, 170))
    
    patrol_text = normal_font.render(f"Patrol: {robot.patrol_count}/5", True, WHITE)
    screen.blit(patrol_text, (730, 200))
    
    intruder_status = "Detected" if robot.intruder_pos else "None"
    intruder_color = ACCENT_RED if robot.intruder_pos else WHITE
    intruder_text = normal_font.render(f"Intruder: {intruder_status}", True, intruder_color)
    screen.blit(intruder_text, (730, 230))
    
    # Battery info
    battery_color = ACCENT_RED if robot.low_battery else ACCENT_GREEN
    battery_status = "LOW!" if robot.low_battery else "OK"
    battery_text = normal_font.render(f"Battery: {robot.battery_level:.1f}%", True, battery_color)
    screen.blit(battery_text, (730, 260))
    
    status_info = normal_font.render(f"Status: {battery_status}", True, battery_color)
    screen.blit(status_info, (730, 285))
    
    # Battery bar
    battery_rect = pygame.Rect(730, 310, 140, 15)
    pygame.draw.rect(screen, DARK_GRAY, battery_rect)
    fill_width = max(0, (robot.battery_level / 100) * 140)
    if fill_width > 0:
        fill_rect = pygame.Rect(730, 310, fill_width, 15)
        pygame.draw.rect(screen, battery_color, fill_rect)
    pygame.draw.rect(screen, WHITE, battery_rect, 2)

    # Controls Panel
    controls_rect = pygame.Rect(720, 450, 160, 120)
    pygame.draw.rect(screen, BLACK, controls_rect, border_radius=10)
    pygame.draw.rect(screen, ACCENT_PURPLE, controls_rect, 2, border_radius=10)
    
    controls_title = header_font.render("CONTROLS", True, WHITE)
    screen.blit(controls_title, (800 - controls_title.get_width()//2, 465))
    
    reset_button.draw(screen, normal_font)
    pause_button.draw(screen, normal_font)
    
    instructions = [
        "Click: Set Intruder",
        "P: Pause/Resume", 
        "R: Reset Simulation"
    ]
    
    for i, instruction in enumerate(instructions):
        inst_text = small_font.render(instruction, True, LIGHT_GRAY)
        screen.blit(inst_text, (730, 490 + i * 25)) #730, 580

    # Paused overlay
    if robot.paused:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        paused_text = title_font.render("SIMULATION PAUSED", True, WHITE)
        screen.blit(paused_text, (WINDOW_WIDTH//2 - paused_text.get_width()//2, WINDOW_HEIGHT//2 - 50))
        continue_text = normal_font.render("Press P or click Resume to continue", True, LIGHT_GRAY)
        screen.blit(continue_text, (WINDOW_WIDTH//2 - continue_text.get_width()//2, WINDOW_HEIGHT//2 + 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()