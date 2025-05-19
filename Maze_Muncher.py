import pygame
import sys
import math
import time
import random

# Initialize pygame
pygame.init()

# Screen constants
TILE_SIZE = 50
COLS, ROWS = 12, 12
SCREEN_WIDTH = TILE_SIZE * COLS
SCREEN_HEIGHT = TILE_SIZE * ROWS + 50  # Extra space for HUD
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Maze Muncher: Gotham Shadows - Unique Edition")

# Colors
WHITE = (255, 255, 255)
WALL_COLOR = (255, 215, 0)
GLOW_COLOR = (255, 165, 0)
PLAYER_COLOR = (134, 235, 255)
ENEMY_COLOR = (255, 0, 0)
COLLECTIBLE_COLOR = (255, 255, 0)
SHADOW_COLOR = (200, 200, 200)  # Define SHADOW_COLOR
STEALTH_COLOR = (128, 128, 128)
HUD_BG = (64, 64, 64)
TEXT_COLOR = (255, 255, 255)
RED_ALERT = (255, 0, 0)

FONT_SMALL = pygame.font.SysFont("Courier New", 18)
FONT_LARGE = pygame.font.SysFont("Courier New", 36)

# Load images
PLAYER_IMAGE = pygame.image.load(r'c:\Users\user\Downloads\player.png').convert_alpha()
ENEMY_IMAGE = pygame.image.load(r'c:\Users\user\Downloads\enemy.png').convert_alpha()

# Load sounds
pygame.mixer.music.load(r'c:\Users\user\Downloads\jump_sound.mp3')
pygame.mixer.music.set_volume(5)
MOVE_SOUND = pygame.mixer.Sound(r'c:\Users\user\Downloads\bg_sound.mp3')

clock = pygame.time.Clock()

# Maze layout generation
def generate_maze():
    maze = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            if random.random() < 0.2:
                maze[r][c] = 1
    return maze

MAZE_LAYOUT = generate_maze()

ROWS = len(MAZE_LAYOUT)
COLS = len(MAZE_LAYOUT[0])

# Dynamic walls state timer
DYNAMIC_WALL_DURATION = 4000  # ms for open/close cycle

# Player class with stealth toggle
class Player:
    def _init_(self):
        self.x = TILE_SIZE + TILE_SIZE // 2
        self.y = TILE_SIZE + TILE_SIZE // 2
        self.radius = TILE_SIZE // 3
        self.speed = 3.5
        self.dir_x = 0
        self.dir_y = 0
        self.stealth = False
        self.score = 0

    def draw(self, surface):
        color = STEALTH_COLOR if self.stealth else PLAYER_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        # Draw faint glow for stealth mode
        if self.stealth:
            glow = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (128, 128, 128, 60), (self.radius*2, self.radius*2), self.radius*2)
            surface.blit(glow, (self.x - self.radius*2, self.y - self.radius*2))

    def move(self):
        new_x = self.x + self.dir_x * self.speed
        new_y = self.y + self.dir_y * self.speed
        if can_move_to(new_x, new_y, self.radius):
            self.x = new_x
            self.y = new_y
            MOVE_SOUND.play()  # Play movement sound
        else:
            # Try axis wise movement if diagonal blocked
            if can_move_to(self.x + self.dir_x * self.speed, self.y, self.radius):
                self.x += self.dir_x * self.speed
                MOVE_SOUND.play()  # Play movement sound
            elif can_move_to(self.x, self.y + self.dir_y * self.speed, self.radius):
                self.y += self.dir_y * self.speed
                MOVE_SOUND.play()  # Play movement sound

