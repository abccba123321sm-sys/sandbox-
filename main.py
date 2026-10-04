import pygame
import random

pygame.init()
screen = pygame.display.set_mode((0, 0))
W, H = screen.get_size()
pygame.display.set_caption("Sandbox")
clock = pygame.time.Clock()
rnd = random.random

# ---------- Элементы ----------
(EMPTY, SAND, WATER, STONE, WOOD, FIRE, STEAM, LAVA, OIL, ICE, PLANT, ACID,
 METAL, GLASS, GUNPOWDER, SNOW, TNT, GRAVEL, MERCURY, HEAT, COLD,
 LN2, ANT, WORM, FISH, FIREFLY,
 BATTERY, WIRE, LAMP, FUSE, SWOFF, SWON, BOLT, SPARK, DIRT) = range(35)

COLORS = {
    EMPTY: (15, 15, 25),
    SAND: (230, 200, 110),
    WATER: (60, 120, 230),
    STONE: (120, 120, 130),
    WOOD: (130, 85, 40),
    FIRE: (255, 120, 20),
    STEAM: (200, 210, 225),
    LAVA: (230, 70, 20),
    OIL: (70, 50, 30),
    ICE: (160, 220, 245),
    PLANT: (40, 160, 60),
    ACID: (150, 230, 40),
    METAL: (150, 155, 165),
    GLASS: (170, 215, 225),
    GUNPOWDER: (60, 60, 60),
    SNOW: (240, 244, 250),
    TNT: (190, 40, 40),
    GRAVEL: (130, 125, 118),
    MERCURY: (190, 195, 205),
    HEAT: (255, 90, 40),
    COLD: (110, 190, 255),
    LN2: (170, 235, 255),
    ANT: (200, 60, 40),
    WORM: (240, 150, 170),
    FISH: (250, 190, 60),
    FIREFLY: (30, 45, 35),
    BATTERY: (60, 170, 70),
    WIRE: (190, 110, 50),
    LAMP: (230, 220, 150),
    FUSE: (170, 150, 110),
    SWOFF: (200, 60, 60),
    SWON: (60, 200, 90),
    BOLT: (40, 40, 90),
    SPARK: (255, 255, 200),
    DIRT: (110, 75, 45),
}

TOOLS = [
    ("Песок", SAND), ("Земля", DIRT), ("Вода", WATER), ("Камень", STONE), ("Дерево", WOOD),
    ("Огонь", FIRE), ("Пар", STEAM), ("Лава", LAVA), ("Масло", OIL),
    ("Лёд", ICE), ("Трава", PLANT), ("Кислота", ACID), ("Металл", METAL),
    ("Стекло", GLASS), ("Порох", GUNPOWDER), ("Снег", SNOW), ("Динамит", TNT),
    ("Гравий", GRAVEL), ("Ртуть", MERCURY), ("Азот", LN2), ("Нагрев", HEAT),
    ("Холод", COLD), ("Муравей", ANT), ("Червь", WORM), ("Рыба", FISH),
    ("Светляк", FIREFLY), ("Батарея", BATTERY), ("Провод", WIRE), ("Лампа", LAMP),
    ("Предохр.", FUSE), ("Рубильн.", SWON), ("Молния", BOLT), ("Ластик", EMPTY),
]
TOOLS_PER_ROW = 8

