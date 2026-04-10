import pygame
import sys
import json
import math
import random

#NOTICE: This program has been victim of mass restructuration and has now become a complete mess, now I hear you wonder : "Will he fix this ?", absolutely not you dumbfuck I'm too lazy for that

def scale_image(img, factor):
    size = round(img.get_width() * factor), round (img.get_height() * factor)
    return pygame.transform.scale(img, size)

WIN_W, WIN_H = 1920, 1080
MENU_H = 100 #it's supposed to be the toolbar but because of the unprecented amount of terms starting with "tool" all over this program as well as for the sake of this code's overall readability, I took the more or less wise decision to call it "menu" (it's just that my lazy ass can't write shit longer than 4 letters...) <- useless ahh comment just go to bed already aaaah t orange bouin
ZOOM_MIN = 2.5
ZOOM_MAX = 200
ZOOM_DEFAULT = 40

#slay queen 💅✨ (aka colors)
BGC = (25, 30, 35)
GRIDC = (50, 120, 210)
WALLC = (200, 230, 230)
SPAWNC = (80, 180, 80)
FINISHC = (230, 70, 60)

ACTIVEC = (70, 75, 80)
HOVERC = (50, 55, 60)
MENUC = (15, 20, 25)
MENU_BORDERC = (55, 60, 65)
NORMAL = (35, 40, 45)
TEXTC = (210, 210,210)
TEXTBUTLESSVISIBLEC = (110, 110, 110)

CARC = (255, 220, 50) #temporary car color before I start adding actual sprites and a car selector or smth like that
#TOTALYNOTAFERRARI = scale_image(pygame.image.load("pitstop_car_1.png"), 0.5)

CPC = (220,180, 40)
BEST = (160, 80, 210) #purple if all-time best
BETTER = (80, 200, 80) #green if better than previously
BAD = (210, 60, 60) #red if worse than before

#AI stuff
POP_SIZE = 60
GENERATIONS = 30
SURVIVORS = 6 #number of AI kept per generations (the best ones of course)
SIM_DT = 1/60 #simulation timestep (seconds)
CP_TIMEOUT = 20.0 #time limit in seconds before the ai gets terminated between 2 spawn, finish or checkpoints
AI_N_IN = 12 #9 raycasts + speed + angle-to-next-cp = 12 inputs
AI_N_HID = 16
AI_N_OUT = 2
# Angles of the rays cast from the car (135° from the front in both directions -> total 270° with 90° blind spot at the rear)
RAY_ANGLES = [-135, -105, -75, -45, -15, 0, 15, 45, 75, 105, 135] #11 rays but only 9 used
RAY_ANGLES = list(range(-120, 121, 30)) #-120, -90, -60, -30, 0, 30, 60, 90, 120 -> 9 rays
RAY_MAX = 20 #the ray's maximum distance in cells

CAR_DEFS = [
    {"name": "Not a Ferrari©", "file": "pitstop_car_1.png"},
    {"name": "white pow(d)er", "file": "pitstop_car_2.png"},
    {"name": "no joke here...", "file": "pitstop_car_3.png"},
    {"name": "blue meth(anol)", "file": "pitstop_car_4.png"},
    {"name": "oh a yellow car WAIT NO ARGH", "file": "pitstop_car_5.png"},
    {"name": "Vorsprung durch Technik ?", "file": "pitstop_car_7.png"},
    {"name": "Twitch's gambling cousin", "file": "pitstop_car_9.png"},
    {"name": "Nike's mechanic uncle", "file": "pitstop_car_10.png"}
]

#Tools
WALL_TOOL = "wall"
ERASE_TOOL = "erase"
SPAWN_TOOL = "spawn"
FINISH_TOOL = "finish"
CHECKPOINT_TOOL = "checkpoint"

TOOLS = [WALL_TOOL, SPAWN_TOOL, FINISH_TOOL, CHECKPOINT_TOOL, ERASE_TOOL]

LABEL= {
    WALL_TOOL: "Wall",
    SPAWN_TOOL: "Spawn",
    FINISH_TOOL: "Finish",
    ERASE_TOOL: "Erase",
    CHECKPOINT_TOOL: "Checkpoint"
}

KEYS = {
    pygame.K_w: WALL_TOOL,
    pygame.K_s: SPAWN_TOOL,
    pygame.K_f: FINISH_TOOL,
    pygame.K_e: ERASE_TOOL,
    pygame.K_c: CHECKPOINT_TOOL
}

TOOL_COLORS = {
    WALL_TOOL: WALLC,
    SPAWN_TOOL: SPAWNC,
    FINISH_TOOL: FINISHC,
    ERASE_TOOL: BGC,
    CHECKPOINT_TOOL: CPC
}

