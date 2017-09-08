# coding=utf-8
import numpy as np
from scipy.signal import convolve2d

SIDE = 8

PLAYER_B = 1
PLAYER_W = -PLAYER_B
CELL_EMPTY = 0

DIRNS = np.array([(xs, ys) for xs in [-1, 0, 1] for ys in [-1, 0, 1] if xs or ys])

# Kernel representing nearest neigbours
NKERNEL = np.ones((3, 3))
NKERNEL[1, 1] = 0

# Kernel representing all cells in 8 directions
DKERNEL = np.eye(2*SIDE-1)
DKERNEL = np.fliplr(DKERNEL)
np.fill_diagonal(DKERNEL, 1)
DKERNEL[SIDE-1, :] = 1
DKERNEL[:, SIDE-1] = 1
DKERNEL[SIDE-1, SIDE-1] = 0

class Board(object):
    side = SIDE
    _stash_board = None
    _stash_turn = None
    
    def __init__(self):
        """Reset board to starting position"""
        self.reset()
    
    def reset(self):
        """Reset board to starting position"""
        self.turn = PLAYER_B
        self.value = np.zeros((self.side, self.side), dtype=np.int8)
        # 1 = black, -1 = white
        self.value[4, 3] = 1
        self.value[3, 4] = 1
        self.value[3, 3] = -1
        self.value[4, 4] = -1
    
    def stash(self):
        self._stash_board = self.value.copy()
        self._stash_turn = self.turn
        
    def pop(self):
        self.value = self._stash_board.copy()
        self.turn = self._stash_turn
    
    def candidate_moves(self):
        """List neighbours that would make turn candidates
        a cell is a good candidate if (a) it is empty and (b) any neighbour is the opposite of self.turn
        """
        candidates = np.logical_and(
            self.value == CELL_EMPTY,
            convolve2d(self.value == self.opponent, NKERNEL, mode='same'),
            #convolve2d(self.value == self.player, DKERNEL, mode='same'),
        )
        
        return np.vstack(np.where(candidates)).T
    
    def move(self, r, c, check_only=False):
        """Attempt to place the next piece at (r, c)
        Turn is decided based on self.turn
        """
        # if we are trying to place in a non-empty cell, return
        if self.value[r, c]:
            return False   
        
        # else, try to turn along each diagonal
        player = self.player
        turned_idx = []
        for (rs, cs) in DIRNS:
            rr, cc = r + rs, c + cs
            diag_turned_idx = []
            diag_terminated = False
            # proceed until we hit an edge, or an empty cell, or our own cell
            while 0 <= rr and rr < self.side and 0 <= cc and cc < self.side:
                if not self.value[rr, cc]: # terminate (unsuccesfully) at an empty cell
                    break
                elif self.value[rr, cc] == player: # terminate at our own stone
                    diag_terminated = True
                    break
                else: # continue along unbroken line of opponent's stones
                    diag_turned_idx += [(rr, cc)]
                    rr, cc = rr + rs, cc + cs
                
            # if diagonal completed successfully, append cells to be turned
            if diag_terminated:
                if diag_turned_idx and check_only:
                    return True
                turned_idx += diag_turned_idx
        
        # if we have turned stones along any of the diagonals
        if turned_idx:
            turned_idx += [(r, c)]
            ridx, cidx = zip(*turned_idx)
            self.value[ridx, cidx] = player
            self.turn = self.opponent
            return True
        else:
            return False
    
    def legal_moves(self):
        moves = []
        for (mr, mc) in self.candidate_moves():
            if self.move(mr, mc, check_only=True):
                moves.append((mr, mc))
        return moves
    
    def pass_move(self):
        self.turn = self.opponent
        
    @property
    def player(self):
        """current player"""
        return self.turn
    
    @property
    def opponent(self):
        """opponent player"""
        return -self.turn
    
    @property
    def score(self):
        """Compute totals for each player"""
        counts = dict(zip(*np.unique(self.value, return_counts=True)))
        if 1 not in counts:
            counts[1] = 0
        if -1 not in counts:
            counts[-1] = 0    
        b, w = counts[1], counts[-1]
        return b, w
        
    @property
    def ordered_score(self):
        b, w = self.score
        if self.player is PLAYER_B:
            return b, w
        else:
            return w, b
    
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        """Return a string representation of the board"""
        SHOW_COORDS = True
        chars = {
            CELL_EMPTY: ". ", #.
            PLAYER_B: "◎ ",  #®
            PLAYER_W: "◉ ",  #©
        }
        def row_str(row):
            cell_chars = [chars[r] for r in row]            
            return ''.join(cell_chars)
        row_strings = [row_str(row) for row in self.value]
        if SHOW_COORDS:
            row_strings = ['%d %s' % (idx, rs) for idx, rs in enumerate(row_strings)]
            header_row = ''.join(['%d ' % d for d in range(self.side)])
            header_row = '  ' + header_row
            row_strings = [header_row] + row_strings
        score_string = 'Score: B[%s] =%d, W[%s]=%d' % (chars[PLAYER_B], self.score[0], chars[PLAYER_W], self.score[1])
        turn_string = 'Next turn: %s [%s]' % ('B' if self.turn == PLAYER_B else 'W', chars[self.turn])
        return '\n'.join([score_string, turn_string] + row_strings)


class Game(object):
    """Run a game between two players"""
    def __init__(self, playerB=None, playerW=None):
        self.board = Board()
        self.playerB = playerB
        self.playerW = playerW
        playerB.board = self.board
        playerW.board = self.board
    
    @property
    def current_player(self):
        if self.board.turn == PLAYER_B:
            return self.playerB
        else:
            return self.playerW
        
    def play(self, reset=True, verbose=0):
        """run a game"""
        if reset:
            self.board.reset()
        passes = 0
        while passes < 2:
            if self.current_player.play():
                passes = 0
            else:
                passes +=1
            if verbose:
                print self.board
        final_score = self.board.score
        return final_score


class Tournament(object):
    """Run a tournament between specified players"""
    def __init__(self, players=[], n=10, diagonal=False):
        """each pair of players play nx2 games (incl. swapping sides)"""
        self.players = players
        self.n_games = n
        self.n_players = len(players)
        self.diagonal = diagonal
        self.wins = np.zeros((self.n_players, self.n_players))
        self.draws = self.wins.copy()
        self.score = self.wins.copy() # 1 for win, 0.5 for draw, 0 for losee
        
    def play(self):
        for idxB, playerB in enumerate(self.players):
            for idxW, playerW in enumerate(self.players):
                if not self.diagonal and idxB==idxW:  # skip games against oneself
                    continue
                g = Game(playerB=playerB, playerW=playerW)
                for _ in range(self.n_games):
                    score = g.play()
                    if score[0] > score[1]:
                        self.wins[idxB, idxW] += 1
                    elif score[0] == score[1]:
                        self.draws[idxB, idxW] += 1
        self.score = self.wins + 0.5*self.draws # 1 for win, 0.5 for draw, 0 for losee