# ---------- Сетка ----------
ROW_H = max(60, H // 30)
UI_H = ROW_H * 6
COLS = 90
CELL = max(2, W // COLS)
COLS = W // CELL
ROWS = (H - UI_H) // CELL

grid = [[EMPTY] * COLS for _ in range(ROWS)]
stamp = [[0] * COLS for _ in range(ROWS)]
temp = [[0.0] * COLS for _ in range(ROWS)]
aux = [[0] * COLS for _ in range(ROWS)]      # направление движения животных
hot = set()          # клетки с ненулевой температурой
pending = []         # отложенные взрывы
batteries = set()    # координаты батарей
powered = set()      # клетки под напряжением
surge_seeds = []     # куда ударила молния
surge_timer = 0
frame = 0

current = SAND
brush = 2
paused = False
solid_gravity = False
noise = [[random.randint(0, 255) for _ in range(COLS)] for _ in range(ROWS)]

# ---------- Группы элементов ----------
ANIMALS = (ANT, WORM, FISH, FIREFLY)
ELEC = (BATTERY, WIRE, LAMP, FUSE, SWOFF, SWON)
CONDUCT = frozenset((BATTERY, WIRE, LAMP, FUSE, SWON, METAL, MERCURY))

# ---------- Плотность (тяжёлое тонет, лёгкое всплывает) ----------
D = {
    EMPTY: 0, STEAM: 0.1, SNOW: 0.5, WOOD: 0.6, PLANT: 0.7, OIL: 0.8, LN2: 0.81,
    ICE: 0.9, WATER: 1.0, ACID: 1.1, GUNPOWDER: 1.3, TNT: 1.5, SAND: 1.6,
    DIRT: 1.7, GRAVEL: 2.0, LAVA: 2.2, GLASS: 2.5, STONE: 2.6, METAL: 7.8, MERCURY: 13.5,
}
MOBILE = frozenset((EMPTY, STEAM, SNOW, OIL, LN2, WATER, ACID, GUNPOWDER, SAND,
                    DIRT, GRAVEL, LAVA, MERCURY))
SOLID_SET = frozenset((WOOD, PLANT, ICE, TNT, GLASS, STONE, METAL))
STATIC = (STONE, WOOD, GLASS, METAL, TNT)
SOLIDS = (STONE, WOOD, ICE, PLANT, METAL, GLASS, TNT,
          BATTERY, WIRE, LAMP, FUSE, SWON)    # рисуются без «зернистости»

COND = {METAL: 0.9, MERCURY: 0.6, WATER: 0.35, STONE: 0.4, GLASS: 0.4}

# ---------- Текстуры ----------
PAL = {
    SAND: [(232, 204, 120), (222, 192, 106), (238, 212, 134), (212, 182, 98)],
    WATER: [(52, 110, 225), (58, 120, 232), (46, 100, 214)],
    STONE: [(118, 118, 128), (104, 104, 114), (132, 132, 142), (96, 96, 106)],
    WOOD: [(135, 88, 42), (112, 70, 30), (150, 100, 52)],
    STEAM: [(205, 214, 228), (190, 200, 216), (220, 226, 238)],
    OIL: [(68, 48, 28), (56, 40, 24), (80, 58, 34)],
    ICE: [(165, 222, 248), (185, 235, 252), (145, 205, 238)],
    PLANT: [(44, 165, 64), (34, 140, 52), (58, 182, 78)],
    ACID: [(150, 232, 40), (130, 215, 30), (172, 245, 70)],
    METAL: [(150, 155, 165), (132, 137, 148), (168, 172, 182)],
    GLASS: [(170, 215, 225), (150, 200, 215), (185, 228, 238)],
    GUNPOWDER: [(60, 60, 60), (44, 44, 50), (76, 76, 70)],
    SNOW: [(240, 244, 250), (225, 232, 243), (250, 252, 255)],
    TNT: [(190, 40, 40), (168, 30, 30), (205, 55, 50)],
    GRAVEL: [(130, 125, 118), (105, 100, 95), (150, 145, 138), (90, 88, 85)],
    MERCURY: [(190, 195, 205), (170, 175, 188), (215, 220, 228)],
    LN2: [(150, 225, 250), (170, 238, 255), (190, 245, 255)],
    DIRT: [(110, 75, 45), (94, 62, 36), (126, 88, 55), (84, 54, 32)],
}
TOP = {
    WATER: (120, 175, 255),
    ICE: (225, 248, 255),
    PLANT: (100, 215, 110),
    OIL: (120, 95, 62),
    MERCURY: (240, 245, 250),
    METAL: (205, 210, 222),
    GLASS: (235, 248, 252),
    SNOW: (255, 255, 255),
    LN2: (235, 252, 255),
}

font = pygame.font.SysFont(None, max(16, ROW_H // 3))

# ---------- Кнопки ----------
buttons = []
bw = W // TOOLS_PER_ROW
for i, (name, el) in enumerate(TOOLS):
    r, c = divmod(i, TOOLS_PER_ROW)
    buttons.append((pygame.Rect(c * bw, H - UI_H + r * ROW_H, bw, ROW_H), name, el))

controls = ["minus", "plus", "clear", "pause", "gravity"]
cw = W // len(controls)
for i, key in enumerate(controls):
    buttons.append((pygame.Rect(i * cw, H - ROW_H, cw, ROW_H), key, key))

world_surf = pygame.Surface((COLS, ROWS))


def control_label(key):
    if key == "minus":
        return "Кисть -"
    if key == "plus":
        return "Кисть + (%d)" % brush
    if key == "clear":
        return "Очистить"
    if key == "pause":
        return "Пуск" if paused else "Пауза"
    if key == "gravity":
        return "Падение: " + ("ВКЛ" if solid_gravity else "ВЫКЛ")
    return key


def in_bounds(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS


def blend(a, b, f):
    return (int(a[0] + (b[0] - a[0]) * f),
            int(a[1] + (b[1] - a[1]) * f),
            int(a[2] + (b[2] - a[2]) * f))


# ---------- Температура ----------
def addheat(x, y, v):
    if grid[y][x] == METAL:
        v *= 0.6                  # у металла большая теплоёмкость — греется медленнее
    t = temp[y][x] + v
    if t > 700:
        t = 700
    elif t < -150:
        t = -150
    temp[y][x] = t
    hot.add((x, y))


def explode(cx, cy, r):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r:
                continue
            x, y = cx + dx, cy + dy
            if not in_bounds(x, y):
                continue
            c = grid[y][x]
            if c == EMPTY:
                if rnd() < 0.5:
                    grid[y][x] = FIRE
            elif c == METAL:
                addheat(x, y, 250)
            elif c == STONE:
                if rnd() < 0.6:
                    grid[y][x] = GRAVEL
            elif c == GLASS:
                if rnd() < 0.6:
                    grid[y][x] = EMPTY
            elif c == WATER:
                grid[y][x] = STEAM
            elif c == TNT:
                grid[y][x] = FIRE
                if (x, y) != (cx, cy):
                    pending.append((x, y))
            elif c == GUNPOWDER:
                grid[y][x] = FIRE
            else:
                grid[y][x] = FIRE if rnd() < 0.5 else EMPTY
            if grid[y][x] != METAL:
                temp[y][x] = 0.0


def thermal(x, y):
    """Что происходит с клеткой при её температуре."""
    c = grid[y][x]
    t = temp[y][x]
    if c == WOOD:
        if t > 140:
            grid[y][x] = FIRE
    elif c == PLANT:
        if t > 120:
            grid[y][x] = FIRE
    elif c == OIL:
        if t > 110:
            grid[y][x] = FIRE
    elif c == GUNPOWDER:
        if t > 130:
            grid[y][x] = FIRE
    elif c == TNT:
        if t > 150:
            grid[y][x] = FIRE
            pending.append((x, y))
    elif c == ICE or c == SNOW:
        if t > 8:
            grid[y][x] = WATER
            temp[y][x] = 0.0
    elif c == WATER:
        if t > 100:
            grid[y][x] = STEAM
            temp[y][x] = 0.0
        elif t < -15:
            grid[y][x] = ICE
            temp[y][x] = 0.0
    elif c == ACID:
        if t > 150:
            grid[y][x] = STEAM
            temp[y][x] = 0.0
    elif c == SAND:
        if t > 300:
            grid[y][x] = GLASS
    elif c == GLASS:
        if t > 480 and rnd() < 0.2:
            grid[y][x] = LAVA
            temp[y][x] = 380.0
    elif c == METAL:
        if t > 480 and rnd() < 0.05:      # металл плавится медленно
            grid[y][x] = LAVA
            temp[y][x] = 380.0
    elif c == WIRE:
        if t > 220:
            grid[y][x] = FIRE
    elif c == FUSE:
        if t > 150:
            grid[y][x] = FIRE
    elif c == SWON or c == SWOFF:
        if t > 220:
            grid[y][x] = FIRE
    elif c == LAMP:
        if t > 180:
            grid[y][x] = SPARK            # лампа лопается
    elif c == BATTERY:
        if t > 200:
            batteries.discard((x, y))
            explode(x, y, 3)              # перегретая батарея взрывается
    elif c == DIRT:
        if t > 400:
            grid[y][x] = STONE            # обжиг земли
    elif c == STONE:
        if t > 650:
            grid[y][x] = LAVA
            temp[y][x] = 450.0
    elif c == LAVA:
        if t < 200:
            grid[y][x] = STONE
    elif c == STEAM:
        if t < -10:
            grid[y][x] = WATER
            temp[y][x] = 0.0
    elif c in ANIMALS:
        if t > 100 or t < -40:
            grid[y][x] = EMPTY
            temp[y][x] = 0.0


def heat_step():
    for (x, y) in list(hot):
        c = grid[y][x]
        t = temp[y][x]
        if c == EMPTY or -1.0 < t < 1.0:
            temp[y][x] = 0.0
            hot.discard((x, y))
            continue
        k = COND.get(c, 0.3) * 0.25
        for dx, dy in NB:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] != EMPTY:
                d = (t - temp[ny][nx]) * k
                if d:
                    temp[y][x] -= d
                    temp[ny][nx] += d
                    hot.add((nx, ny))
        temp[y][x] *= 0.985
        thermal(x, y)


# ---------- Электричество ----------
def update_power():
    global powered, surge_timer
    seen = set()
    stack = []
    for p in list(batteries):
        if grid[p[1]][p[0]] == BATTERY:
            seen.add(p)
            stack.append(p)
        else:
            batteries.discard(p)
    if surge_timer > 0:
        surge_timer -= 1
        for p in surge_seeds:
            if p not in seen and grid[p[1]][p[0]] in CONDUCT:
                seen.add(p)
                stack.append(p)
        if surge_timer == 0:
            del surge_seeds[:]
    while stack:
        x, y = stack.pop()
        for dx, dy in NB:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in seen and grid[ny][nx] in CONDUCT:
                seen.add((nx, ny))
                stack.append((nx, ny))
    powered = seen
    for (x, y) in list(seen):
        if grid[y][x] == FUSE and rnd() < 0.12:
            grid[y][x] = FIRE          # предохранитель перегорел
            continue
        for dx, dy in NB:               # током бьёт живых существ
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and grid[ny][nx] in ANIMALS and rnd() < 0.3:
                grid[ny][nx] = EMPTY


def impact(x, y):
    global surge_timer
    c = grid[y][x]
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny):
                continue
            n = grid[ny][nx]
            if n == EMPTY or n == SPARK:
                continue
            if n in (WOOD, PLANT, OIL, GUNPOWDER):
                grid[ny][nx] = FIRE
            elif n == TNT:
                grid[ny][nx] = FIRE
                pending.append((nx, ny))
            elif n == SAND:
                grid[ny][nx] = GLASS
            elif n in ANIMALS:
                grid[ny][nx] = EMPTY
            elif n == WATER and rnd() < 0.5:
                grid[ny][nx] = STEAM
            if grid[ny][nx] != EMPTY:
                addheat(nx, ny, 250)
    if c in CONDUCT:
        surge_seeds.append((x, y))
        surge_timer = 12


def lightning(cx):
    x = max(0, min(COLS - 1, cx))
    y = 0
    while y < ROWS:
        c = grid[y][x]
        if c == EMPTY:
            grid[y][x] = SPARK
        elif c != SPARK:
            impact(x, y)
            return
        y += 1
        x = max(0, min(COLS - 1, x + random.choice((-1, 0, 0, 1))))


def toggle_switch(cx, cy):
    done = False
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x, y = cx + dx, cy + dy
            if in_bounds(x, y):
                if grid[y][x] == SWON:
                    grid[y][x] = SWOFF
                    done = True
                elif grid[y][x] == SWOFF:
                    grid[y][x] = SWON
                    done = True
    return done


# ---------- Рисование ----------
def paint(cx, cy):
    for dy in range(-brush, brush + 1):
        for dx in range(-brush, brush + 1):
            x, y = cx + dx, cy + dy
            if not in_bounds(x, y):
                continue
            if current == HEAT:
                if grid[y][x] != EMPTY:
                    addheat(x, y, 20)
            elif current == COLD:
                if grid[y][x] != EMPTY:
                    addheat(x, y, -20)
            elif current == EMPTY:
                grid[y][x] = EMPTY
                temp[y][x] = 0.0
            elif current == BOLT:
                pass
            elif current in ANIMALS:
                if (grid[y][x] == EMPTY or (current == FISH and grid[y][x] == WATER)) and rnd() < 0.06:
                    grid[y][x] = current
                    aux[y][x] = 1 if rnd() < 0.5 else -1
                    temp[y][x] = 0.0
            elif grid[y][x] == EMPTY:
                if current not in SOLIDS and rnd() < 0.3:
                    continue
                grid[y][x] = current
                temp[y][x] = 0.0
                if current == LAVA:
                    addheat(x, y, 400)
                elif current == BATTERY:
                    batteries.add((x, y))


def paint_line(x0, y0, x1, y1):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        paint(x0 + (x1 - x0) * i // steps, y0 + (y1 - y0) * i // steps)


# ---------- Физика ----------
NB = ((1, 0), (-1, 0), (0, 1), (0, -1))
NB8 = NB + ((1, 1), (-1, 1), (1, -1), (-1, -1))
DISSOLVABLE = (SAND, DIRT, STONE, WOOD, PLANT, ICE, GRAVEL, METAL, SNOW)


def swap(x, y, nx, ny):
    grid[y][x], grid[ny][nx] = grid[ny][nx], grid[y][x]
    ty = temp[y]
    tn = temp[ny]
    a = ty[x]
    b = tn[nx]
    if a or b:
        ty[x] = b
        tn[nx] = a
        hot.add((x, y))
        hot.add((nx, ny))
    stamp[y][x] = frame
    stamp[ny][nx] = frame


def can_pass(b, dc):
    """Может ли элемент плотностью dc вытеснить клетку b (пройти сквозь неё)."""
    if D.get(b, 99) >= dc:
        return False
    return b in MOBILE or (solid_gravity and b in SOLID_SET)


def fall(x, y, c, sideways, diag):
    dc = D[c]
    if y + 1 < ROWS and can_pass(grid[y + 1][x], dc):
        swap(x, y, x, y + 1)
        return
    ds = (-1, 1) if rnd() < 0.5 else (1, -1)
    if diag and y + 1 < ROWS:
        for d in ds:
            nx = x + d
            if 0 <= nx < COLS and can_pass(grid[y + 1][nx], dc):
                swap(x, y, nx, y + 1)
                return
    if sideways:
        for d in ds:
            nx = x + d
            if 0 <= nx < COLS and grid[y][nx] == EMPTY:
                swap(x, y, nx, y)
                return


def rise(x, y):
    ds = (-1, 1) if rnd() < 0.5 else (1, -1)
    if y > 0:
        up = grid[y - 1][x]
        if up == EMPTY or up == WATER or up == OIL or up == ACID:
            swap(x, y, x, y - 1)          # пар «пробулькивает» сквозь жидкость
            return
        for d in ds:
            nx = x + d
            if 0 <= nx < COLS and grid[y - 1][nx] == EMPTY:
                swap(x, y, nx, y - 1)
                return
    for d in ds:
        nx = x + d
        if 0 <= nx < COLS and grid[y][nx] == EMPTY:
            swap(x, y, nx, y)
            return


# ---------- Животные ----------
def amove(x, y, nx, ny):
    h = aux[y][x]
    swap(x, y, nx, ny)
    aux[ny][nx] = h
    aux[y][x] = 0


def deadly(x, y):
    for dx, dy in NB:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            n = grid[ny][nx]
            if n == FIRE or n == LAVA or n == ACID or n == SPARK:
                return True
    return False


def ant_step(x, y):
    if deadly(x, y):
        grid[y][x] = EMPTY
        return
    if y > 0 and grid[y - 1][x] == WATER and rnd() < 0.1:
        grid[y][x] = EMPTY             # утонул
        return
    below = grid[y + 1][x] if y + 1 < ROWS else STONE
    if below == EMPTY or below == STEAM:
        amove(x, y, x, y + 1)          # падает
        return
    if rnd() < 0.35:
        return
    h = aux[y][x]
    if h == 0 or rnd() < 0.08:
        h = 1 if rnd() < 0.5 else -1
    aux[y][x] = h
    nx = x + h
    if not 0 <= nx < COLS:
        aux[y][x] = -h
        return
    t = grid[y][nx]
    if t == EMPTY:
        amove(x, y, nx, y)
    elif t in (SAND, DIRT, GRAVEL, SNOW) and rnd() < 0.4:
        amove(x, y, nx, y)             # копает
    else:
        if t == PLANT and rnd() < 0.05:
            grid[y][nx] = EMPTY        # ест траву
        elif y > 0 and grid[y - 1][x] == EMPTY and grid[y - 1][nx] == EMPTY:
            amove(x, y, nx, y - 1)     # лезет вверх
        else:
            aux[y][x] = -h


def worm_step(x, y):
    if deadly(x, y):
        grid[y][x] = EMPTY
        return
    below = grid[y + 1][x] if y + 1 < ROWS else STONE
    if below == EMPTY or below == STEAM:
        amove(x, y, x, y + 1)
        return
    if rnd() < 0.75:
        return
    dx, dy = random.choice(NB)
    nx, ny = x + dx, y + dy
    if not in_bounds(nx, ny):
        return
    t = grid[ny][nx]
    if t == SAND or t == DIRT or t == GRAVEL or t == SNOW or t == PLANT:
        grid[ny][nx] = WORM            # прорывает ход
        grid[y][x] = EMPTY
        stamp[ny][nx] = frame
    elif t == EMPTY and dy == 0:
        amove(x, y, nx, ny)


def fish_step(x, y):
    if deadly(x, y):
        grid[y][x] = EMPTY
        return
    in_water = False
    for dx, dy in NB:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == WATER:
            in_water = True
            break
    if not in_water:
        if y + 1 < ROWS and grid[y + 1][x] == EMPTY:
            amove(x, y, x, y + 1)
        elif rnd() < 0.03:
            grid[y][x] = EMPTY         # без воды погибает
        return
    if rnd() < 0.4:
        return
    h = aux[y][x]
    if h == 0 or rnd() < 0.05:
        h = 1 if rnd() < 0.5 else -1
        aux[y][x] = h
    if rnd() < 0.8:
        dx, dy = h, 0
    else:
        dx, dy = 0, random.choice((-1, 1))
    nx, ny = x + dx, y + dy
    if in_bounds(nx, ny) and grid[ny][nx] == WATER:
        amove(x, y, nx, ny)
    else:
        aux[y][x] = -h


def fly_step(x, y):
    if deadly(x, y):
        grid[y][x] = EMPTY
        return
    if rnd() < 0.5:
        return
    dx, dy = random.choice(NB8)
    nx, ny = x + dx, y + dy
    if in_bounds(nx, ny) and grid[ny][nx] == EMPTY:
        amove(x, y, nx, ny)


def step():
    global frame
    frame += 1
    if pending:
        todo = pending[:]
        del pending[:]
        for (px, py) in todo:
            explode(px, py, 7)
    if frame % 2 == 0:
        heat_step()
    if frame % 3 == 0:
        update_power()

    xr = range(COLS) if frame % 2 else range(COLS - 1, -1, -1)
    for y in range(ROWS - 1, -1, -1):
        row = grid[y]
        st = stamp[y]
        for x in xr:
            c = row[x]
            if c == EMPTY or st[x] == frame:
                continue

            if c in ELEC:
                continue

            if c in STATIC:
                if solid_gravity:
                    fall(x, y, c, False, False)
                continue

            if c == SAND or c == GRAVEL or c == GUNPOWDER:
                fall(x, y, c, False, True)

            elif c == DIRT:
                # у воды на земле вырастает трава
                if y > 0 and grid[y - 1][x] == EMPTY and rnd() < 0.01:
                    for dx, dy in NB:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny) and grid[ny][nx] == WATER:
                            grid[y - 1][x] = PLANT
                            break
                fall(x, y, c, False, rnd() < 0.6)

            elif c == SNOW:
                if rnd() < 0.5:
                    fall(x, y, c, False, True)

            elif c == WATER:
                changed = False
                for dx, dy in NB:
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny) and grid[ny][nx] == FIRE:
                        grid[ny][nx] = EMPTY
                        if rnd() < 0.5:
                            row[x] = STEAM
                            changed = True
                            break
                if not changed:
                    fall(x, y, c, True, True)

            elif c == OIL or c == MERCURY:
                fall(x, y, c, True, True)

            elif c == LN2:
                boiled = False
                for dx, dy in NB:
                    nx, ny = x + dx, y + dy
                    if not in_bounds(nx, ny):
                        continue
                    n = grid[ny][nx]
                    if n == EMPTY or n == LN2:
                        continue
                    if n == FIRE:
                        grid[ny][nx] = EMPTY
                        continue
                    addheat(nx, ny, -30)          # сильно охлаждает соседей
                    if rnd() < 0.03:
                        row[x] = EMPTY            # выкипает
                        boiled = True
                        break
                if not boiled:
                    fall(x, y, c, True, True)

            elif c == ACID:
                consumed = False
                for dx, dy in NB:
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        n = grid[ny][nx]
                        if n in DISSOLVABLE and rnd() < 0.08 and not (n == METAL and rnd() < 0.7):
                            grid[ny][nx] = EMPTY
                            if rnd() < 0.25:
                                row[x] = EMPTY
                                consumed = True
                                break
                if not consumed:
                    fall(x, y, c, True, True)

            elif c == LAVA:
                changed = False
                if temp[y][x] < 560:
                    temp[y][x] += 10
                hot.add((x, y))
                for dx, dy in NB:
                    nx, ny = x + dx, y + dy
                    if not in_bounds(nx, ny):
                        continue
                    n = grid[ny][nx]
                    if n == WATER:
                        grid[ny][nx] = STEAM
                        row[x] = STONE
                        changed = True
                        break
                    elif n == ICE or n == SNOW:
                        grid[ny][nx] = WATER
                    elif (n in (WOOD, PLANT, OIL, GUNPOWDER) or n in ELEC) and rnd() < 0.5:
                        grid[ny][nx] = FIRE
                    if n != EMPTY and n != LAVA:
                        addheat(nx, ny, 45)
                if not changed and rnd() < 0.3:
                    fall(x, y, c, True, True)

            elif c == FIRE:
                fuel = False
                for dx, dy in NB8:
                    nx, ny = x + dx, y + dy
                    if not in_bounds(nx, ny):
                        continue
                    n = grid[ny][nx]
                    if n == WOOD:
                        fuel = True
                        if rnd() < 0.10:
                            grid[ny][nx] = FIRE
                    elif n == PLANT:
                        fuel = True
                        if rnd() < 0.25:
                            grid[ny][nx] = FIRE
                    elif n == OIL:
                        fuel = True
                        if rnd() < 0.6:
                            grid[ny][nx] = FIRE
                    elif n == GUNPOWDER:
                        if rnd() < 0.8:
                            grid[ny][nx] = FIRE
                    elif n == TNT:
                        if rnd() < 0.5:
                            grid[ny][nx] = FIRE
                            pending.append((nx, ny))
                    elif (n == ICE or n == SNOW) and rnd() < 0.6:
                        grid[ny][nx] = WATER
                    elif n in ELEC:
                        fuel = True
                        if rnd() < 0.03:       # электроника тоже горит
                            grid[ny][nx] = FIRE
                    if n != EMPTY and n != FIRE:
                        addheat(nx, ny, 35)
                # рядом с топливом огонь горит долго
                if rnd() < (0.02 if fuel else 0.1):
                    row[x] = EMPTY
                elif y > 0 and grid[y - 1][x] == EMPTY and rnd() < 0.3:
                    swap(x, y, x, y - 1)

            elif c == STEAM:
                if rnd() < 0.012:
                    row[x] = EMPTY
                else:
                    rise(x, y)

            elif c == SPARK:
                if rnd() < 0.6:
                    row[x] = EMPTY

            elif c == ANT:
                ant_step(x, y)
            elif c == WORM:
                worm_step(x, y)
            elif c == FISH:
                fish_step(x, y)
            elif c == FIREFLY:
                fly_step(x, y)

            elif c == PLANT:
                if solid_gravity:
                    fall(x, y, c, False, False)
                    continue
                dx, dy = random.choice(NB)
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny) and grid[ny][nx] == WATER and rnd() < 0.1:
                    grid[ny][nx] = PLANT

            elif c == ICE:
                if solid_gravity:
                    fall(x, y, c, False, False)
                    continue
                dx, dy = random.choice(NB)
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny) and grid[ny][nx] == WATER and rnd() < 0.01:
                    grid[ny][nx] = ICE