def screen_to_grid(mx, my, cam_x, cam_y, zoom):
    col = int((mx - cam_x) // zoom)
    row = int((my - cam_y) // zoom)
    return col, row

def grid_to_screen(col, row, cam_x, cam_y, zoom):
    x = int(col*zoom + cam_x)
    y = int(row*zoom + cam_y)
    return x, y

class MapState:
    def __init__(self):
        self.walls = set()
        self.spawn = set()
        self.finish = set()
        self.history = []
        self.checkpoints = []
        self.spawn_angle = 0.0

    def snapshot(self):
        return {
            "walls": set(self.walls),
            "spawn": set(self.spawn),
            "finish": set(self.finish),
            "checkpoints": list(self.checkpoints),
            "spawn_angle": self.spawn_angle
        }
    
    def push_history(self):
        self.history.append(self.snapshot())
        if len(self.history)>200:
            self.history.pop(0)

    def undo(self):
        if self.history:
            snap = self.history.pop()
            self.walls = snap["walls"]
            self.spawn = snap["spawn"]
            self.finish = snap["finish"]
            self.checkpoints = snap["checkpoints"]
            self.spawn_angle = snap["spawn_angle"]

    def apply_tool(self, col, row, tool):
        if tool == WALL_TOOL:
            self.walls.add((col, row))
            self.spawn.discard((col, row))
            self.finish.discard((col, row))
            self.checkpoints = [c for c in self.checkpoints if c != (col, row)]
        elif tool == SPAWN_TOOL:
            self.walls.discard((col, row))
            self.spawn.clear()
            self.spawn.add((col, row))
            self.checkpoints = [c for c in self.checkpoints if c != (col, row)]
        elif tool == FINISH_TOOL:
            self.walls.discard((col, row))
            self.finish.clear()
            self.finish.add((col, row))
            self.checkpoints = [c for c in self.checkpoints if c != (col, row)]
        elif tool == CHECKPOINT_TOOL:
            self.walls.discard((col, row))
            self.spawn.discard((col, row))
            self.finish.discard((col, row))
            if(col, row) not in self.checkpoints:
                self.checkpoints.append((col, row))
        elif tool == ERASE_TOOL:
            self.walls.discard((col, row))
            self.spawn.discard((col, row))
            self.finish.discard((col, row))
            self.checkpoints = [c for c in self.checkpoints if c != (col, row)]
        
    def is_loop(self):
            return bool(self.spawn and self.finish and self.spawn == self.finish)
    
    def to_json(self):
        return json.dumps({
            "zoom_default": ZOOM_DEFAULT,
            "walls": [list(t) for t in self.walls],
            "spawn": [list(t) for t in self.spawn],
            "finish": [list(t) for t in self.finish],
            "checkpoints": [list(t) for t in self.checkpoints],
            "spawn_angle": self.spawn_angle,
        }, indent=2)

def draw_grid(surf, cam_x, cam_y, zoom):
    grid_h = WIN_H - MENU_H

    alpha = min(255, int((zoom - 1)*20))
    grid_color = (*GRIDC, alpha)
    grid_surface = pygame.Surface((WIN_W, WIN_H - MENU_H), pygame.SRCALPHA)

    col_start = int(-cam_x // zoom) - 1
    col_end = int((WIN_W - cam_x) // zoom) + 1
    row_start = int(-cam_y // zoom) - 1
    row_end = int((grid_h - cam_y) // zoom) + 1
    for c in range(col_start, col_end + 1):
        x = int(c*zoom + cam_x)
        pygame.draw.line(grid_surface, grid_color, (x, 0), (x, WIN_H - MENU_H))

    for r in range(row_start, row_end + 1):
        y = int(r*zoom + cam_y)
        if 0<= y <= WIN_H - MENU_H:
            pygame.draw.line(grid_surface, grid_color, (0, y), (WIN_W, y))
    surf.blit(grid_surface, (0, 0))

def draw_tile(surf, col, row, color, font, label, cam_x, cam_y, zoom, alpha=255):
    x, y = grid_to_screen(col, row, cam_x, cam_y, zoom)
    size = max(1, int(zoom) - 1)

    #skip if outside of grid area
    if x + size < 0 or x > WIN_W or y + size < 0 or y > WIN_H - MENU_H:
        return
    
    if alpha < 255:
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surf.blit(s, (x+1, y + 1))
    else:
        pygame.draw.rect(surf, color, (x + 1, y + 1, size, size))

    if label and font and zoom >= 14:
        cx = x + int(zoom) // 2
        cy = y + int(zoom) //2
        lbl = font.render(label, True, BGC)
        surf.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

def draw_spawn_arrow(surf, col, row, angle_deg, cam_x, cam_y, zoom):
    x, y = grid_to_screen(col, row, cam_x, cam_y, zoom)
    size = max(1, int(zoom) - 1)
    if x + size < 0 or x > WIN_W or y + size < 0 or y > WIN_H - MENU_H:
        return
    cx = x + size // 2
    cy = y + size // 2
    r = max(4, size // 2 - 4)
    rad = math.radians(angle_deg)
    tip_x = cx + math.cos(rad) * r
    tip_y = cy + math.sin(rad) * r
    hw = max(2, size // 8)
    lw = max(1, size // 16)
    ah = max(3, size // 5)
    base_x = tip_x - math.cos(rad) * ah
    base_y = tip_y - math.sin(rad) * ah
    tail_x = cx - math.cos(rad) * r * 0.5
    tail_y = cy - math.sin(rad) * r * 0.5
    perp = rad + math.pi / 2
    pygame.draw.line(surf, (255, 255, 255), (int(tail_x), int(tail_y)), (int(base_x), int(base_y)), lw)
    lp = (int(base_x - math.cos(perp) * hw), int(base_y - math.sin(perp) * hw))
    rp = (int(base_x + math.cos(perp) * hw), int(base_y + math.sin(perp) * hw))
    pygame.draw.polygon(surf, (255, 255, 255), [(int(tip_x), int(tip_y)), lp, rp])

def draw_hover(surf, col, row, tool, cam_x, cam_y, zoom, font):
    color = TOOL_COLORS.get(tool, BGC)
    label = {"spawn": "S", "finish": "F"}.get(tool)
    draw_tile(surf, col, row, color, font, label, cam_x, cam_y, zoom, alpha=100)

def cells_between(c0, r0, c1, r1):  #Bresenham line algorithm magic stuff spewed by Claude cuz issue with tile placement at high speed
        if c0 == c1 and r0 == r1:   #so no idea how it works but it does so let's move on
            return [(c0, r0)]       #EDIT: It did, matter of fact, not work...
        cells = []                  #Ok sorry mb I'm just autistic and replaced an < with an >
        dc = abs(c1 - c0)           
        dr = abs(r1 - r0)
        sc = 1 if c0 < c1 else -1
        sr = 1 if r0 < r1 else -1
        err = dc - dr
        while True:
            cells.append((c0, r0))
            if c0 == c1 and r0 == r1:
                break
            e2 = 2 * err
            if e2 > -dr:
                err -= dr
                c0 += sc
            if e2 < dc:
                err += dc
                r0 += sr
        return cells

def fmt_time(t):
    if t is None:
        return "--:--.---"
    mins = int(t) // 60
    secs = t - mins * 60
    return f"{mins:02d}:{secs:06.3f}"


class ToolButton:
    W, H = 160, 60
    RADIUS = 8

    def __init__(self, cx, cy, tool):
        self.rect = pygame.Rect(cx - self.W//2, cy - self.H//2, self.W, self.H)
        self.tool = tool
        self.label = LABEL[tool]
        self.color = TOOL_COLORS[tool]
        self.hovered = False
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surf, active_tool, font, font_small):
        active = active_tool == self.tool
        bg = ACTIVEC if active else (HOVERC if self.hovered else NORMAL)
        border = self.color if active else MENU_BORDERC

        pygame.draw.rect(surf, bg, self.rect, border_radius=self.RADIUS)
        bw = 2 if active else 1
        pygame.draw.rect(surf, border, self.rect, width=bw, border_radius=self.RADIUS)

        #coulour swatch why do I need this again
        swatch_r = 6
        swatch_x = self.rect.left + 18
        swatch_y = self.rect.centery
        if self.tool != ERASE_TOOL:
            pygame.draw.circle(surf, self.color, (swatch_x, swatch_y), swatch_r)
        else:
            pygame.draw.line(surf, TEXTBUTLESSVISIBLEC,
                             (swatch_x - 5, swatch_y - 5), (swatch_x + 5, swatch_y + 5), 2)
            pygame.draw.line(surf, TEXTBUTLESSVISIBLEC,
                             (swatch_x + 5, swatch_y - 5), (swatch_x - 5, swatch_y + 5), 2) #This shit is to make an X symbol
       #label     
        txt_col = TEXTC if active else (TEXTC if self.hovered else TEXTBUTLESSVISIBLEC)
        lbl = font.render(self.label, True, txt_col)
        surf.blit(lbl, (self.rect.left + 34, self.rect.centery - lbl.get_height()//2))
        #keyhints for shortcuts ? keyhints ? is that even a word ???
        key_hints = {WALL_TOOL: "W", SPAWN_TOOL:"S", FINISH_TOOL:"F", ERASE_TOOL:"E", CHECKPOINT_TOOL: "R"}
        hint = font_small.render(key_hints[self.tool], True, TEXTBUTLESSVISIBLEC)
        surf.blit(hint, (self.rect.right - hint.get_width() - 10,
                         self.rect.top + 6))
        

# Okay, pause, u know what ?
# let's take a quick break alr?
# inhale, hold your breath for a sec..., aaand  ...exhale, now again: inhale...
# and take a quick look at my motivation letter for a frech university yayy q(≧▽≦q)
#Madame, Monsieur,
#Je souhaite m'orienter vers les métiers de l'ingénierie et plus spécifiquement de la mécanique.
#Pour cette raison, je voudrais intégrer Sorbonne Université, spécialisé dans ce domaine, notamment
#via sa formation C.M.I Mécanique à lauqlle j'ai décidé de candidater.

#En effet, particulièrement attiré par l'ingénierie mécanique, c'est avec enthousiasme que j'ai pris
#connaissance de votre formation et des enseignements qui y sont associés.

#Me destinant au métier d'ingénieur, j'éprouve un vif intérêt pour les disciplines scientifiques, la
#mécanique et modélisation. Les ensignements du C.M.I constituent donc l'environment idéa pour m'améliorer
#dans ces domaines.
#En complément aux connaissances académiques, je suis inéteressé par l'aspect professionalisant de ce
#diplôme, la place importante accordée aux projets, ainsi qu'à votre adossement à un grand centre de
#recherche. Par ailleurs, je suis conscient que l'environnement du campus de la Sorbonne offre de
#nombreuses opportunités pour se former dans les domaines technologiques. Suite à mes recherches, je suis
#donc convaincu que votre formation C.M.I Mécanique propose le cursus le mieux adapté à mes projets
#professionels. Je suis prêt à m'investir pour réussir dans ce projet de formation.

#Je me tiens à votre disposition pour vous fournir toutes informations complémentaires nécessaires. En
#espérant un retour favorable de votre part, je vous remercie par avance de l'attention que vous aurez
#accordée à ma candidature.

#Yeah, I'm gonna prepare one for my local McDonald too, probably have more luck over there... ಥ_ಥ
#Oh yeah btw you can exhale now ^3^

#Ok back to work now

class Car:
    MAX_SPEED = 1000.0
    ACCEL = 700.0
    FRICTION = 180.0
    TURN_SPEED = 4
    SIZE = 0.6

    def __init__(self, col, row, sprite = None, spawn_angle_deg=0.0, checkpoints=None, finish=None, loop_map=True):
        self.x = (col + 0.5) * ZOOM_DEFAULT
        self.y = (row + 0.5) * ZOOM_DEFAULT
        self.angle = math.radians(spawn_angle_deg)
        self.speed = 0.0
        self.sprite = sprite
        self.checkpoints = checkpoints or []
        self.finish_cells = finish or set()
        self.loop_map = loop_map
        self.next_cp = 0
        self.lap_time = 0.0
        self.sector_time = 0.0
        self.best_lap = None
        self.last_lap = None
        self.last_sectors = []
        self.best_sectors = []
        self.sector_colors = []
        self.last_cell = None
        self.finished = False
        self.final_sector_time = []
        self.left_start = False #must leave spawn to before the lap, else when in loop mode with no checkpoint you complete laps just by staying on the spawn/finish point...
        self._on_finish = True
        self._on_cp = False

    def _get_mask(self, zoom):
            hw = self.SIZE * zoom
            hh = self.SIZE * zoom * 2
            if self.sprite:
                target_w = max(1, int(hw * 2))
                target_h = max(1, int(hh * 2))
                scaled = pygame.transform.scale(self.sprite, (target_w, target_h))
                angle_deg = -math.degrees(self.angle) + 90
                rotated = pygame.transform.rotate(scaled, angle_deg)
            else:
                surf = pygame.Surface((max(1, int(hw * 2)), max(1, int(hh * 2))), pygame.SRCALPHA)
                surf.fill((255, 255, 255))
                cos_a = math.cos(self.angle)
                sin_a = math.sin(self.angle)
                corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
                pts = [(hw + x * cos_a - y * sin_a, hh + x * sin_a + y * cos_a) for x, y in corners]
                pygame.draw.polygon(surf, (255, 255, 255, 255), pts)
                rotated = surf
            return pygame.mask.from_surface(rotated), rotated.get_rect()

    def update(self, dt, walls):
        if self.finished:
            return
        keys = pygame.key.get_pressed()
        accel_input = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]: accel_input = 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: accel_input = -1
        turn_input = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: turn_input = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: turn_input = 1

        if  accel_input != 0:
            self.speed += accel_input * self.ACCEL * dt
            self.speed = max(-self.MAX_SPEED * 0.5, min(self.MAX_SPEED, self.speed))
        else:
            if abs(self.speed) < self.FRICTION * dt:
                self.speed = 0.0
            else:
                self.speed -= math.copysign(self.FRICTION * dt, self.speed)
        speed_abs = abs(self.speed)
        if speed_abs > 25:
            speed_factor = (abs(self.speed)/self.MAX_SPEED)
            turn_scale = 0.45 + 0.3* speed_factor
            self.angle += turn_input * self.TURN_SPEED * dt *turn_scale * math.copysign(1, self.speed)

        new_x = self.x + math.cos(self.angle) * self.speed * dt
        new_y = self.y + math.sin(self.angle) * self.speed * dt

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        hw = self.SIZE * ZOOM_DEFAULT * 1.6
        hh = self.SIZE * ZOOM_DEFAULT * 0.8
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]

        def corner_world(px, py, cx, cy):
            return (px + cx * cos_a - cy * sin_a, py + cx * sin_a + cy * cos_a)

        def cell_of(wx, wy):
            return (math.floor(wx / ZOOM_DEFAULT), math.floor(wy / ZOOM_DEFAULT))
        
        def in_wall(wx, wy):
            return cell_of(wx, wy) in walls
    
        hitting =[]
        for cx, cy in corners:
            wx, wy = corner_world(new_x, new_y, cx, cy)
            if in_wall(wx, wy):
                hitting.append((cx, cy))
        
        if not hitting:
            self.x = new_x
            self.y = new_y
        else:
            self.speed = 0.0
            hit_cx = [cx for cx, cy in hitting]
            hit_cy = [cy for cx, cy in hitting]
            block_x = all(c > 0 for c in hit_cx) or all(c < 0 for c in hit_cx)
            block_y = all(c > 0 for c in hit_cy) or all(c < 0 for c in hit_cy)
            if not block_x:
                wx, wy = corner_world(new_x, self.y, hitting[0][0], hitting[0][1])
                if not in_wall(wx, wy):
                    self.x = new_x
            if not block_y:
                wx, wy = corner_world(self.x, new_y, hitting[0][0], hitting[0][1])
                if not in_wall(wx, wy):
                    self.y = new_y
        
        self.lap_time += dt
        self.sector_time += dt

        scale = ZOOM_DEFAULT
        sx = self.x
        sy = self.y
        car_mask, car_rect = self._get_mask(ZOOM_DEFAULT)
        car_rect.center = (int(sx), int(sy))

        def overlaps_cell(col, row):
            cell_x = col * ZOOM_DEFAULT
            cell_y = row * ZOOM_DEFAULT
            #offset between car mask origin and cell mask origin
            ox = car_rect.left - cell_x
            oy = car_rect.top - cell_y
            cell_surf = pygame.Surface((ZOOM_DEFAULT, ZOOM_DEFAULT))
            cell_mask = pygame.mask.from_surface(cell_surf)
            return cell_mask.overlap(car_mask, (ox, oy)) is not None
        
        if self.checkpoints and self.next_cp < len(self.checkpoints):
            cp_col, cp_row = self.checkpoints[self.next_cp]
            if overlaps_cell(cp_col, cp_row):
                if not getattr(self, '_on_cp', False):
                    self._complete_sector(self.next_cp)
                    self.next_cp += 1
                self._on_cp = True
            else:
                self._on_cp = False
            
        all_cp_done = not self.checkpoints or self.next_cp >= len(self.checkpoints)
        if all_cp_done:
            on_finish = any(overlaps_cell(fc, fr) for fc, fr in self.finish_cells)
            if not self.left_start:
                if not on_finish:
                    self.left_start = True
            elif on_finish and not getattr(self, '_on_finish', False):
                if self.loop_map:
                    self._complete_lap()
                else:
                    self._complete_sector(self.next_cp)
                    self.last_lap = self.lap_time
                    if self.best_lap is None or self.lap_time < self.best_lap:
                        self.best_lap = self.lap_time
                    self.finished = True
            self._on_finish = on_finish


    def _complete_sector(self, idx):
        t = self.sector_time
        self.sector_time = 0.0
        if idx < len(self.best_sectors) and self.best_sectors[idx] is not None:
            if t < self.best_sectors[idx]:
                col = BEST
                self.best_sectors[idx]
            else:
                prev = self.last_sectors[idx] if idx < len(self.last_sectors) and self.last_sectors[idx] else None
                col = BETTER if (prev is None or t < prev) else BAD
        else:
            while len(self.best_sectors) <= idx:
                self.best_sectors.append(None)
            self.best_sectors[idx] = t
            col = BETTER
            while len(self.sector_colors) <= idx:
                self.sector_colors.append(BAD)
            self.sector_colors[idx] = col
            while len(self.last_sectors) <= idx:
                self.last_sectors.append(None)
            self.last_sectors[idx] = t

    def _complete_lap(self):
        self._complete_sector(self.next_cp)
        t = self.lap_time
        self.last_lap = t
        if self.best_lap is None or t < self.best_lap:
            self.best_lap = t
        self.lap_time = 0.0
        self.sector_time = 0.0
        self.next_cp = 0

    def draw(self, surf, cam_x, cam_y, zoom):
        scale = zoom / ZOOM_DEFAULT
        sx = self.x * scale + cam_x
        sy = self.y * scale + cam_y
        hw = self.SIZE * zoom
        hh = self.SIZE * zoom * 2

        if self.sprite:
            target_w = int(hw * 2)
            target_h = int(hh * 2)
            if target_w > 0 and target_h > 0:
                scaled = pygame.transform.scale(self.sprite, (target_w, target_h))
                angle_deg = -math.degrees(self.angle) + 90
                rotated = pygame.transform.rotate(scaled, angle_deg)
                rect = rotated.get_rect(center=(int(sx), int(sy)))
                surf.blit(rotated, rect.topleft)
        else:
            corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
            cos_a = math.cos(self.angle)
            sin_a = math.sin(self.angle)
            rotated = [ 
                (sx + x * cos_a - y * sin_a,
                sy + x * sin_a + y * cos_a)
                for x, y in corners
            ]
            pygame.draw.polygon(surf, CARC, rotated)
            pygame.draw.polygon(surf, (180, 150, 20), rotated, 2)

            front_x = sx + math.cos(self.angle) * hw
            front_y = sy + math.sin(self.angle) * hw
            pygame.draw.circle(surf, (50, 30, 10), (int(front_x), int(front_y)), max(2, int(hw*0.25)))

    def draw_hud(self, surf, font, font_small):
        x, y = 24, 24
        pad = 6
        lines = [
            (f"Time: {fmt_time(self.lap_time)}", TEXTC),
            (f"Last lap: {fmt_time(self.last_lap)}",TEXTBUTLESSVISIBLEC),
            (f"Best lap: {fmt_time(self.best_lap)}", BEST if self.best_lap else TEXTBUTLESSVISIBLEC)
        ]

        if self.checkpoints:
            total = len(self.checkpoints) + 1
            for i in range (total):
                label = f"S{i+1}"
                if i < len(self.sector_colors):
                    col = self.sector_colors[i]
                elif i == self.next_cp:
                    col = TEXTC
                else:
                    col = TEXTBUTLESSVISIBLEC
                lines.append((label, col))
        bg_w = 260
        bg_h = len(lines) * 22 + pad * 2
        bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surf.blit(bg, (x - pad, y - pad))
        for text, col in lines:
            s = font_small.render(text, True, col)
            surf.blit(s, (x, y))
            y += 22

def draw_split_tile(surf, col, row, cam_x, cam_y, zoom):
    x, y = grid_to_screen(col, row, cam_x, cam_y, zoom)
    size = max(1, int(zoom) - 1)
    if x + size < 0 or x > WIN_W or y + size < 0 or y > WIN_H - MENU_H:
        return
    x1, y1 = x + 1, y + 1
    x2, y2 = x + size, y + size
    pygame.draw.polygon(surf, SPAWNC, [(x1, y1), (x2, y1), (x1, y2)])
    pygame.draw.polygon(surf,FINISHC, [(x2, y1), (x2, y2), (x1, y2)])

def draw_select_popup(surf, car_defs, car_sprites, selected_idx, mouse_pos, font, font_small):
    #dim bg
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    n = len(car_defs)
    card_w = 160
    card_h = 200
    padding = 24
    total_w = n * card_w + (n-1) * padding
    panel_w = total_w + 80
    panel_h = card_h + 120
    panel_x = WIN_W //2 - panel_w // 2
    panel_y = WIN_H // 2 - panel_h // 2
    pygame.draw.rect(surf, (20, 24, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(surf, MENU_BORDERC, (panel_x, panel_y, panel_w, panel_h), width=1, border_radius=12)
    title = font.render("Select you car", True, TEXTC)
    surf.blit(title, (WIN_W //2 - title.get_width() // 2, panel_y + 16))
    hint = font_small.render("Enter to confirm | Esc to cancel", True, TEXTBUTLESSVISIBLEC)
    surf.blit(hint, (WIN_W //2 - hint.get_width() // 2, panel_y + panel_h - 24))
    hovered_idx = None
    cards_start_x = WIN_W // 2 - total_w // 2
    cards_y = panel_y + 52
    for i, car_def in enumerate(car_defs):
        cx = cards_start_x + i * (card_w + padding)
        card_r = pygame.Rect(cx, cards_y, card_w, card_h)
        hovered = card_r.collidepoint(mouse_pos)
        if hovered:
            hovered_idx = i
        
        active = i == selected_idx
        bg = ACTIVEC if active else (HOVERC if hovered else NORMAL)
        border = SPAWNC if active else (MENU_BORDERC if not hovered else TEXTBUTLESSVISIBLEC)
        bw = 2 if active else 1
        pygame.draw.rect(surf, bg, card_r, border_radius=8)
        pygame.draw.rect(surf, border, card_r, width=bw, border_radius=8)

        #sprite preview
        sprite = car_sprites[i]
        if sprite:
            prev_h = card_h - 50
            prev_w = card_h // 2.4
            scaled = pygame.transform.scale(sprite, (prev_w, prev_h))
            rotated = pygame.transform.rotate(scaled, 90)
            r = rotated.get_rect(center =(cx + card_w // 2, cards_y + (card_h - 36) // 2))
            surf.blit(rotated, r.topleft)
        else:
            pygame.draw.rect(surf, CARC, (cx + 20, cards_y + 20, card_w - 40, card_h - 60), border_radius=4)
        name_surf = font_small.render(car_def["name"], True, TEXTC if active else TEXTBUTLESSVISIBLEC)
        surf.blit(name_surf, (cx + card_w // 2 - name_surf.get_width() // 2, cards_y + card_h - 28))
    return hovered_idx

def draw_results(surf, car, font, font_small, mouse_pos):
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surf.blit(overlay, (0, 0))

    panel_w = 400
    n_sectors = len([t for t in car.last_sectors if t != None])
    panel_h = 180 + n_sectors * 22 + 60
    panel_x = WIN_W // 2 - panel_w // 2
    panel_y = WIN_H // 2 - panel_h // 2
    pygame.draw.rect(surf, (20, 24, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(surf, MENU_BORDERC, (panel_x, panel_y, panel_w, panel_h), width=1, border_radius=12)
    cy = panel_y + 20

    title = font.render("Run completed", True, TEXTC)
    surf.blit(title, (WIN_W//2 - title.get_width()//2, cy))
    cy += 36

    time_col = BEST if (car.best_lap == car.last_lap) else TEXTC
    t = font.render(fmt_time(car.last_lap), True, time_col)
    surf.blit(t, (WIN_W // 2 - t.get_width() // 2, cy))
    cy += 30

    best_s = font_small.render(f"Best: {fmt_time(car.best_lap)}", True, BEST)
    surf.blit(best_s, (WIN_W // 2 - best_s.get_width() // 2, cy))
    cy += 26

    pygame.draw.line(surf, MENU_BORDERC, (panel_x + 20, cy), (panel_x + panel_w - 20, cy), 1)
    cy += 10

    for i, t_sec in enumerate(car.last_sectors):
        if t_sec is None:
            continue
        best_t = car.best_sectors[i] if i < len(car.best_sectors) else None
        col = car.sector_colors[i] if i < len(car.sector_colors) else TEXTBUTLESSVISIBLEC
        label = f"S{i+1}: {fmt_time(t_sec)}"
        if best_t is not None:
            label += f"(best {fmt_time(best_t)})"
        s = font_small.render(label, True, col)
        surf.blit(s, (panel_x + 30, cy))
        cy += 22
    cy += 10

    btn_w, btn_h = 160, 44
    gap = 24
    retry_rect = pygame.Rect(WIN_W // 2 - btn_w - gap//2, cy, btn_w, btn_h)
    back_rect = pygame.Rect(WIN_W//2 + gap//2, cy, btn_w, btn_h)
    for rect, label, key_hints in [
        (retry_rect, "Retry", "Enter"),
        (back_rect, "Go Back", "Tab"),
        ]:
        hovered = rect.collidepoint(mouse_pos)
        bg = HOVERC if hovered else NORMAL
        pygame.draw.rect(surf, bg, rect, border_radius = 8)
        pygame.draw.rect(surf, MENU_BORDERC, rect, width=1, border_radius=8)
        lbl = font.render(label, True, TEXTC)
        hint = font_small.render(key_hints, True, TEXTBUTLESSVISIBLEC)
        surf.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height()//2 - 6))
        surf.blit(hint, (rect.centerx - hint.get_width()//2, rect.centery + 6))
    
    return retry_rect, back_rect

class NeuralNetwork:
    def __init__(self, weights=None):
        if weights is None:
            self.w1 = [[random.uniform(-1, 1) for _ in range(AI_N_IN)] for _ in range(AI_N_HID)]
            self.b1 = [random.uniform(-1, 1) for _ in range(AI_N_HID)]
            self.w2 = [[random.uniform(-1, 1) for _ in range(AI_N_HID)] for _ in range(AI_N_OUT)]
            self.b2 = [random.uniform(-1, 1) for _ in range(AI_N_OUT)]
        else:
            self.w1, self.b1, self.w2, self.b2 = weights

    def forward(self, inputs):
        h = []
        for i in range(AI_N_HID):
            s = self.b1[i] + sum(self.w1[i][j] * inputs[j] for j in range(AI_N_IN))
            h.append(math.tanh(s))
        out = []
        for i in range(AI_N_OUT):
            s = self.b2[i] + sum(self.w2[i][j] * h[j] for j in range(AI_N_HID))
            out.append(math.tanh(s))
        steer = out[0]
        throttle = (out[1] + 1) / 2
        return steer, throttle

    def mutate(self, rate=0.12):
        def m(x): return x + random.gauss(0, 0.4) if random.random() < rate else x
        self.w1 = [[m(x) for x in row] for row in self.w1]
        self.b1 = [m(x) for x in self.b1]
        self.w2 = [[m(x) for x in row] for row in self.w2]
        self.b2 = [m(x) for x in self.b2]
    
    def crossover(self, other):
        def cx(a, b): return a if random.random() < 0.5 else b
        child = self.clone()
        child.w1 = [[cx(self.w1[i][j], other.w1[i][j]) for j in range(AI_N_IN)] for i in range(AI_N_HID)]
        child.b1 = [cx(self.b1[i], other.b1[i]) for i in range(AI_N_HID)]
        child.w2 = [[cx(self.w2[i][j], other.w2[i][j]) for j in range(AI_N_HID)] for i in range(AI_N_OUT)]
        child.b2 = [cx(self.b2[i], other.b2[i]) for i in range(AI_N_OUT)]
        return child
    
    def clone(self):
        return NeuralNetwork((
            [row[:] for row in self.w1], self.b1[:],
            [row[:] for row in self.w2], self.b2[:]
        ))

def ai_raycast(x, y, angle_rad, walls, max_cells=RAY_MAX):
    step = ZOOM_DEFAULT * 0.25
    max_dist = max_cells * ZOOM_DEFAULT
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    for d in range(1, int(max_dist / step) + 1):
        dist = d * step
        px = x + cos_a * dist
        py = y + sin_a * dist
        col = math.floor(px / ZOOM_DEFAULT)
        row = math.floor(py / ZOOM_DEFAULT)
        if (col, row) in walls:
            return dist / max_dist
    return 1.0

def ai_build_inputs(x, y, angle, speed, checkpoints, next_cp, walls):
    rays = []
    for deg in RAY_ANGLES:
        ray_angle = angle + math.radians(deg)
        rays.append(ai_raycast(x, y, ray_angle, walls))
    if checkpoints and next_cp < len(checkpoints):
        cp_col, cp_row = checkpoints[next_cp]
        cp_x = (cp_col + 0.5) * ZOOM_DEFAULT
        cp_y = (cp_row + 0.5) * ZOOM_DEFAULT
        dx, dy = cp_x - x, cp_x - y
        dist = math.hypot(dx, dy)
        desired = math.atan2(dy, dx)
        angle_err = ((desired - angle + math.pi) % (2 * math.pi) - math.pi) / math.pi
        dist_norm = min(dist / (RAY_MAX * ZOOM_DEFAULT), 1.0)
    else:
        angle_err = 0.0
        dist_norm = 0.0
    
    speed_norm = min(abs(speed) / Car.MAX_SPEED, 1.0)
    return rays + [angle_err, dist_norm, speed_norm]

def ai_simulate(nn, spawn_col, spawn_row, spawn_angle_deg, walls, checkpoints, finish_cells, loop_map):
    x = (spawn_col + 0.5) * ZOOM_DEFAULT
    y = (spawn_row + 0.5) * ZOOM_DEFAULT
    angle = math.radians(spawn_angle_deg)
    speed = 0.0
    next_cp = 0
    fitness = 0.0
    time_alive = 0.0
    cp_timer = 0.0
    left_start = False
    on_finish = True
    sector_times = []
    sector_colors = []
    sector_start = 0.0
    history = [(x, y, angle)]
    timing_history = [(0.0, 0, [], [])] #(lap_time, next_cp, sector_time, sector_colors)

    hw = Car.SIZE * ZOOM_DEFAULT * 1.6
    hh = Car.SIZE * ZOOM_DEFAULT * 0.8
    corner_offsets = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]

    def corner_world(px, py, cos_a, sin_a, cx, cy):
        return (px + cx * cos_a - cy * sin_a, py + cx * sin_a + cy * cos_a)
    
    def cell_of(wx, wy):
        return (math.floor(wx / ZOOM_DEFAULT), math.floor(wy / ZOOM_DEFAULT))
    
    def hits_wall(nx, ny, cos_a, sin_a):
        for cx, cy in corner_offsets:
            wx, wy = corner_world(nx, ny, cos_a, sin_a, cx, cy)
            if cell_of(wx, wy) in walls:
                return True
        return False

    if checkpoints:
        cp0 = checkpoints[0]
        best_dist = math.hypot(x - (cp0[0]+0.5)*ZOOM_DEFAULT, y - (cp0[1]+0.5)*ZOOM_DEFAULT)
    else:
        best_dist = 0.0

    MAX_SIM_TIME = CP_TIMEOUT * (len(checkpoints) + 1) if checkpoints else CP_TIMEOUT

    while time_alive < MAX_SIM_TIME:
        inputs = ai_build_inputs(x, y, angle, speed, checkpoints, next_cp, walls)
        steer, throttle = nn.forward(inputs)

        if abs(speed) > 25:
            sf = abs(speed) / Car.MAX_SPEED
            angle += steer * Car.TURN_SPEED * SIM_DT * (0.45 + 0.3 * sf) * math.copysign(1, speed)
            
        if throttle > 0.3:
            speed += Car.ACCEL * SIM_DT
        else:
            if abs(speed) < Car.FRICTION * SIM_DT:
                speed = 0.0
            else:
                speed -= math.copysign(Car.FRICTION * SIM_DT, speed)
        speed = max(-Car.MAX_SPEED * 0.5, min(Car.MAX_SPEED, speed))

        new_x = x + math.cos(angle) * speed * SIM_DT
        new_y = y + math.sin(angle) * speed * SIM_DT
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        if hits_wall(new_x, new_y, cos_a, sin_a):
            fitness -= 500
            break

        x, y = new_x, new_y
        time_alive += SIM_DT
        cp_timer += SIM_DT
        fitness += max(speed, 0) * SIM_DT * 0.1
        history.append((x, y, angle))
        timing_history.append((time_alive, next_cp, list(sector_times), list(sector_colors)))
        if checkpoints and next_cp < len(checkpoints):
            cp_col, cp_row = checkpoints[next_cp]
            cp_x = (cp_col + 0.5) * ZOOM_DEFAULT
            cp_y = (cp_row + 0.5) * ZOOM_DEFAULT
            dist_now = math.hypot(x - cp_x, y - cp_y)

            if dist_now < best_dist:
                fitness += (best_dist - dist_now) * 2.0
                best_dist = dist_now

            if dist_now < ZOOM_DEFAULT * 1.2:
                fitness += 2000
                t_sec = time_alive - sector_start
                sector_start = time_alive
                if sector_times and t_sec < min(sector_times):
                    sector_colors.append(BEST)
                elif sector_times:
                    sector_colors.append(BETTER if t_sec < sector_times[-1] else BAD)
                else:
                    sector_colors.append(BETTER)
                sector_times.append(t_sec)
                next_cp += 1
                cp_timer = 0.0
                if next_cp < len(checkpoints):
                    nc = checkpoints[next_cp]
                    best_dist = math.hypot(x - (nc[0]+0.5) * ZOOM_DEFAULT, y - (nc[1]+0.5)*ZOOM_DEFAULT)

        if cp_timer > CP_TIMEOUT:
            break

        all_cp_done = not checkpoints or next_cp > len(checkpoints)
        if all_cp_done and finish_cells:
            cur_cell = cell_of(x, y)
            if not left_start:
                if cur_cell not in finish_cells:
                    left_start = True
            elif cur_cell in finish_cells and not on_finish:
                fitness += 10000
                fitness -= time_alive * 5
                break
            on_finish = cur_cell in finish_cells

    return fitness, history, timing_history

def draw_training_screen(screen, font, font_small, gen, total_gens, best_fitness, log, cancel_rect, watch_buttons):
    screen.fill(BGC)
    title = font.render("Training AI..", True, TEXTC)
    screen.blit(title, (WIN_W // 2 - title.get_width() // 2, 40))
    if gen >= 0:
        prog = font_small.render(f"Generation {gen + 1} / {total_gens}", True, TEXTBUTLESSVISIBLEC)
        screen.blit(prog, (WIN_W // 2 - prog.get_width() // 2, 80))
        bar_w = int((gen + 1) / total_gens * 600)
        pygame.draw.rect(screen, (50, 55, 60), (WIN_W // 2 - 300, 110, 600, 16), border_radius=4)
        pygame.draw.rect(screen, BETTER, (WIN_W // 2 - 300, 110, bar_w, 16), border_radius=4)
        fit = font_small.render(f"Best fitness: {best_fitness:.0f}", True, BETTER)
        screen.blit(fit, (WIN_W // 2 - fit.get_width() // 2, 138))

        #log list
        y = 180
        for entry in log:
            g, f, has_watch = entry
            row_text = f"Gen {g+1:>3} - fitness {f:.0f}"
            col = BETTER if f == max(e[1] for e in log) else TEXTBUTLESSVISIBLEC
            s = font_small.render(row_text, True, col)
            screen.blit(s, (WIN_W // 2 - 260, y))

            btn_rect = watch_buttons.get(g)
            if btn_rect:
                hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
                pygame.draw.rect(screen, HOVERC if hovered else NORMAL, btn_rect, border_radius =3)
                pygame.draw.rect(screen, MENU_BORDERC, btn_rect, width=1, border_radius = 3)
                lbl = font_small.render("Watch", True, TEXTC)
                screen.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2, btn_rect.centery - lbl.get_height() // 2))

            y += 26
            if y > WIN_H - 120:
                break

        hovered = cancel_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, BAD if hovered else NORMAL, cancel_rect, border_radius = 8)
        pygame.draw.rect(screen, BAD, cancel_rect, width = 1, border_radius = 8)
        lbl = font.render("Cancel training", True, TEXTC)
        screen.blit(lbl, (cancel_rect.centerx - lbl.get_width() // 2, cancel_rect.centery - lbl.get_height() // 2))
        hint = font_small.render("Training runs headlessly - click  Watch  to replay any generation's best run", True, TEXTBUTLESSVISIBLEC)
        screen.blit(hint, (WIN_W // 2 - hint.get_width() // 2, WIN_H - 40))
        pygame.display.flip()

def run_replay(screen, clock, font, font_small, history, timing_history, gen_num, walls, checkpoints, finish_cells, cam_x, cam_y, zoom):
    running = True
    frame = 0
    while running and frame < len(history):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
        
        x, y, angle = history[frame]
        if frame < len(timing_history):
            lap_t, n_cp, s_times, s_colors = timing_history[frame]
        else:
            lap_t, n_cp, s_times, s_colors = 0.0, 0, [], []
        frame += 1
        scale = zoom / ZOOM_DEFAULT
        cam_x = WIN_W / 2 - x * scale
        cam_y = (WIN_H - MENU_H) / 2 - y * scale
        screen.fill(BGC)
        draw_grid(screen, cam_x, cam_y, zoom)
        for (c, r) in walls:
            draw_tile(screen, c, r, WALLC, font_small, None, cam_x, cam_y, zoom)
        for (c, r) in finish_cells:
            draw_tile(screen, c, r, FINISHC, font_small, "F", cam_x, cam_y, zoom)
        for idx, (c, r) in enumerate(checkpoints):
            draw_tile(screen, c, r, CPC, font_small, str(idx + 1), cam_x, cam_y, zoom)

        #draw agent (just a rectangle)
        s_x = x * scale + cam_x
        s_y = y * scale + cam_y
        hw = Car.SIZE * zoom * 1.6
        hh = Car.SIZE * zoom * 0.8
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        corners_s = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = [(s_x + cx * cos_a - cy * sin_a, s_y + cx * sin_a + cy * cos_a) for cx, cy in corners_s]
        pygame.draw.polygon(screen, BEST, pts)
        pygame.draw.polygon(screen, (255, 255, 255), pts, 1)
        lbl = font_small.render(str(gen_num + 1), True, (255, 255, 255))
        screen.blit(lbl, (int(s_x) - lbl.get_width() // 2, int(s_y) - lbl.get_height() // 2))
        
        hud_x, hud_y = 24, 24
        pad = 6
        hud_lines = [
            (f"Time: {fmt_time(lap_t)}", TEXTC),
            (f"Last lap: --:--.---", TEXTBUTLESSVISIBLEC),
            (f"Best lap: --:--.---", TEXTBUTLESSVISIBLEC)
        ]
        total_sectors = len(checkpoints) + 1
        for i in range(total_sectors):
            if i < len(s_colors):
                col = s_colors[i]
            elif i == n_cp:
                col = TEXTC
            else:
                col = TEXTBUTLESSVISIBLEC
            t_str = fmt_time(s_times[i]) if i < len(s_times) else "--:--.---"
            hud_lines.append((f"S{i+1} {t_str}", col))
        bg_w = 280
        bg_h = len(hud_lines)* 22 + pad * 2
        bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        screen.blit(bg, (hud_x - pad, hud_y - pad))
        for text, col, in hud_lines:
            s = font_small.render(text, True, col)
            screen.blit(s, (hud_x, hud_y))
            hud_y += 22
        
        pygame.draw.rect(screen, MENUC, (0, WIN_H - MENU_H, WIN_W, MENU_H))
        pygame.draw.rect(screen, MENU_BORDERC, (0, WIN_H - MENU_H, WIN_W, WIN_H - MENU_H), 1)
        info = font_small.render(f"Replaying Gen {gen_num + 1} - Esc to stop", True, TEXTBUTLESSVISIBLEC)
        screen.blit(info, (24, WIN_H - MENU_H + 20))
        elapsed = frame * SIM_DT
        time_s = font_small.render(f"GEN {gen_num + 1} - Time: {fmt_time(elapsed)}", True, TEXTC)
        screen.blit(time_s, (WIN_W // 2 - time_s.get_width() // 2, 20))
        pygame.display.flip()
        clock.tick(120)

    return True

def export_map(state):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    path = filedialog.asksaveasfilename(
        defaultextension = "json",
        filetypes = [("JSON map files", "*.json")],
        title = "Export map"
    )
    root.destroy()
    if path:
        with open(path, "w") as f:
            f.write(state.to_json())
        return True
    return False

def import_map(state):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    path = filedialog.askopenfilename(
        filetypes = [("JSON map files", "*.json")],
        title = "Import map"
    )
    root.destroy()
    if not path:
        return False
    with open(path) as f:
        data = json.load(f)
        state.walls = {tuple(t) for t in data.get("walls", [])}
        state.spawn = {tuple(t) for t in data.get("spawn", [])}
        state.finish = {tuple(t) for t in data.get("finish", [])}
        state.checkpoints = [tuple(t) for t in data.get("checkpoints", [])]
        state.spawn_angle = data.get("spawn_angle", 0.0)
        state.history = []
        return True
    
def draw_io_popup(surf, font, font_small, mouse_pos):
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    panel_w, panel_h = 400, 200
    panel_x = WIN_W // 2 - panel_w // 2
    panel_y = WIN_H // 2 - panel_h // 2
    pygame.draw.rect(surf, (20, 24, 30), (panel_x, panel_y, panel_w, panel_h), border_radius = 12)
    title = font.render("Map file", True, TEXTC)
    surf.blit(title, (WIN_W // 2 - title.get_width() // 2, panel_y + 20))
    hint = font_small.render("Esc to cancel", True, TEXTBUTLESSVISIBLEC)
    surf.blit(hint, (WIN_W // 2 - hint.get_width() // 2, panel_y + panel_x - 24))

    btn_w, btn_h = 140, 50
    gap = 20
    export_rect = pygame.Rect(WIN_W // 2 - btn_w - gap // 2, panel_y + 80, btn_w, btn_h)
    import_rect = pygame.Rect(WIN_W // 2 + gap // 2, panel_y + 80, btn_w, btn_h)

    for rect, label, sub in [
        (export_rect, "Export", "save to file"),
        (import_rect, "Import", "load from file")
    ]:
        hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(surf, HOVERC if hovered else NORMAL, rect, border_radius = 8)
        pygame.draw.rect(surf, MENU_BORDERC, rect, width = 1, border_radius = 8)
        lbl = font.render(label, True, TEXTC)
        sub_s = font_small.render(sub, True, TEXTBUTLESSVISIBLEC)
        surf.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2 - 8))
        surf.blit(sub_s, (rect.centerx - sub_s.get_width() // 2, rect.centery + 6))

    return export_rect, import_rect

def make_car(state, car_sprites, selected_car_idx):
    col, row = next(iter(state.spawn))
    return Car(col, row, sprite=car_sprites[selected_car_idx], spawn_angle_deg=state.spawn_angle, checkpoints=list(state.checkpoints), finish=set(state.finish),loop_map=state.is_loop())

def main():
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Map Editor")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("segoeui", 18, bold=True)
    font_small = pygame.font.SysFont("segoeui", 13)
    font_label = pygame.font.SysFont("segoeui", 14, bold=True)
    font_hint = pygame.font.SysFont("segoeui", 13)

    car_sprites = []
    for cd in CAR_DEFS:
        try:
            img = pygame.image.load(cd["file"]).convert_alpha()
            car_sprites.append(img)
        except:
            car_sprites.append(None)

    state = MapState()
    active_tool = WALL_TOOL # default tool
    painting = False
    erasing = False
    last_cell = None

    cam_x, cam_y = float(WIN_W // 2), float(WIN_H // 2)
    zoom = float(ZOOM_DEFAULT)
    panning = False
    pan_start = None
    pan_origin = None

    editor_cam = (cam_x, cam_y, zoom)
    mode = "editor"
    car = None
    warning_msg = ""
    warning_timer =0.0
    selected_car_idx = 0
    r_held = False

    ai_log = [] #list of gen, fitness has_history
    ai_histories = {} # gen -> history list
    ai_watch_btns = {} # gen _> pygame.Rect (built during draw)
    ai_cancelled = False
    ai_training_active = False

    menu_y = WIN_H - MENU_H
    n = len(TOOLS)
    spacing = 180
    total_w = spacing * (n-1)
    start_x = WIN_W // 2 - total_w // 2
    buttons = [
        ToolButton(start_x + i*spacing, menu_y + MENU_H//2, tool)
        for i, tool in enumerate(TOOLS)
    ]

    running = True
    while running:
        dt = min(clock.tick(120) / 1000.0, 0.05 )
        mouse_pos = pygame.mouse.get_pos()
        mx, my = mouse_pos

        #When cell hovered
        hover_column, hover_row = screen_to_grid(mx, my, cam_x, cam_y, zoom)
        in_grid = my < WIN_H-MENU_H

        if warning_timer > 0:
            warning_timer -= dt

        r_held = pygame.key.get_pressed()[pygame.K_r]

        for btn in buttons:
            btn.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if mode == "select":
                        mode = "editor"
                    elif mode == "results":
                        mode = "editor"
                        cam_x, cam_y, zoom = editor_cam
                        car = None
                    elif mode == "training":
                        ai_cancelled = True
                        mode = "editor"
                        cam_x, cam_y, zoom = editor_cam
                    elif mode == "io_popup":
                        mode = "editor"
                    else:
                        running = False

                elif event.key == pygame.K_TAB:
                    if mode == "editor":
                        if not state.spawn:
                            warning_msg = "Place a spawn point first!"
                            warning_timer = 2.5
                        else:
                            editor_cam = (cam_x, cam_y, zoom)
                            mode = "select"

                    elif mode == "select":
                        col, row = next(iter(state.spawn))
                        car = make_car(state, car_sprites, selected_car_idx)
                        zoom = float(ZOOM_DEFAULT)
                        mode = "drive"
                    elif mode == "results":
                        mode = "editor"
                        cam_x, cam_y, zoom = editor_cam
                        car = None

                    else:
                        mode = "editor"
                        cam_x,cam_y, zoom = editor_cam
                        car = None
                
                elif event.key == pygame.K_LEFT and mode == "select":
                    selected_car_idx = (selected_car_idx - 1)%len(CAR_DEFS)
                elif event.key == pygame.K_RIGHT and mode == "select":
                    selected_car_idx = (selected_car_idx + 1)%len(CAR_DEFS)
                elif event.key == pygame.K_RETURN and mode == "select":
                    col, row = next(iter(state.spawn))
                    car = make_car(state, car_sprites, selected_car_idx)
                    zoom = float(ZOOM_DEFAULT)
                    mode = "drive"
                elif mode == "results" and car:
                    prev_best_lap = car.best_lap
                    prev_best_sectors = list(car.best_sectors)
                    car = make_car(state, car_sprites, selected_car_idx)
                    car.best_lap = prev_best_lap
                    car.best_sectors = prev_best_sectors
                    zoom = float(ZOOM_DEFAULT)
                    mode = "drive"
                elif mode == "editor":
                    if event.key in KEYS:
                        active_tool = KEYS[event.key]
                    elif event.key == pygame.K_z and(event.mod & pygame.KMOD_CTRL):
                        state.undo()
                    elif event.key == pygame.K_RETURN:
                        mode = "io_popup"

                    elif event.key == pygame.K_t:
                        if not state.spawn:
                            warning_msg = "Place a spawn point first!"
                            warnin_timer = 2.5
                        else:
                            editor_cam = (cam_x, cam_y, zoom)
                            ai_log = []
                            ai_histories = {}
                            ai_watch_btns = {}
                            ai_cancelled = False
                            mode = "training"

            elif event.type == pygame.MOUSEBUTTONDOWN and mode == "select":
                if event.button == 1:
                    hovered = draw_select_popup(screen, CAR_DEFS, car_sprites, selected_car_idx, mouse_pos, font, font_small)
                    if hovered is not None:
                        if hovered == selected_car_idx:
                            col, row = next(iter(state.spawn))
                            car = make_car(state, car_sprites, selected_car_idx)
                            zoom = float(ZOOM_DEFAULT)
                            mode = "drive"
                        else:
                            selected_car_idx = hovered

            elif event.type == pygame.MOUSEBUTTONDOWN and mode =="editor":
                if event.button == 1:
                    clicked_btn = False
                    for btn in buttons:
                        if btn.rect.collidepoint(mouse_pos):
                            active_tool = btn.tool
                            clicked_btn = True
                            break
                    if not clicked_btn and in_grid:
                        state.push_history()
                        painting = True
                        last_cell = None
                        state.apply_tool(hover_column, hover_row, active_tool)
                        last_cell = (hover_column, hover_row)
                elif event.button == 3 and in_grid:
                    state.push_history()
                    erasing = True
                    last_cell = None
                    state.apply_tool(hover_column, hover_row, ERASE_TOOL)
                    last_cell = (hover_column, hover_row)
                elif event.button == 2:
                    panning = True
                    pan_start = (mx, my)
                    pan_origin = (cam_x, cam_y)
                
            elif event.type == pygame.MOUSEMOTION and mode == "editor":
                cell = (hover_column, hover_row)
                if painting and in_grid and cell != last_cell:
                    if last_cell:
                        for (c, r) in cells_between(last_cell[0], last_cell[1], hover_column, hover_row):
                            state.apply_tool(c, r, active_tool)
                    else:
                        state.apply_tool(hover_column, hover_row, active_tool)
                    last_cell = cell
                elif erasing and in_grid and cell != last_cell:
                    if last_cell:
                        for (c, r) in cells_between(last_cell[0], last_cell[1], hover_column, hover_row):
                            state.apply_tool(c, r, ERASE_TOOL)
                    else:
                        state.apply_tool(hover_column, hover_row, ERASE_TOOL)
                    last_cell = cell
                elif panning:
                    cam_x = pan_origin[0] + (mx - pan_start[0])
                    cam_y = pan_origin[1] + (my - pan_start[1])

            elif event.type == pygame.MOUSEBUTTONUP and mode == "editor":
                if event.button == 1: 
                    painting = False
                if event.button == 3: 
                    erasing = False
                    last_cell = None
                if event.button == 2:
                    panning = False

            elif event.type == pygame.MOUSEWHEEL and mode == "editor":
                if r_held and state.spawn:
                    state.spawn_angle = (state.spawn_angle + event.y * 5) % 360
                else:
                    zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))
                    old_zoom = zoom
                    zoom_factor = 1.1
                    cam_x = mx - (mx - cam_x) * zoom / old_zoom
                    cam_y = my - (my - cam_y) * zoom / old_zoom
                    
                    if event.y > 0:
                        zoom *= zoom_factor
                    else:
                        zoom /= zoom_factor
                

        if mode == "training" and not ai_cancelled:
            gen = len(ai_log)
            if gen < GENERATIONS:
                if gen == 0:
                    population = [NeuralNetwork() for _ in range(POP_SIZE)]
                else:
                    population = ai_histories.get('_population', [NeuralNetwork() for _ in range(POP_SIZE)])
                spawn_col, spawn_row = next(iter(state.spawn))
                scored = []
                for nn in population:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            ai_cancelled = True
                            break
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            ai_cancelled = True
                            break
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            cancel_rect = pygame.Rect(WIN_W // 2 - 120, WIN_H -100, 240, 44)
                            if cancel_rect.collidepoint(event.pos):
                                break
                    if ai_cancelled:
                        break
                    fit, hist, t_hist = ai_simulate(nn, spawn_col, spawn_row, state.spawn_angle, state.walls, list(state.checkpoints), set(state.finish), state.is_loop())
                    scored.append((fit, nn, hist, t_hist))

                if not ai_cancelled:
                    scored.sort(key=lambda x: x[0], reverse = True)
                    best_fit, best_nn_this_gen, best_hist, best_t_hist = scored[0]
                    ai_log.append((gen, best_fit, True))
                    ai_histories[gen] = (best_hist, best_t_hist)
                    survivors = [nn for _, nn, _, _ in scored[:SURVIVORS]]
                    weights = [SURVIVORS - i for i in range(SURVIVORS)]
                    new_pop = [scored[0][1].clone()]
                    stale = len(ai_log) > 5 and all(abs(ai_log[-i][1] - best_fit) < 50 for i in range(1, 6))
                    while len(new_pop) < POP_SIZE:
                        pa = random.choices(survivors, weights = weights, k=1)[0]
                        pb = random.choices(survivors, weights = weights, k=1)[0]
                        child = pa.crossover(pb) if pa is not pb else pa.clone()
                        child.mutate(rate=0.20 if stale else 0.12)
                        new_pop.append(child)
                    ai_histories['_population'] = new_pop
                    ai_watch_btns = {}
                    y_btn = 180
                    for entry in ai_log:
                        g = entry[0]
                        ai_watch_btns[g] = pygame.Rect(WIN_W // 2 + 80, y_btn, 80, 22)
                        y_btn += 26
                        if y_btn > WIN_H - 120:
                            break
            else:
                pass
        

        if mode == "drive" and car:
            car.update(dt, state.walls)
            if car.finished:
                mode = "results"
            else:
                scale = zoom / ZOOM_DEFAULT
                cam_x = WIN_W / 2 - car.x * scale
                cam_y = (WIN_H - MENU_H) / 2 - car.y * scale

        #drawing everything
        screen.fill(BGC)
        draw_grid(screen, cam_x, cam_y, zoom)

        loop = state.is_loop()
        for (c, r) in state.walls:
            draw_tile(screen, c, r, WALLC, font_label, None, cam_x, cam_y, zoom)
        for (c, r) in state.spawn:
            if loop:
                draw_split_tile(screen, c, r, cam_x, cam_y, zoom)
            else:
                draw_tile(screen, c, r, SPAWNC, font_label, None, cam_x, cam_y, zoom)
            draw_spawn_arrow(screen, c, r, state.spawn_angle, cam_x, cam_y, zoom)
        if not loop:
            for (c, r) in state.finish:
                draw_tile(screen, c, r, FINISHC, font_label, "F", cam_x, cam_y, zoom)
        if in_grid and not panning and mode in ("editor", "select"):
            draw_hover(screen, hover_column, hover_row, active_tool, cam_x, cam_y, zoom, font_label)
        
        for idx, (c, r) in enumerate(state.checkpoints):
            draw_tile(screen, c, r, CPC, font_label, str(idx + 1), cam_x, cam_y, zoom)
        
        if mode == "editor" and in_grid and not panning:
            draw_hover(screen, hover_column, hover_row, active_tool, cam_x, cam_y, zoom, font_label)

        if mode in ("drive", "results")and car:
            car.draw(screen, cam_x, cam_y, zoom)
            if mode == "drive":
                car.draw_hud(screen, font, font_small)

        pygame.draw.rect(screen, MENUC, (0, WIN_H - MENU_H, WIN_W, MENU_H))
        pygame.draw.line(screen, MENU_BORDERC, (0, WIN_H - MENU_H), (WIN_W, WIN_H - MENU_H), 1)

        if mode == "editor":
            for btn in buttons:
                btn.draw(screen, active_tool, font, font_small)

            hints = ["left click to place | right click to erase",
                 "middle mouse to pan | scroll to zoom",
                 "CTRL + z to undo | Enter to print JSON file",
                 "Tab to switch to drive mode | Esc to quit"
                ]
            hx, hy = 24, WIN_H - MENU_H + 14
            for h in hints:
                surf = font_hint.render(h, True, TEXTBUTLESSVISIBLEC)
                screen.blit(surf, (hx, hy))
                hy += 16

            #active tool indicator
            tool_str = f"Tool: {LABEL[active_tool]}"
            ts = font.render(tool_str, True, TOOL_COLORS[active_tool])
            screen.blit(ts, (WIN_W - ts.get_width() - 24, WIN_H - MENU_H + 20))

            #cell coord under cursor
            if in_grid:
                coord = font_hint.render(f"({hover_column}, {hover_row})", True, TEXTBUTLESSVISIBLEC)
                screen.blit(coord, (WIN_W - coord.get_width() - 24, WIN_H - MENU_H + 46))

            if active_tool == SPAWN_TOOL and state.spawn:
                ang_str = f"Spawn angle: {int(state.spawn_angle)}° (Hold r and scroll to rotate)"

            map_type = "Loop map" if loop else "Point-to-point"
            mt_s = font_hint.render(map_type, True, SPAWNC if loop else CPC)
            screen.blit(mt_s, (WIN_W // 2  - mt_s.get_width() // 2, WIN_H - MENU_H - 40))

            
            if warning_timer > 0:
                w = font.render(warning_msg, True, FINISHC)
                screen.blit(w, (WIN_W // 2 - w.get_width()//2, WIN_H - MENU_H - 40))
        
        elif mode == "select":
            draw_select_popup(screen, CAR_DEFS, car_sprites, selected_car_idx, mouse_pos, font, font_small)

        elif mode == "results" and car:
            retry_rect, back_rect = draw_results(screen, car, font, font_small, mouse_pos)
            for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                if event.button == 1:
                    if retry_rect.collidepoint(event.pos):
                        prev_best_lap = car.best_lap
                        prev_best_sectors = list(car.best_sectors)
                        car = make_car(state, car_sprites, selected_car_idx)
                        car.best_lap = prev_best_lap
                        car.best_sectors = prev_best_sectors
                        zoom = float(ZOOM_DEFAULT)
                        mode = "drive"
                    elif back_rect.collidepoint(event.pos):
                        mode = "editor"
                        cam_x, cam_y, zoom = editor_cam
                        car = None

        elif mode == "training":
            gen_done = len(ai_log)
            best_fit = ai_log[-1][1] if ai_log else 0.0
            cancel_rect = pygame.Rect(WIN_W // 2 - 120, WIN_H - 86, 240, 44)
            draw_training_screen(screen, font, font_small, gen_done - 1, GENERATIONS, best_fit, ai_log, cancel_rect, ai_watch_btns)
            for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                if event.button == 1:
                    if cancel_rect.collidepoint(event.pos):
                        ai_cancelled = True
                        mode = "editor"
                        cam_x, cam_y, zoom = editor_cam
                    else:
                        for g, btn_rect in ai_watch_btns.items():
                            if btn_rect.collidepoint(event.pos) and g in ai_histories:
                                hist, t_hist = ai_histories[g]
                                run_replay(screen, clock, font, font_small, hist, t_hist, g, state.walls, list(state.checkpoints), set(state.finish), cam_x, cam_y, zoom)
                                break
            
        elif mode == "io_popup":
            export_rect, import_rect = draw_io_popup(screen, font, font_small, mouse_pos)
            for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                if event.button == 1:
                    if export_rect.collidepoint(event.pos):
                        export_map(state)
                        mode = "editor"
                    elif import_rect.collidepoint(event.pos):
                        if import_map(state):
                            if state.spawn:
                                sc, sr = next(iter(state.spawn))
                                cam_x = WIN_W / 2 - (sc + 0.5) * ZOOM_DEFAULT * (zoom / ZOOM_DEFAULT)
                                cam_y = WIN_H / 2 - (sr + 0.5) * ZOOM_DEFAULT * (zoom / ZOOM_DEFAULT)
                        mode = "editor"

        else:
            hints = [
                "Arrow keys / WASD to drive",
                "Tab to switch to editor mode | Esc to quit"
            ]
            hx, hy = 24, WIN_H - MENU_H + 22
            for h in hints:
                s = font_hint.render(h, True, TEXTBUTLESSVISIBLEC)
                screen.blit(s, (hx, hy))
                hy += 18
            spd = font.render(f"Speed: {abs(int(car.speed))} px/s", True, TEXTC)
            screen.blit(spd, (WIN_W - spd.get_width() - 24, WIN_H - MENU_H + 28))

            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()