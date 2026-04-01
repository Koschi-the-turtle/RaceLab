import pygame
import sys

WIN_W, WIN_H = 1920, 1080
CELL = 20 #grid cell size
MENU_H = 0 #it's supposed to be the toolbar but because of the unprecented amount of terms starting with "tool" all over this program as well as for the sake of this code's overall readability, I took the more or less wise decision to call it "menu" (it's just my lazy ass can't write shit longer than 4 letters...) <- useless ahh comment just go to bed already aaaah t orange bouin
G_COLUMN = WIN_W//CELL
G_ROW = (WIN_H - MENU_H)//CELL

#colors✨
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


#Tools

WALL_TOOL = "wall"
ERASE_TOOL = "erase"
SPAWN_TOOL = "spawn"
FINISH_TOOL = "finish"

TOOLS = [WALL_TOOL, SPAWN_TOOL, FINISH_TOOL, ERASE_TOOL]

LABEL= {
    WALL_TOOL: "Wall",
    SPAWN_TOOL: "Spawn",
    FINISH_TOOL: "Finish",
    ERASE_TOOL: "Erase"
}

KEYS = {
    pygame.K_w: WALL_TOOL,
    pygame.K_s: SPAWN_TOOL,
    pygame.K_f: FINISH_TOOL,
    pygame.K_e: ERASE_TOOL
}

TOOL_COLORS = {
    WALL_TOOL: WALLC,
    SPAWN_TOOL: SPAWNC,
    FINISH_TOOL: FINISHC,
    ERASE_TOOL: BGC
}

class MapState:
    def __init__(self):
        self.walls = set()
        self.spawn = set()
        self.finish = set()
        self.history = []

    def snapshot(self):
        return {
            "walls": set(self.walls),
            "spawn": set(self.spawn),
            "finish": set(self.finish)
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

    def apply_tool(self, col, row, tool):
        if not(0 <= col < G_COLUMN and 0<= row < G_ROW):
            return
        if tool == WALL_TOOL:
            self.walls.add((col, row))
            self.spawn.discard((col, row))
            self.finish.discard((col, row))
        elif tool == SPAWN_TOOL:
            self.walls.discard((col, row))
            self.spawn.clear()
            self.spawn.add((col, row))
        elif tool == FINISH_TOOL:
            self.walls.discard((col, row))
            self.spawn.discard((col, row))
            self.finish.clear()
            self.finish.add((col, row))
        elif tool == ERASE_TOOL:
            self.walls.discard((col, row))
            self.spawn.discard((col, row))
            self.finish.discard((col, row))

    
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
        key_hints = {WALL_TOOL: "W", SPAWN_TOOL:"S", FINISH_TOOL:"F", ERASE_TOOL:"E"}
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

def draw_tile(surf, col, row, color, font, label, alpha=255):
    x = col*CELL
    y = row*CELL
    cx = col*CELL + CELL//2
    cy = row*CELL  + CELL//2
    if alpha<255:
        s = pygame.Surface((CELL - 1, CELL - 1), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surf.blit(s, (x + 1, y + 1))
    else:
        pygame.draw.rect(surf, color, (x + 1, y + 1, CELL - 1, CELL - 1))
    lbl = font.render(label, True, BGC)
    surf.blit(lbl, (cx - lbl.get_width() //2, cy - lbl.get_height() // 2))
    
def draw_entity(surf, col, row, color, font, label):
    cx = col*CELL + CELL//2
    cy = row*CELL  + CELL//2
    r = CELL//2 - 4
    pygame.draw.circle(surf, color, (cx, cy), r)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r, 2)
    lbl = font.render(label, True, BGC)
    surf.blit(lbl, (cx - lbl.get_width() //2, cy - lbl.get_height() // 2))

def draw_grid(surf):
    for c in range(G_COLUMN + 1):
        x = c*CELL
        pygame.draw.line(surf, GRIDC, (x, 0), (x, WIN_H - MENU_H))
    for r in range(G_ROW + 1):
        y = r*CELL
        pygame.draw.line(surf, GRIDC, (0, y), (WIN_W, y))

def draw_hover(surf, col, row, tool):
    if not (0 <= col < G_COLUMN and 0 <= row < G_ROW):
        return
    color = TOOL_COLORS.get(tool, BGC)
    font = pygame.font.SysFont("segoeui", 18, bold=True)
    draw_tile(surf, col, row, color, font, None, alpha=100)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Map Editor")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("segoeui", 18, bold=True)
    font_small = pygame.font.SysFont("segoeui", 13)
    font_label = pygame.font.SysFont("segoeui", 14, bold=True)
    font_hint = pygame.font.SysFont("segoeui", 13)

    state = MapState()
    active_tool = WALL_TOOL # default tool
    painting = False
    erasing = False
    last_cell = None

    menu_y = WIN_H - MENU_H
    n = len(TOOLS)
    spacing = 180
    total_w = spacing * (n-1)
    start_x = WIN_W // 2 - total_w // 2
    buttons = [
        ToolButton(start_x + i*spacing, menu_y + MENU_H//2, tool)
        for i, tool in enumerate(TOOLS)
    ]

    grid_surf = pygame.Surface((WIN_W, WIN_H - MENU_H))
    grid_surf.fill(BGC)
    draw_grid(grid_surf)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mx, my = mouse_pos

        #When cell hovered
        hover_column = mx//CELL
        hover_row = my//CELL
        in_grid = my < WIN_H-MENU_H

        for btn in buttons:
            btn.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEYS:
                    active_tool = KEYS[event.key]
                elif event.key == pygame.K_z and(event.mod & pygame.KMOD_CONTROL):
                    state.undo()
                elif event.key == pygame.K_RETURN:
                    print("Map JSON: \n", state.to_json()) #To do later, does nothing rn :|

            elif event.type == pygame.MOUSEBUTTONDOWN:
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
                
            elif event.type == pygame.MOUSEMOTION:
                cell = (hover_column, hover_row)
                if painting and in_grid and cell != last_cell:
                    state.apply_tool(hover_column, hover_row, active_tool)
                    last_cell = cell
                elif erasing and in_grid and cell != last_cell:
                    state.apply_tool(hover_column, hover_row, ERASE_TOOL)
                    last_cell = cell

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: painting = False
                if event.button == 3: erasing = False
                last_cell = None

        #drawing everything
        screen.blit(grid_surf, (0, 0))

        for (c, r) in state.walls:
            draw_tile(screen, c, r, WALLC, font_label, None)
        for (c, r) in state.spawn:
            draw_tile(screen, c, r, SPAWNC, font_label, "S")
        for (c, r) in state.finish:
            draw_tile(screen, c, r, FINISHC, font_label, "F")
        if in_grid:
            draw_hover(screen, hover_column, hover_row, active_tool)
        
        menu_rect = pygame.Rect(0, WIN_H - MENU_H, WIN_W, MENU_H)
        pygame.draw.rect(screen, MENUC, menu_rect)
        pygame.draw.line(screen, MENU_BORDERC, (0, WIN_H - MENU_H), (WIN_W, WIN_H - MENU_H), 1)

        for btn in buttons:
            btn.draw(screen, active_tool, font, font_small)

        hints = ["left click / drag to place",
                 "right click / drag to erase",
                 "CTRL + z to undo",
                 "Enter to print JSON file",
                 "Esc to quit"
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

        pygame.display.flip()
        clock.tick(90)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()