# ---------- Иконки ----------
def draw_icon(el, r):
    base = COLORS[el] if el != EMPTY else (230, 120, 150)
    pygame.draw.rect(screen, base, r, border_radius=6)
    cx, cy = r.center
    if el == SAND:
        for dx, dy in ((-0.25, 0.2), (0, -0.1), (0.25, 0.2), (-0.1, 0.3), (0.15, 0.0)):
            pygame.draw.circle(screen, (190, 160, 80), (int(cx + dx * r.w), int(cy + dy * r.h)), max(2, r.w // 12))
    elif el == WATER:
        for k in (-0.2, 0.15):
            y = int(cy + k * r.h)
            pygame.draw.lines(screen, (190, 220, 255), False,
                              [(r.x + r.w * i // 6, y + (3 if i % 2 else -3)) for i in range(1, 6)], 2)
    elif el == STONE:
        pygame.draw.line(screen, (80, 80, 90), (r.x + 4, cy), (r.right - 4, cy), 2)
        pygame.draw.line(screen, (80, 80, 90), (cx, r.y + 4), (cx, cy), 2)
        pygame.draw.line(screen, (80, 80, 90), (r.x + r.w // 3, cy), (r.x + r.w // 3, r.bottom - 4), 2)
    elif el == WOOD:
        for k in (0.33, 0.66):
            y = int(r.y + r.h * k)
            pygame.draw.line(screen, (90, 55, 25), (r.x + 4, y), (r.right - 4, y), 2)
    elif el == FIRE:
        pts = [(cx, r.y + 4), (r.right - 6, r.bottom - 5), (r.x + 6, r.bottom - 5)]
        pygame.draw.polygon(screen, (255, 220, 60), pts)
    elif el == STEAM:
        for dx, dy, rad in ((-0.2, 0.15, 0.16), (0.1, -0.05, 0.2), (0.22, 0.2, 0.13)):
            pygame.draw.circle(screen, (240, 245, 255), (int(cx + dx * r.w), int(cy + dy * r.h)), int(rad * r.w), 2)
    elif el == LAVA:
        for k in (-0.2, 0.15):
            y = int(cy + k * r.h)
            pygame.draw.lines(screen, (255, 200, 60), False,
                              [(r.x + r.w * i // 6, y + (3 if i % 2 else -3)) for i in range(1, 6)], 2)
    elif el == OIL:
        pygame.draw.circle(screen, (120, 90, 60), (cx, cy), r.w // 4)
        pygame.draw.circle(screen, (170, 140, 100), (cx - r.w // 10, cy - r.h // 10), max(2, r.w // 10))
    elif el == ICE:
        pygame.draw.line(screen, (255, 255, 255), (r.x + 6, r.bottom - 6), (r.right - 6, r.y + 6), 2)
        pygame.draw.line(screen, (255, 255, 255), (r.x + 6, cy + r.h // 6), (cx + r.w // 6, r.y + 6), 2)
    elif el == PLANT:
        pygame.draw.line(screen, (20, 100, 30), (cx, r.bottom - 4), (cx, r.y + 6), 3)
        pygame.draw.line(screen, (20, 100, 30), (cx, cy), (r.x + 6, r.y + r.h // 3), 2)
        pygame.draw.line(screen, (20, 100, 30), (cx, cy), (r.right - 6, r.y + r.h // 3), 2)
    elif el == ACID:
        for dx, dy in ((-0.2, 0.15), (0.15, -0.1), (0.2, 0.25)):
            pygame.draw.circle(screen, (230, 255, 150), (int(cx + dx * r.w), int(cy + dy * r.h)), max(3, r.w // 8), 2)
    elif el == METAL:
        for k in (0.3, 0.7):
            y = int(r.y + r.h * k)
            pygame.draw.line(screen, (225, 230, 240), (r.x + 4, y), (r.right - 4, y), 2)
        for px, py in ((r.x + 6, r.y + 6), (r.right - 6, r.y + 6), (r.x + 6, r.bottom - 6), (r.right - 6, r.bottom - 6)):
            pygame.draw.circle(screen, (90, 95, 105), (px, py), 2)
    elif el == GLASS:
        pygame.draw.rect(screen, (235, 248, 252), r.inflate(-8, -8), 2, border_radius=4)
        pygame.draw.line(screen, (255, 255, 255), (r.x + 8, r.bottom - 10), (cx, r.y + 8), 2)
    elif el == GUNPOWDER:
        for dx, dy in ((-0.25, 0.2), (0, -0.15), (0.25, 0.15), (-0.05, 0.25)):
            pygame.draw.circle(screen, (255, 160, 40), (int(cx + dx * r.w), int(cy + dy * r.h)), max(2, r.w // 11))
    elif el == SNOW:
        for ang in ((1, 0), (0, 1), (1, 1), (1, -1)):
            m = r.w // 3
            pygame.draw.line(screen, (140, 165, 200), (cx - ang[0] * m, cy - ang[1] * m), (cx + ang[0] * m, cy + ang[1] * m), 2)
    elif el == TNT:
        band = pygame.Rect(r.x, cy - r.h // 6, r.w, r.h // 3)
        pygame.draw.rect(screen, (235, 205, 70), band)
        pygame.draw.line(screen, (60, 20, 20), (r.x + 4, r.y + 4), (r.right - 4, r.y + 4), 2)
        pygame.draw.line(screen, (60, 20, 20), (r.x + 4, r.bottom - 4), (r.right - 4, r.bottom - 4), 2)
    elif el == DIRT:
        for dx, dy in ((-0.25, 0.2), (0.05, 0.0), (0.25, 0.25), (-0.1, 0.32)):
            pygame.draw.circle(screen, (70, 45, 25), (int(cx + dx * r.w), int(cy + dy * r.h)), max(2, r.w // 11))
        pygame.draw.rect(screen, (60, 170, 70), (r.x, r.y, r.w, max(4, r.h // 5)), border_radius=3)
    elif el == GRAVEL:
        for dx, dy, k in ((-0.22, 0.15, 7), (0.1, -0.15, 6), (0.25, 0.22, 8), (-0.05, 0.3, 5)):
            pygame.draw.circle(screen, (85, 82, 78), (int(cx + dx * r.w), int(cy + dy * r.h)), max(2, r.w // k))
    elif el == MERCURY:
        pygame.draw.circle(screen, (235, 240, 248), (cx, cy), r.w // 3)
        pygame.draw.circle(screen, (255, 255, 255), (cx - r.w // 10, cy - r.h // 10), max(2, r.w // 10))
    elif el == HEAT:
        pygame.draw.polygon(screen, (255, 230, 120), [(cx, r.y + 5), (r.right - 8, cy), (r.x + 8, cy)])
        pygame.draw.line(screen, (255, 230, 120), (cx, cy), (cx, r.bottom - 5), 4)
    elif el == COLD:
        for ang in ((1, 0), (0, 1), (1, 1), (1, -1)):
            m = r.w // 3
            pygame.draw.line(screen, (240, 250, 255), (cx - ang[0] * m, cy - ang[1] * m), (cx + ang[0] * m, cy + ang[1] * m), 2)
    elif el == LN2:
        t = font.render("N2", True, (20, 70, 110))
        screen.blit(t, t.get_rect(center=(cx, cy)))
    elif el == ANT:
        for k in (-0.25, 0.0, 0.28):
            rad = max(2, int(r.w * (0.1 if k < 0 else 0.13)))
            pygame.draw.circle(screen, (50, 15, 10), (int(cx + k * r.w), cy), rad)
        for k in (-0.1, 0.05, 0.2):
            pygame.draw.line(screen, (50, 15, 10), (int(cx + k * r.w), cy), (int(cx + k * r.w) - 3, r.bottom - 6), 1)
            pygame.draw.line(screen, (50, 15, 10), (int(cx + k * r.w), cy), (int(cx + k * r.w) - 3, r.y + 6), 1)
    elif el == WORM:
        pts = [(r.x + 5 + i * (r.w - 10) // 6, cy + (5 if i % 2 else -5)) for i in range(7)]
        pygame.draw.lines(screen, (170, 60, 90), False, pts, 4)
    elif el == FISH:
        pygame.draw.rect(screen, (60, 120, 200), r, border_radius=6)
        body = pygame.Rect(0, 0, int(r.w * 0.55), int(r.h * 0.4))
        body.center = (cx - 3, cy)
        pygame.draw.ellipse(screen, (250, 190, 60), body)
        pygame.draw.polygon(screen, (250, 190, 60), [(body.right - 2, cy), (r.right - 5, cy - 7), (r.right - 5, cy + 7)])
    elif el == FIREFLY:
        pygame.draw.circle(screen, (120, 160, 70), (cx, cy), r.w // 3, 1)
        pygame.draw.circle(screen, (225, 255, 90), (cx, cy), max(3, r.w // 7))
    elif el == BATTERY:
        pygame.draw.line(screen, (255, 255, 255), (cx - 7, cy), (cx + 7, cy), 3)
        pygame.draw.line(screen, (255, 255, 255), (cx, cy - 7), (cx, cy + 7), 3)
    elif el == WIRE:
        pts = [(r.x + 4 + i * (r.w - 8) // 6, cy + (6 if i % 2 else -6)) for i in range(7)]
        pygame.draw.lines(screen, (255, 235, 120), False, pts, 3)
    elif el == LAMP:
        pygame.draw.circle(screen, (255, 255, 235), (cx, cy - 3), r.w // 4)
        pygame.draw.rect(screen, (110, 110, 120), (cx - r.w // 6, cy + r.w // 6, r.w // 3, r.h // 6))
    elif el == FUSE:
        pygame.draw.line(screen, (90, 70, 40), (r.x + 4, cy), (cx - 5, cy), 3)
        pygame.draw.line(screen, (90, 70, 40), (cx + 5, cy), (r.right - 4, cy), 3)
        pygame.draw.rect(screen, (255, 255, 255), (cx - 6, cy - 5, 12, 10), 1)
    elif el == SWON:
        pygame.draw.line(screen, (255, 255, 255), (r.x + 6, cy + 5), (r.right - 6, cy - 7), 3)
        pygame.draw.circle(screen, (255, 255, 255), (r.x + 6, cy + 5), 3)
        pygame.draw.circle(screen, (255, 255, 255), (r.right - 6, cy + 5), 3)
    elif el == BOLT:
        pts = [(cx + 4, r.y + 3), (cx - 6, cy + 2), (cx, cy + 2), (cx - 4, r.bottom - 3),
               (cx + 7, cy - 3), (cx + 1, cy - 3)]
        pygame.draw.polygon(screen, (255, 240, 90), pts)
    elif el == EMPTY:
        pygame.draw.line(screen, (255, 255, 255), (r.x + 6, r.y + 6), (r.right - 6, r.bottom - 6), 3)
        pygame.draw.line(screen, (255, 255, 255), (r.x + 6, r.bottom - 6), (r.right - 6, r.y + 6), 3)


def draw():
    world_surf.fill(COLORS[EMPTY])
    for y in range(ROWS):
        row = grid[y]
        trow = temp[y]
        for x in range(COLS):
            v = row[x]
            if v:
                if v == FIRE:
                    col = (255, random.randint(70, 180), 20)
                elif v == LAVA:
                    col = (230, random.randint(50, 110), 20)
                    if y == 0 or grid[y - 1][x] != LAVA:
                        col = (255, random.randint(150, 210), 40)
                elif v == SPARK:
                    col = (255, 255, random.randint(150, 230))
                elif v == FIREFLY:
                    col = (random.randint(150, 230), 255, random.randint(40, 110))
                elif v in ANIMALS:
                    col = COLORS[v]
                elif v in ELEC:
                    p = (x, y) in powered
                    if v == WIRE:
                        col = (255, 235, 120) if p else (190, 110, 50)
                    elif v == LAMP:
                        col = (255, 252, 200) if p else (130, 120, 90)
                    elif v == FUSE:
                        col = (255, 110, 70) if p else (175, 155, 115)
                    elif v == BATTERY:
                        col = (50, 165, 65) if (x + y) % 2 else (38, 135, 52)
                    elif v == SWON:
                        col = (60, 200, 90)
                    else:
                        col = (200, 60, 60)
                else:
                    pal = PAL[v]
                    n = noise[y][x]
                    if v == WOOD:
                        idx = (x + (n > 230)) % 3
                    elif v == STONE:
                        idx = (x // 3 + y // 3 + (n > 200)) % 4
                    elif v == METAL:
                        idx = (y + (n > 230)) % 3
                    else:
                        idx = n % len(pal)
                    col = pal[idx]
                    if v == TNT and (y // 2) % 4 == 0:
                        col = (235, 205, 70)
                    elif v in TOP and (y == 0 or grid[y - 1][x] != v):
                        col = TOP[v]
                    elif v == WATER and (x * 3 + y * 5 + frame // 5) % 11 == 0:
                        col = (90, 150, 245)
                    # свечение от нагрева / иней от холода
                    t = trow[x]
                    if t > 80:
                        col = blend(col, (255, 110, 30), min(1.0, (t - 80) / 350.0))
                        if t > 400:
                            col = blend(col, (255, 235, 190), min(1.0, (t - 400) / 300.0))
                    elif t < -20:
                        col = blend(col, (190, 225, 255), min(0.6, -t / 120.0))
                world_surf.set_at((x, y), col)
    screen.blit(pygame.transform.scale(world_surf, (COLS * CELL, ROWS * CELL)), (0, 0))

    pygame.draw.rect(screen, (30, 30, 40), (0, H - UI_H, W, UI_H))
    for rect, name, val in buttons:
        if isinstance(val, int):
            selected = (val == current)
        else:
            selected = (val == "pause" and paused) or (val == "gravity" and solid_gravity)
        pygame.draw.rect(screen, (110, 110, 150) if selected else (55, 55, 70),
                         rect.inflate(-6, -6), border_radius=8)
        if isinstance(val, int):
            txt = font.render(name, True, (255, 255, 255))
            icon_r = pygame.Rect(0, 0, int(ROW_H * 0.52), int(ROW_H * 0.52))
            icon_r.center = (rect.centerx, int(rect.y + ROW_H * 0.36))
            draw_icon(val, icon_r)
            screen.blit(txt, txt.get_rect(center=(rect.centerx, int(rect.bottom - ROW_H * 0.17))))
        else:
            txt = font.render(control_label(val), True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))


def handle_button(pos):
    global current, brush, grid, stamp, temp, aux, powered, surge_timer, paused, solid_gravity
    for rect, name, val in buttons:
        if rect.collidepoint(pos):
            if val == "minus":
                brush = max(1, brush - 1)
            elif val == "plus":
                brush = min(10, brush + 1)
            elif val == "clear":
                grid = [[EMPTY] * COLS for _ in range(ROWS)]
                stamp = [[0] * COLS for _ in range(ROWS)]
                temp = [[0.0] * COLS for _ in range(ROWS)]
                aux = [[0] * COLS for _ in range(ROWS)]
                hot.clear()
                batteries.clear()
                powered = set()
                del pending[:]
                del surge_seeds[:]
                surge_timer = 0
            elif val == "pause":
                paused = not paused
            elif val == "gravity":
                solid_gravity = not solid_gravity
            else:
                current = val
            return True
    return False


running = True
last_pos = None
suppress = False      # после молнии / переключения рубильника не рисуем
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if not handle_button(e.pos) and e.pos[1] < H - UI_H:
                gx, gy = e.pos[0] // CELL, e.pos[1] // CELL
                if current == BOLT:
                    lightning(gx)
                    suppress = True
                elif current == SWON:
                    if toggle_switch(gx, gy):
                        suppress = True

    if pygame.mouse.get_pressed()[0] and not suppress:
        mx, my = pygame.mouse.get_pos()
        if my < H - UI_H:
            cx, cy = mx // CELL, my // CELL
            if last_pos is None:
                paint(cx, cy)
            else:
                paint_line(last_pos[0], last_pos[1], cx, cy)
            last_pos = (cx, cy)
        else:
            last_pos = None
    else:
        last_pos = None
        if not pygame.mouse.get_pressed()[0]:
            suppress = False

    if not paused:
        step()
    draw()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
