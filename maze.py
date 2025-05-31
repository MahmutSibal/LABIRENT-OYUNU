import pygame
import random
import time
import os

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (255, 255, 100)
PURPLE = (180, 50, 180)

PLAYER_COLORS = [
    ("Sarı", (255, 255, 100)),
    ("Mavi", (50, 150, 255)),
    ("Kırmızı", (200, 50, 50)),
    ("Yeşil", (50, 200, 50)),
]

# Oyun ayarları (sabit boyut)
GRID_SIZE = 12
CELL_SIZE = 48
FPS = 60
SCREEN_SIZE = GRID_SIZE * CELL_SIZE

class Maze:
    def __init__(self, size, coin_count=10):
        self.size = size
        self.grid = [[1 for _ in range(size)] for _ in range(size)]
        self.start = (0, 0)
        self.generate_maze(*self.start)
        self.end = self.find_end()
        self.solution_path = self.solve_maze()
        self.coins = self.place_coins(coin_count)

    def find_end(self):
        # Sağ alt köşeden yukarı ve sola doğru ilk açık hücreyi bul
        for d in range(self.size):
            for dx, dy in [(0, -1), (-1, 0), (-1, -1)]:
                x = self.size - 1 - d if dx else self.size - 1
                y = self.size - 1 - d if dy else self.size - 1
                if 0 <= x < self.size and 0 <= y < self.size and self.grid[y][x] == 0:
                    return (x, y)
        # Hiçbiri bulunamazsa yine sağ alt köşe
        return (self.size - 1, self.size - 1)

    def generate_maze(self, x, y):
        self.grid[y][x] = 0
        dirs = [(0,1),(1,0),(0,-1),(-1,0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx*2, y + dy*2
            if 0 <= nx < self.size and 0 <= ny < self.size and self.grid[ny][nx] == 1:
                self.grid[y + dy][x + dx] = 0
                self.generate_maze(nx, ny)

    def solve_maze(self):
        from collections import deque
        queue = deque()
        queue.append((self.start, [self.start]))
        visited = set()
        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == self.end:
                return path
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and self.grid[ny][nx] == 0 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return []

    def place_coins(self, coin_count):
        coins = set()
        empty_cells = [(x, y) for y in range(self.size) for x in range(self.size)
                       if self.grid[y][x] == 0 and (x, y) != self.start and (x, y) != self.end]
        random.shuffle(empty_cells)
        for i in range(min(coin_count, len(empty_cells))):
            coins.add(empty_cells[i])
        return coins

    def is_valid(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def draw(self, screen, show_path=False, cell_size=48):
        for y in range(self.size):
            for x in range(self.size):
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                if (x, y) == self.start:
                    pygame.draw.rect(screen, GREEN, rect)
                elif (x, y) == self.end:
                    pygame.draw.rect(screen, RED if len(self.coins) == 0 else GRAY, rect)
                elif self.grid[y][x] == 0:
                    pygame.draw.rect(screen, WHITE, rect)
                else:
                    pygame.draw.rect(screen, BLACK, rect)
                pygame.draw.rect(screen, BLUE, rect, 1)
        # Altınları çiz
        for cx, cy in self.coins:
            center = (cx * cell_size + cell_size // 2, cy * cell_size + cell_size // 2)
            pygame.draw.circle(screen, (255, 215, 0), center, cell_size // 5)
        if show_path:
            for px, py in self.solution_path:
                rect = pygame.Rect(px * cell_size + cell_size // 4, py * cell_size + cell_size // 4, cell_size // 2, cell_size // 2)
                pygame.draw.rect(screen, PURPLE, rect)

class Player:
    def __init__(self, maze, color):
        self.maze = maze
        self.x, self.y = maze.start
        self.color = color

    def move(self, dx, dy):
        nx, ny = self.x + dx, self.y + dy
        if self.maze.is_valid(nx, ny) and self.maze.grid[ny][nx] == 0:
            self.x, self.y = nx, ny

    def draw(self, screen, cell_size=48):
        rect = pygame.Rect(self.x * cell_size + cell_size // 6, self.y * cell_size + cell_size // 6, cell_size - cell_size // 3, cell_size - cell_size // 3)
        pygame.draw.rect(screen, self.color, rect)

class Game:
    def __init__(self):
        pygame.init()
        # Sabit ekran boyutu
        self.screen_width = SCREEN_SIZE
        self.screen_height = SCREEN_SIZE + 100  # Alt bilgi için ekstra alan
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🔷 Labirent Oyunu")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 32)
        self.coin_sound = pygame.mixer.Sound("coin.wav")
        self.move_sound = pygame.mixer.Sound("move.wav")
        self.win_sound = pygame.mixer.Sound("win.wav")
        self.state = "menu"
        self.username = ""
        self.selected_color = 0
        self.scores = self.load_scores()
        self.input_text = ""
        self.show_path = False

    def load_scores(self):
        if not os.path.exists("scores.txt"):
            return []
        with open("scores.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        scores = []
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                scores.append((parts[0], float(parts[1])))
        return sorted(scores, key=lambda x: x[1])[:10]

    def save_score(self, name, score):
        with open("scores.txt", "a", encoding="utf-8") as f:
            f.write(f"{name},{score}\n")

    def new_game(self):
        # Sabit grid ve hücre boyutu
        self.maze = Maze(GRID_SIZE, coin_count=15)
        self.player = Player(self.maze, PLAYER_COLORS[self.selected_color][1])
        self.start_time = time.time()
        self.score = 0
        self.finished = False
        self.show_path = False

    def run(self):
        while True:
            self.clock.tick(FPS)
            if self.state == "menu":
                self.menu_events()
                self.draw_menu()
            elif self.state == "howto":
                self.howto_events()
                self.draw_howto()
            elif self.state == "register":
                self.register_events()
                self.draw_register()
            elif self.state == "play":
                self.handle_events()
                self.update()
                self.draw()
            elif self.state == "scoreboard":
                self.scoreboard_events()
                self.draw_scoreboard()

    def draw_menu(self):
        self.screen.fill(GRAY)
        title = self.font.render("Labirent Oyununa Hoşgeldiniz!", True, BLACK)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 60))
        btn1 = self.font.render("Oyuna Başla", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 80, 150, 160, 40))
        self.screen.blit(btn1, (self.screen_width // 2 - btn1.get_width() // 2, 160))
        btn2 = self.font.render("Nasıl Oynanır?", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 80, 210, 160, 40))
        self.screen.blit(btn2, (self.screen_width // 2 - btn2.get_width() // 2, 220))
        btn3 = self.font.render("Skor Tablosu", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 80, 270, 160, 40))
        self.screen.blit(btn3, (self.screen_width // 2 - btn3.get_width() // 2, 280))
        pygame.display.flip()

    def menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if 150 <= y <= 190:
                    self.state = "register"
                elif 210 <= y <= 250:
                    self.state = "howto"
                elif 270 <= y <= 310:
                    self.state = "scoreboard"

    def draw_register(self):
        self.screen.fill(GRAY)
        title = self.font.render("Kullanıcı Adı Girin ve Renk Seçin", True, BLACK)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 40))
        # İsim kutusu
        pygame.draw.rect(self.screen, WHITE, (self.screen_width // 2 - 100, 100, 200, 40))
        name_text = self.font.render(self.input_text or "İsminiz...", True, BLACK)
        self.screen.blit(name_text, (self.screen_width // 2 - 90, 110))
        # Renk seçenekleri
        for i, (name, color) in enumerate(PLAYER_COLORS):
            rect = pygame.Rect(self.screen_width // 2 - 120 + i * 60, 180, 40, 40)
            pygame.draw.rect(self.screen, color, rect)
            if i == self.selected_color:
                pygame.draw.rect(self.screen, BLACK, rect, 3)
        # Başla butonu
        btn = self.font.render("Başla", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 60, 320, 120, 40))
        self.screen.blit(btn, (self.screen_width // 2 - btn.get_width() // 2, 330))
        pygame.display.flip()

    def register_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    if self.input_text.strip():
                        self.username = self.input_text.strip()
                        self.state = "play"
                        self.new_game()
                elif len(self.input_text) < 12 and event.unicode.isprintable():
                    self.input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Renk seçimi
                for i in range(len(PLAYER_COLORS)):
                    rect = pygame.Rect(self.screen_width // 2 - 120 + i * 60, 180, 40, 40)
                    if rect.collidepoint(x, y):
                        self.selected_color = i
                # Başla butonu
                if self.screen_width // 2 - 60 <= x <= self.screen_width // 2 + 60 and 320 <= y <= 360:
                    if self.input_text.strip():
                        self.username = self.input_text.strip()
                        self.state = "play"
                        self.new_game()

    def draw_howto(self):
        self.screen.fill(GRAY)
        lines = [
            "Nasıl Oynanır?",
            "- Yön tuşları ile hareket edin.",
            "- Tüm altınları toplayın.",
            "- Altınlar bitmeden çıkışa ulaşamazsınız.",
            "- Kendi kutu renginizi seçebilirsiniz.",
            "- En hızlı bitiren skor tablosuna girer!",
            "- Çıkmak için ESC tuşuna basabilirsiniz."
        ]
        for i, line in enumerate(lines):
            text = self.font.render(line, True, BLACK)
            self.screen.blit(text, (40, 60 + i * 40))
        btn = self.font.render("Geri", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 60, self.screen_height - 70, 120, 40))
        self.screen.blit(btn, (self.screen_width // 2 - btn.get_width() // 2, self.screen_height - 60))
        pygame.display.flip()

    def howto_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if self.screen_width // 2 - 60 <= x <= self.screen_width // 2 + 60 and self.screen_height - 70 <= y <= self.screen_height - 30:
                    self.state = "menu"

    def draw_scoreboard(self):
        self.screen.fill(GRAY)
        title = self.font.render("Skor Tablosu (En İyi 10)", True, BLACK)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 40))
        for i, (name, score) in enumerate(self.scores):
            line = self.font.render(f"{i+1}. {name}: {score}s", True, BLACK)
            self.screen.blit(line, (self.screen_width // 2 - 100, 80 + i * 30))
        btn = self.font.render("Geri", True, WHITE)
        pygame.draw.rect(self.screen, BLUE, (self.screen_width // 2 - 60, self.screen_height - 70, 120, 40))
        self.screen.blit(btn, (self.screen_width // 2 - btn.get_width() // 2, self.screen_height - 60))
        pygame.display.flip()

    def scoreboard_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if self.screen_width // 2 - 60 <= x <= self.screen_width // 2 + 60 and self.screen_height - 70 <= y <= self.screen_height - 30:
                    self.state = "menu"

    def update(self):
        if (self.player.x, self.player.y) == self.maze.end and not self.finished and len(self.maze.coins) == 0:
            self.finished = True
            self.score = round(time.time() - self.start_time, 2)
            self.win_sound.play()
            self.save_score(self.username, self.score)
            self.scores = self.load_scores()
            self.state = "scoreboard"

    def draw(self):
        self.screen.fill(GRAY)
        # Labirenti üstte ortala
        maze_area = self.maze.size * CELL_SIZE
        offset_x = (self.screen_width - maze_area) // 2
        offset_y = 20
        surface = pygame.Surface((maze_area, maze_area))
        surface.fill(GRAY)
        self.maze.draw(surface, self.show_path, CELL_SIZE)
        self.player.draw(surface, CELL_SIZE)
        self.screen.blit(surface, (offset_x, offset_y))
        # Altın sayısı
        coin_text = self.font.render(f"Kalan Altın: {len(self.maze.coins)}", True, (255, 140, 0))
        self.screen.blit(coin_text, (self.screen_width - 250, self.screen_height - 70))
        # Skor veya süre
        if self.finished:
            result = self.font.render(f"Bitti! Süre: {self.score}s", True, BLACK)
            self.screen.blit(result, (30, self.screen_height - 70))
        else:
            live = self.font.render(f"Süre: {round(time.time() - self.start_time, 1)}s", True, BLACK)
            self.screen.blit(live, (30, self.screen_height - 70))
        # Oyun sahibi
        owner_text = self.font.render("Oyun Sahibi: Mahmut Sibal", True, BLACK)
        self.screen.blit(owner_text, (30, self.screen_height - 40))
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                if not self.finished:
                    moved = False
                    if event.key == pygame.K_UP:
                        self.player.move(0, -1)
                        moved = True
                    elif event.key == pygame.K_DOWN:
                        self.player.move(0, 1)
                        moved = True
                    elif event.key == pygame.K_LEFT:
                        self.player.move(-1, 0)
                        moved = True
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1, 0)
                        moved = True
                    elif event.key == pygame.K_SPACE:
                        self.show_path = not self.show_path
                    if moved:
                        # Altın toplama kontrolü
                        pos = (self.player.x, self.player.y)
                        if pos in self.maze.coins:
                            self.maze.coins.remove(pos)
                            self.coin_sound.play()
                        self.move_sound.play()

if __name__ == "__main__":
    Game().run()