import pygame
import sys
import json
import math

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
            "finish": [list(t) for t in self.finish]
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
        hw = self.SIZE * ZOOM_DEFAULT
        hh = self.SIZE * ZOOM_DEFAULT * 0.6
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        
        def corner_world(px, py, cx, cy):
            return (px + cx * cos_a - cy * sin_a,
                    py + cx * sin_a + cy * cos_a)
        
        def in_wall(wx, wy):
            return (math.floor(wx / ZOOM_DEFAULT), math.floor(wy / ZOOM_DEFAULT)) in walls
        
        hitting = []
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
                wx, wy = corner_world(new_x, self.y, hitting [0][0], hitting [0][1])
                if not in_wall(wx, wy):
                    self.x = new_x
            if not block_y:
                wx, wy = corner_world(self.x, new_y, hitting[0][0], hitting[0][1])
                if not in_wall(wx, wy):
                    self.y = new_y
        
        self.lap_time += dt
        self.sector_time += dt
        cur_col = math.floor(self.x / ZOOM_DEFAULT)
        cur_row = math.floor(self.y / ZOOM_DEFAULT)
        cur_cell = (cur_col, cur_row)

        if cur_cell != self.last_cell:
            self.last_cell = cur_cell

            if self.checkpoints and self.next_cp < len(self.checkpoints):
                if cur_cell == self.checkpoints[self.next_cp]:
                    self._complete_sector(self.next_cp)
                    self.next_cp += 1
                    
            if cur_cell in self.finish_cells:
                all_cp_done = (not self.checkpoints) or (self.next_cp >= len(self.checkpoints))
                if all_cp_done:
                    self._complete_lap()
                    if not self.loop_map:
                        self.finished = True

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
    panel_y = WIN_W // 2 - panel_w // 2
    pygame.draw.rect(surf, (20, 24, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(surf, MENU_BORDERC, (panel_x, panel_y, panel_w, panel_h), width=1, border_radius=12)
    title = font.render("Select you car", True, TEXTC)
    surf.blit(title, (WIN_W//2 - title.get_width()//2, panel_y + 16))
    hint = font_small.render("Enter to confirm | Esc to cancel", True, TEXTBUTLESSVISIBLEC)
    surf.blit(hint, (WIN_W //2 - hint.get_width() //2, panel_y + panel_h - 24))
    hovered_idx = None
    cards_start_x = WIN_W // 2 - total_w // 2
    cards_y = panel_y + 52
    for i, car_def in enumerate(car_defs):
        cx = cards_start_x + i * (card_w + padding)
        card_r = pygame.Rect(cx, cards_y, card_w, card_h)
        hovered = card_r.collidepoint(mousepos)
        if hovered:
            hovered_idx = i

        active = i == selected_idx
        bg = ACTIVEC if active else (HOVERC if hovered else NORMAL)
        border = SPAWNC if active else (MENU_BORDERC if not hovered else TEXTBUTLESSVISIBLEC)
        bw = 2 if active else 1
        pygame.draw.rect(surf, bg, card_r, border_radius=8)
        pygame.draw.rect(sirf, border, card_r, width=bw, border_radius=8)
    
        sprite = car_sprites[i]
        if sprite:
            prev_h = card_h - 50
            prec_w = card_h // 2.4
            scaled = pygame.transform.scale(sprite, (prev_w, prev_h))
            rotated = pygame.transform.rotate(scaled, 90)
            r = rotated.get_rect(center=(cx + card_w //2, cards_y + (card_h - 36) // 2))
            surf.blir(rotated, r.topleft)
        else:
            pygame.draw.rect(surf, CARC, (cx + 20, cards_y + 20, card_w - 40, card_h - 60), border_radius=4)
            name_surf = font_small.render(car_def["name"], True, TEXTC if active else TEXTBUTLESSVISIBLEC)
            surf.blit(name_surf, (cx + card_w // 2 - name_surf.get_width() // 2, cards_y + card_h - 28))
    return hovered_idx

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
                        print("Map JSON: \n", state.to_json()) #To do later, does nothing rn :|

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