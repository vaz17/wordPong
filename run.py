import game

if __name__ == "__main__":
    g = game.Game(1000,800)
    g.wait_for_opponent()
    g.run()
