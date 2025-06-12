import pygame
import json
import random
import string
from network import network

pygame.init()
FONT = pygame.font.SysFont("comicsans", 30)
WIDTH, HEIGHT = 1000, 800
BALL_WIDTH = 100
BALL_HEIGHT = 50


class Player():

    def __init__(self, id, balls=[]):

        self.balls = balls
        self.id = id

    def draw(self, g):

        for ball in self.balls:
            pygame.draw.rect(g, "white", ball["rect"])
            word = ball["word"]
            typed_len = ball["letter"]

            total_width = sum(FONT.size(c)[0] for c in word)
            start_x = ball["rect"].centerx - total_width // 2
            y = ball["rect"].centery - FONT.get_height() // 2
            x = start_x

            for i, char in enumerate(word):
                color = "red" if i < typed_len else "black"
                letter_surf = FONT.render(char, True, color)
                g.blit(letter_surf, (x, y))
                x += FONT.size(char)[0]


    def add_ball(self, ball):

        self.balls.append(ball)


    def remove_ball(self, ball):

        self.balls.remove(ball)


    def update(self, letter, player, player2):
        

        for ball in player.balls[:]:
            if letter == ball["word"][ball["letter"]]:
                ball["letter"] += 1
            else:
                ball["letter"] = 0

            if ball["letter"] == ball["length"]:
                player.remove_ball(ball)
                b = ball["rect"]
                b.x, b.y = get_random_cords(other, left=(player.id == 0))
                word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 5)))
                player2.add_ball({"rect": b, "word": word, "letter": 0, "length": len(word)})



def get_random_cords(balls, left):
    while True:
        if left:
            ball_x = random.randint(10, WIDTH // 2 - BALL_WIDTH - 10)
        else:
            ball_x = random.randint(WIDTH // 2 + 10, WIDTH - BALL_WIDTH - 10)
        ball_y = random.randint(10, HEIGHT - BALL_HEIGHT - 10)

        hit = False
        for ball in balls:
            rect = ball["rect"]
            if abs(ball_x - rect.x) < BALL_WIDTH + 5 and abs(ball_y - rect.y) < BALL_HEIGHT + 5:
                hit = True
                break

        if not hit:
            return ball_x, ball_y


def setup(left):
    balls = []
    for _ in range(10):
        ball_x, ball_y = get_random_cords(balls, left)
        ball_rect = pygame.Rect(ball_x, ball_y, BALL_WIDTH, BALL_HEIGHT)
        length = random.randint(3, 5)
        word = ''.join(random.choices(string.ascii_lowercase, k=length))
        balls.append({"rect": ball_rect, "word": word, "letter": 0, "length": len(word)})
    return balls


class Game:

    def __init__(self, w, h):
        self.net = Network()
        self.width = w
        self.height = h
        self.player = Player(self.net.id, setup(self.net.id == 0))
        self.player2 = Player(self.net.id + 1 % 2)
        self.canvas = Canvas(self.width, self.height, "Testing...")

    def run(self):
        clock = pygame.time.Clock()
        run = True
        while run:
            clock.tick(60)


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.KEYDOWN:

                    self.player.update(pygame.key.name(event.key), self.player, self.player2)

            # Send Network Stuff
            self.player2.balls = self.parse_data(self.send_data())

            # Update Canvas
            self.canvas.draw_background()
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.canvas.update()

        pygame.quit()

    def send_data(self):
        ball_data = []
        for ball in self.player.balls:
            ball_data.append({
                "x": ball["rect"].x,
                "y": ball["rect"].y,
                "word": ball["word"],
                "letter": ball["letter"],
                "length": ball["length"]
            })

        data = json.dumps({"id": self.net.id, "balls": ball_data})
        reply = self.net.send(data)
        return reply

    @staticmethod
    def parse_data(data):
        try:
            parsed = json.loads(data)
            balls = []
            for b in parsed["balls"]:
                rect = pygame.Rect(b["x"], b["y"], WORD_WIDTH, WORD_HEIGHT)
                balls.append({
                    "rect": rect,
                    "word": b["word"],
                    "letter": b["letter"],
                    "length": b["length"]
                })
            return balls
        except:
            return []



class Canvas:

    def __init__(self, w, h, name="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w,h))
        pygame.display.set_caption(name)

    @staticmethod
    def update():
        pygame.display.update()

    def draw_text(self, text, size, x, y):
        pygame.font.init()
        font = pygame.font.SysFont("comicsans", size)
        render = font.render(text, 1, (0,0,0))

        self.screen.draw(render, (x,y))

    def get_canvas(self):
        return self.screen

    def draw_background(self):
        self.screen.fill((255,255,255))
