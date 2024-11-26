import math
import random
import pygame
import threading
import time

# Dimensões da janela e grade
width = 800
height = 800
cols = 40
rows = 40

# Semáforos para recursos compartilhados
desenho_lock = threading.Semaphore(1)  # Controle de acesso ao desenho
snack_lock = threading.Semaphore(1)    # Controle de acesso ao snack

class cube:
    rows = 40
    w = 800

    def __init__(self, start, dirnx=1, dirny=0, color=(255, 0, 0)):
        self.pos = start
        self.dirnx = dirnx
        self.dirny = dirny  # Direção
        self.color = color

    def move(self):
        self.pos = (self.pos[0] + self.dirnx, self.pos[1] + self.dirny)

    def draw(self, surface, eyes=False):
        dis = self.w // self.rows
        i = self.pos[0]
        j = self.pos[1]

        pygame.draw.rect(surface, self.color, (i * dis + 1, j * dis + 1, dis - 2, dis - 2))
        if eyes:
            centre = dis // 2
            radius = 3
            circleMiddle = (i * dis + centre - radius, j * dis + 8)
            circleMiddle2 = (i * dis + dis - radius * 2, j * dis + 8)
            pygame.draw.circle(surface, (0, 0, 0), circleMiddle, radius)
            pygame.draw.circle(surface, (0, 0, 0), circleMiddle2, radius)


class snake(threading.Thread):
    def __init__(self, color, pos, name, controls):
        threading.Thread.__init__(self)
        self.color = color
        self.head = cube(pos, color=color)
        self.body = [self.head]
        self.dirnx = 0
        self.dirny = 1
        self.name = name
        self.running = True  # Controle de execução da thread
        self.controls = controls  # Teclas de controle (esquerda, direita, cima, baixo)
        self.turns = {}  # Inicializa o atributo turns

    def run(self):
        while self.running:
            self.move()
            time.sleep(0.2)  # Velocidade mais lenta (200ms entre movimentos)

    def move(self):
        # Atualizar posição de cada parte do corpo
        for i, c in enumerate(self.body):
            if c.pos in self.turns:
                turn = self.turns[c.pos]
                c.dirnx = turn[0]
                c.dirny = turn[1]
                if i == len(self.body) - 1:
                    self.turns.pop(c.pos)
            c.move()

        # Verificar colisão com a borda
        if self.head.pos[0] < 0 or self.head.pos[0] >= cols or self.head.pos[1] < 0 or self.head.pos[1] >= rows:
            end_game(self.name)

        # Verificar colisão com o próprio corpo
        for segment in self.body[1:]:
            if self.head.pos == segment.pos:
                end_game(self.name)

        # Verificar colisão com outras cobras
        for s in snakes:
            if s != self:
                for segment in s.body:
                    if self.head.pos == segment.pos:
                        end_game(self.name)

    def addCube(self):
        tail = self.body[-1]
        dx, dy = tail.dirnx, tail.dirny

        if dx == 1 and dy == 0:
            self.body.append(cube((tail.pos[0] - 1, tail.pos[1]), color=self.color))
        elif dx == -1 and dy == 0:
            self.body.append(cube((tail.pos[0] + 1, tail.pos[1]), color=self.color))
        elif dx == 0 and dy == 1:
            self.body.append(cube((tail.pos[0], tail.pos[1] - 1), color=self.color))
        elif dx == 0 and dy == -1:
            self.body.append(cube((tail.pos[0], tail.pos[1] + 1), color=self.color))

        self.body[-1].dirnx = dx
        self.body[-1].dirny = dy

    def draw(self, surface):
        for i, c in enumerate(self.body):
            c.draw(surface, eyes=(i == 0))


def redrawWindow():
    global win, snakes, snack
    with desenho_lock:  # Garante que apenas uma thread desenhe por vez
        win.fill((0, 0, 0))
        drawGrid(width, rows, win)
        snack.draw(win)
        for snake in snakes:
            snake.draw(win)
        pygame.display.update()


def drawGrid(w, rows, surface):
    sizeBtwn = w // rows
    x = 0
    y = 0
    for l in range(rows):
        x = x + sizeBtwn
        y = y + sizeBtwn
        pygame.draw.line(surface, (255, 255, 255), (x, 0), (x, w))
        pygame.draw.line(surface, (255, 255, 255), (0, y), (w, y))


def randomSnack(rows, snakes):
    positions = []
    for snake in snakes:
        positions.extend([c.pos for c in snake.body])

    while True:
        x = random.randrange(rows)
        y = random.randrange(rows)
        if (x, y) not in positions:
            break
    return (x, y)

def end_game(loser_name):
    global game_running
    print(f"{loser_name} colidiu! Fim de jogo.")
    game_running = False
    pygame.quit()
    return

def main():
    global win, snakes, snack, game_running
    pygame.init()
    win = pygame.display.set_mode((width, height))

    # Criar cobras e threads com controles diferentes
    snakes = [
        snake((255, 0, 0), (10, 10), "Snake 1", {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s}),
        snake((255, 255, 0), (30, 30), "Snake 2", {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN})  # Cobra 2 amarela
    ]

    for s in snakes:
        s.start()  # Iniciar as threads

    snack = cube(randomSnack(rows, snakes), color=(0, 255, 0))
    clock = pygame.time.Clock()
    game_running = True

    while game_running:
        pygame.time.delay(50)
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
                pygame.quit()
                return

        keys = pygame.key.get_pressed()

        # Atualizar direções das cobras com base nas teclas pressionadas
        for s in snakes:
            if keys[s.controls['left']] and s.dirnx == 0:
                s.dirnx = -1
                s.dirny = 0
            elif keys[s.controls['right']] and s.dirnx == 0:
                s.dirnx = 1
                s.dirny = 0
            elif keys[s.controls['up']] and s.dirny == 0:
                s.dirny = -1
                s.dirnx = 0
            elif keys[s.controls['down']] and s.dirny == 0:
                s.dirny = 1
                s.dirnx = 0

            s.turns[s.head.pos[:]] = [s.dirnx, s.dirny]

        # Verificar colisão com o snack
        for s in snakes:
            if s.head.pos == snack.pos:
                with snack_lock:  # Garante que apenas uma cobra pegue o snack
                    s.addCube()
                    snack = cube(randomSnack(rows, snakes), color=(0, 255, 0))

        redrawWindow()


main()
