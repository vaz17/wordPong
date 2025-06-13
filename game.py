import pygame
import json
import random
import string
import time
import uuid
from network import Network

pygame.init()
FONT = pygame.font.SysFont("comicsans", 30)
WIDTH, HEIGHT = 1000, 800
BALL_WIDTH = 100
BALL_HEIGHT = 50

def generate_ball_id():
    return str(uuid.uuid4())

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
            if ball["letter"] >= ball["length"]:
                continue  # already completed

            if letter == ball["word"][ball["letter"]]:
                ball["letter"] += 1
                if ball["letter"] == ball["length"]:
                    self.balls.remove(ball)

                    b = pygame.Rect(0, 0, BALL_WIDTH, BALL_HEIGHT)
                    b.x, b.y = get_random_cords(player2.balls, left=not self.id == 0)
                    word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 5)))

                    self.transfer_queue.append({
                        "id": generate_ball_id(),
                        "x": b.x,
                        "y": b.y,
                        "word": word,
                        "letter": 0,
                        "length": len(word)
                    })
            else:
                ball["letter"] = 0





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
        self.received_ids = set()

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

            if balls:
                self.player2.balls = balls
            else:
                print("[WARN] Empty or bad ball sync received — keeping previous state.")
                print(balls)

            if new_balls:
                for b in new_balls:
                    if b["id"] not in self.received_ids:
                        self.received_ids.add(b["id"])
                        self.player.balls.append(b)
            else:
                print("FAIL")

            other_ids = {b["id"] for b in self.player2.balls}
            self.player.transfer_queue = [
                b for b in self.player.transfer_queue if b["id"] not in other_ids
            ]


            # Update Canvas
            self.canvas.draw_background(elapsed_time)
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.canvas.update()


        self.game_end()

        pygame.quit()

    def send_data(self):
        try:
            ball_data = [{
                "id": b.get("id", generate_ball_id()),
                "x": b["rect"].x,
                "y": b["rect"].y,
                "word": b["word"],
                "letter": b["letter"],
                "length": b["length"]
            } for b in self.player.balls]

            for b in self.player.transfer_queue:
                if "id" not in b:
                    b["id"] = generate_ball_id()

            outgoing_transfer = self.player.transfer_queue[:]

            payload = {
                "id": self.net.id,
                "balls": ball_data,
                "new": outgoing_transfer
            }

            reply = self.net.send(json.dumps(payload))

            # Ensure the reply is valid JSON
            try:
                json.loads(reply)
                return reply
            except:
                print(f"[ERROR] Invalid JSON reply: {reply}")
                return json.dumps({"balls": [], "new": []})

        except Exception as e:
            print(f"[ERROR] Failed to send data: {e}")
            return json.dumps({"balls": [], "new": []})



    @staticmethod
    def parse_data(data):
        if not data or not data.strip():
            print("[ERROR] Empty or invalid data received in parse_data")
            return [], []

        try:
            print(f"[DEBUG] Raw data to parse: {repr(data)}")
            parsed = json.loads(data)

            balls = []
            for b in parsed["balls"]:
                rect = pygame.Rect(b["x"], b["y"], BALL_WIDTH, BALL_HEIGHT)
                balls.append({
                    "rect": rect,
                    "word": b["word"],
                    "letter": b["letter"],
                    "length": b["length"],
                    "id": b.get("id", generate_ball_id())
                })

            print("[DEBUG] Parsed balls:", balls)

            new = []
            if "new" in parsed:
                for b in parsed["new"]:
                    rect = pygame.Rect(b["x"], b["y"], BALL_WIDTH, BALL_HEIGHT)
                    new.append({
                        "rect": rect,
                        "word": b["word"],
                        "letter": 0,
                        "length": b["length"],
                        "id": b.get("id", generate_ball_id())
                    })

            print("[DEBUG] Parsed new balls:", new)
            return balls, new

        except Exception as e:
            print("[ERROR] parse_data exception:", e)
            pygame.quit()
            exit()

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


    def game_end(self):
        self.canvas.draw_background()

        p1_score = len(self.player.balls)
        p2_score = len(self.player2.balls)

        if p1_score < p2_score:
            message = "YOU WIN"
        elif p2_score > p1_score:
            message = "YOU LOSE"
        else:
            message = "TIE"

        self.canvas.draw_text(message, 40, WIDTH // 2, HEIGHT // 2, "white")
        self.canvas.update()
        time.sleep(5)



class Canvas:

    def __init__(self, w, h, name="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w,h))
        pygame.display.set_caption(name)

    @staticmethod
    def update():
        pygame.display.update()

    def draw_text(self, text, size, center_x, center_y, color="white"):
        pygame.font.init()
        font = pygame.font.SysFont("comicsans", size)
        render = font.render(text, True, color)
        text_rect = render.get_rect(center=(center_x, center_y))
        self.screen.blit(render, text_rect)


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


