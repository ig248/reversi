from reversi import *
if __name__ == "__main__":
    g = Game(playerB=Player_Human(), playerW=Player_Weighted())
    g.play()