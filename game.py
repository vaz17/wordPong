import pygame
import json
import random
import string
import time
from network import Network

pygame.init()
FONT = pygame.font.SysFont("comicsans", 30)
WIDTH, HEIGHT = 1000, 800
BALL_WIDTH = 100
BALL_HEIGHT = 50


class Player:
    def __init__(self, id, balls=None):
        self.balls = balls if balls is not None else []
        self.transfer_queue = []  # Balls to send to other player
        self.id = int(id)

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

    def update(self, letter, player2):
        for ball in self.balls[:]:
            if letter == ball["word"][ball["letter"]]:
                ball["letter"] += 1
            else:
                ball["letter"] = 0

            if ball["letter"] == ball["length"]:
                self.balls.remove(ball)

                b = pygame.Rect(0, 0, BALL_WIDTH, BALL_HEIGHT)
                b.x, b.y = get_random_cords(player2.balls, left= not self.id == 0)
                word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 5)))

                self.transfer_queue.append({
                    "x": b.x, "y": b.y,
                    "word": word,
                    "letter": 0,
                    "length": len(word)
                })


def get_random_cords(balls, left):
    while True:
        if left:
            ball_x = random.randint(10, WIDTH // 2 - BALL_WIDTH - 10)
        else:
            ball_x = random.randint(WIDTH // 2 + 10, WIDTH - BALL_WIDTH - 10)
        ball_y = random.randint(10, HEIGHT - BALL_HEIGHT - 10)

        hit = False
        if balls:
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
        self.player = Player(int(self.net.id), setup(int(self.net.id) == 0))
        self.player2 = Player((int(self.net.id) + 1) % 2)
        self.canvas = Canvas(self.width, self.height, "Testing...")
        self.start_time = None
        self.time_limit = 60

    def run(self):
        clock = pygame.time.Clock()
        self.start_time = time.time()
        run = True
        while run:
            clock.tick(60)

            elapsed_time = time.time() - self.start_time
            if elapsed_time >= self.time_limit:
                print("Time's up!")
                run = False


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.KEYDOWN:

                    self.player.update(pygame.key.name(event.key), self.player2)


            # Send Network Stuff
            balls, new_balls = self.parse_data(self.send_data())
            self.player2.balls = balls
            for b in new_balls:
                self.player.balls.append(b)

            # Update Canvas
            self.canvas.draw_background(elapsed_time)
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.canvas.update()

        pygame.quit()


    def send_data(self):
        ball_data = [{
            "x": b["rect"].x,
            "y": b["rect"].y,
            "word": b["word"],
            "letter": b["letter"],
            "length": b["length"]
        } for b in self.player.balls]

        # Copy and reset transfer queue
        outgoing_transfer = self.player.transfer_queue[:]
        self.player.transfer_queue.clear()

        payload = {
            "id": self.net.id,
            "balls": ball_data,
            "new": outgoing_transfer
        }

        reply = self.net.send(json.dumps(payload))
        return reply

    @staticmethod
    def parse_data(data):
        try:
            parsed = json.loads(data)
            balls = []
            for b in parsed["balls"]:
                rect = pygame.Rect(b["x"], b["y"], BALL_WIDTH, BALL_HEIGHT)
                balls.append({
                    "rect": rect,
                    "word": b["word"],
                    "letter": b["letter"],
                    "length": b["length"]
                })

            new = []
            if "new" in parsed:
                for b in parsed["new"]:
                    rect = pygame.Rect(b["x"], b["y"], BALL_WIDTH, BALL_HEIGHT)
                    new.append({
                        "rect": rect,
                        "word": b["word"],
                        "letter": 0,
                        "length": b["length"]
                    })

            return balls, new
        except:
            return [], []



    def wait_for_opponent(self):
        print("Waiting for opponent...")

        waiting = True
        while waiting:
            # Send your current balls (could be empty)
            reply = self.send_data()
            try:
                parsed = json.loads(reply)
                # Opponent is connected when they send back *non-empty* balls or at least a valid ID
                if "balls" in parsed and parsed["balls"] != []:
                    waiting = False
            except:
                pass

            # Optional: Draw something while waiting
            self.canvas.draw_background()
            self.canvas.draw_text("Waiting for other player...", 40, 300, 350)
            self.canvas.update()
            time.sleep(0.5)  # avoid overloading the server




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
        self.screen.blit(render, (x, y))  # Correct method


    def get_canvas(self):
        return self.screen

    def draw_background(self, elapsed_time=None):
        self.screen.fill("black")
        pygame.draw.line(self.screen, "white", (self.width // 2, 0), (self.width // 2, self.height))

        if elapsed_time is not None:
            remaining = max(0, int(60 - elapsed_time))
            time_text = f"Time: {remaining}"
            font = pygame.font.SysFont("comicsans", 40)
            render = font.render(time_text, True, "white")
            text_width = render.get_width()
            self.screen.blit(render, ((self.width - text_width) // 2, 10))


