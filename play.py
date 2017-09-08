from reversi.game import Game
from reversi.players import Player_Human, Player_Weighted

if __name__ == "__main__":
    g = Game(playerB=Player_Human(), playerW=Player_Weighted())
    g.play()