# Enemy class with patrol and detection logic
class Enemy:
    def _init_(self, patrol_points):
        self.patrol_points = patrol_points
        self.current_point_idx = 0
        self.x, self.y = self.patrol_points[0]
        self.radius = TILE_SIZE // 3
        self.speed = 2.3
        self.alerted = False
        self.alert_color_timer = 0

    def draw(self, surface):
        color = RED_ALERT if self.alerted and (pygame.time.get_ticks() // 300) % 2 == 0 else ENEMY_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        # Eyes
        offset_x = self.radius // 2
        offset_y = self.radius // 3
        eye_radius = self.radius // 4
        pygame.draw.circle(surface, (255,255,255), (int(self.x - offset_x), int(self.y - offset_y)), eye_radius)
        pygame.draw.circle(surface, (255,255,255), (int(self.x + offset_x), int(self.y - offset_y)), eye_radius)
        pygame.draw.circle(surface, (0,0,0), (int(self.x - offset_x), int(self.y - offset_y)), eye_radius // 2)
        pygame.draw.circle(surface, (0,0,0), (int(self.x + offset_x), int(self.y - offset_y)), eye_radius // 2)

    def move(self, player):
        target_x, target_y = self.patrol_points[self.current_point_idx]

        # Vector to target patrol point
        vec_x = target_x - self.x
        vec_y = target_y - self.y
        dist = math.hypot(vec_x, vec_y)

        # Move towards patrol point
        if dist < 5:
            # Move to next point
            self.current_point_idx = (self.current_point_idx + 1) % len(self.patrol_points)
        else:
            norm_x = vec_x / dist
            norm_y = vec_y / dist
            new_x = self.x + norm_x * self.speed
            new_y = self.y + norm_y * self.speed
            if can_move_to(new_x, new_y, self.radius):
                self.x = new_x
                self.y = new_y

        # Check detection (line of sight within radius and player not in stealth)
        if not player.stealth and self.can_see_player(player):
            self.alerted = True
            self.alert_color_timer = pygame.time.get_ticks()
            # Chase player directly if alerted
            self.chase(player)
        else:
            # If alerted for over 3 seconds, lose alert
            if pygame.time.get_ticks() - self.alert_color_timer > 3000:
                self.alerted = False

    def chase(self, player):
        vec_x = player.x - self.x
        vec_y = player.y - self.y
        dist = math.hypot(vec_x, vec_y)
        if dist > 5:
            norm_x = vec_x / dist
            norm_y = vec_y / dist
            new_x = self.x + norm_x * (self.speed + 1)
            new_y = self.y + norm_y * (self.speed + 1)
            if can_move_to(new_x, new_y, self.radius):
                self.x = new_x
                self.y = new_y

    def can_see_player(self, player):
        # Detection radius
        MAX_DIST = TILE_SIZE * 4
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > MAX_DIST:
            return False

        # Raycast to check walls blocking view
        steps = int(dist / 5)
        for i in range(1, steps):
            sample_x = self.x + dx * i / steps
            sample_y = self.y + dy * i / steps
            c = int(sample_x // TILE_SIZE)
            r = int(sample_y // TILE_SIZE)
            if r < 0 or r >= ROWS or c < 0 or c >= COLS:
                return False
            # Wall blocks sight if tile != 0 or dynamic wall closed
            if MAZE_DYNAMIC_STATE[r][c] != 0:
                return False
        return True

# Collectible class (bat symbol shaped polygon)
class Collectible:
    def _init_(self, x, y):
        self.x = x
        self.y = y
        self.size = TILE_SIZE // 3
        self.collected = False

    def draw(self, surface):
        if self.collected:
            return
        points = []
        s = self.size
        cx, cy = self.x, self.y
        # Simple bat wing shape using triangles
        points = [
            (cx, cy - s//2),
            (cx - s//3, cy + s//3),
            (cx - s//6, cy + s//6),
            (cx, cy + s//2),
            (cx + s//6, cy + s//6),
            (cx + s//3, cy + s//3),
        ]
        pygame.draw.polygon(surface, COLLECTIBLE_COLOR, points)

def can_move_to(x, y, radius):
    # Check 4 points around circle to avoid clipping walls
    check_points = [
        (x - radius, y),
        (x + radius, y),
        (x, y - radius),
        (x, y + radius),
    ]
    for px, py in check_points:
        c = int(px // TILE_SIZE)
        r = int(py // TILE_SIZE)

        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return False
        
        # Use dynamic state for walls
        if MAZE_DYNAMIC_STATE[r][c] != 0:
            return False
    return True

def draw_maze(surface):
    surface.fill(WHITE)
    for r in range(ROWS):
        for c in range(COLS):
            cell = MAZE_DYNAMIC_STATE[r][c]
            rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)

            # Draw shadow zones adjacent to walls
            if cell == 0 and adjacent_to_wall(r, c):
                pygame.draw.rect(surface, SHADOW_COLOR, rect)

            if cell == 1:
                draw_bat_wing_wall(surface, rect)
            elif cell == 2:
                draw_dynamic_wall(surface, rect, open=dynamic_open)

def adjacent_to_wall(r, c):
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        rr, cc = r+dr, c+dc
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            if MAZE_DYNAMIC_STATE[rr][cc] in (1,2):
                return True
    return False

def draw_bat_wing_wall(surface, rect):
    # Gothic bat wing style wall with "ears" spikes on top corners
    pygame.draw.rect(surface, WALL_COLOR, rect)
    # Draw bat wing ears - two triangles on top-left and top-right
    ear_size = TILE_SIZE//4
    p1 = (rect.left, rect.top)
    p2 = (rect.left + ear_size, rect.top - ear_size)
    p3 = (rect.left + ear_size*2, rect.top)
    pygame.draw.polygon(surface, GLOW_COLOR, [p1,p2,p3])
    p4 = (rect.right, rect.top)
    p5 = (rect.right - ear_size, rect.top - ear_size)
    p6 = (rect.right - ear_size*2, rect.top)
    pygame.draw.polygon(surface, GLOW_COLOR, [p4,p5,p6])

def draw_dynamic_wall(surface, rect, open):
    # Draw dynamic wall as pillar but open or closed
    color = WALL_COLOR if not open else GLOW_COLOR
    pygame.draw.rect(surface, color, rect)
    # Flickering glow effect
    if not open and (pygame.time.get_ticks() // 300) % 2 == 0:
        pygame.draw.rect(surface, RED_ALERT, rect, 3)

# Initialize dynamic maze state (copy of MAZE_LAYOUT)
import copy
MAZE_DYNAMIC_STATE = copy.deepcopy(MAZE_LAYOUT)

# Timing for dynamic walls open/close toggle
dynamic_open = True
last_toggle_time = pygame.time.get_ticks()

# Create collectibles on all free tiles not walls (0 only)
def create_collectibles():
    items = []
    for r in range(ROWS):
        for c in range(COLS):
            if MAZE_DYNAMIC_STATE[r][c] == 0:
                x = c*TILE_SIZE + TILE_SIZE//2
                y = r*TILE_SIZE + TILE_SIZE//2
                # Avoid player start and enemy start
                if not (r == 1 and c == 1) and not (r == ROWS-2 and c == COLS-2):
                    items.append(Collectible(x,y))
    return items

def main():
    global dynamic_open, last_toggle_time

    player = Player()
    enemy_patrol_points = [
        (TILE_SIZE*(COLS-2)+TILE_SIZE//2, TILE_SIZE*(ROWS-2)+TILE_SIZE//2),
        (TILE_SIZE*(COLS-2)+TILE_SIZE//2, TILE_SIZE*1+TILE_SIZE//2),
        (TILE_SIZE*1+TILE_SIZE//2, TILE_SIZE*1+TILE_SIZE//2),
        (TILE_SIZE*1+TILE_SIZE//2, TILE_SIZE*(ROWS-2)+TILE_SIZE//2),
    ]
    enemy = Enemy(enemy_patrol_points)

    collectibles = create_collectibles()

    running = True
    game_over_flag = False
    win_flag = False

    start_time = pygame.time.get_ticks()

    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        # Toggle dynamic walls open/closed every few seconds
        if current_time - last_toggle_time > DYNAMIC_WALL_DURATION:
            dynamic_open = not dynamic_open
            for r in range(ROWS):
                for c in range(COLS):
                    if MAZE_LAYOUT[r][c] == 2:
                        MAZE_DYNAMIC_STATE[r][c] = 0 if dynamic_open else 2
            last_toggle_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if not game_over_flag and not win_flag:
                    if event.key == pygame.K_UP:
                        player.dir_x = 0
                        player.dir_y = -1
                    elif event.key == pygame.K_DOWN:
                        player.dir_x = 0
                        player.dir_y = 1
                    elif event.key == pygame.K_LEFT:
                        player.dir_x = -1
                        player.dir_y = 0
                    elif event.key == pygame.K_RIGHT:
                        player.dir_x = 1
                        player.dir_y = 0
                    elif event.key == pygame.K_s:
                        player.stealth = not player.stealth

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    player.dir_x = 0
                    player.dir_y = 0

        if not game_over_flag and not win_flag:
            player.move()
            enemy.move(player)

            # Collectibles pickup
            for item in collectibles:
                if not item.collected:
                    dist = math.hypot(player.x - item.x, player.y - item.y)
                    if dist < player.radius + item.size/2:
                        item.collected = True
                        player.score += 15

            # Enemy collision triggers game over
            if math.hypot(player.x - enemy.x, player.y - enemy.y) < player.radius + enemy.radius:
                # Player captured
                game_over_flag = True

            # Win if all collectibles collected
            if all(item.collected for item in collectibles):
                win_flag = True

        # Drawing
        draw_maze(SCREEN)
        for item in collectibles:
            item.draw(SCREEN)
        player.draw(SCREEN)
        enemy.draw(SCREEN)
        draw_hud(SCREEN, player.score, player.stealth, current_time - start_time)

        if game_over_flag:
            show_message(SCREEN, "YOU WERE CAUGHT!", RED_ALERT)
        elif win_flag:
            show_message(SCREEN, "YOU ESCAPED THE SHADOWS!", (100, 255, 100))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_hud(surface, score, stealth, elapsed_ms):
    rect = pygame.Rect(0, SCREEN_HEIGHT-50, SCREEN_WIDTH, 50)
    pygame.draw.rect(surface, HUD_BG, rect)

    score_text = FONT_SMALL.render(f"Score: {score}", True, TEXT_COLOR)
    surface.blit(score_text, (10, SCREEN_HEIGHT-40))

    stealth_text = FONT_SMALL.render(f"Stealth Mode: {'ON' if stealth else 'OFF'} (Press S to toggle)", True, TEXT_COLOR)
    surface.blit(stealth_text, (150, SCREEN_HEIGHT-40))

    seconds = elapsed_ms // 1000
    time_text = FONT_SMALL.render(f"Time: {seconds}s", True, TEXT_COLOR)
    surface.blit(time_text, (500, SCREEN_HEIGHT-40))

def show_message(surface, text, color):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(WHITE)
    surface.blit(overlay, (0,0))
    msg = FONT_LARGE.render(text, True, color)
    rect = msg.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    surface.blit(msg, rect)

if _name_ == "_main_":
    main()
