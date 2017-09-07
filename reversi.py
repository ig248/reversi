# coding=utf-8
import numpy as np
from scipy.signal import convolve2d
import re

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
        self.board = np.zeros((self.side, self.side), dtype=np.int8)
        # 1 = black, -1 = white
        self.board[4, 3] = 1
        self.board[3, 4] = 1
        self.board[3, 3] = -1
        self.board[4, 4] = -1
    
    def stash(self):
        self._stash_board = self.board.copy()
        self._stash_turn = self.turn
        
    def pop(self):
        self.board = self._stash_board.copy()
        self.turn = self._stash_turn
    
    def candidate_moves(self):
        """List neighbours that would make turn candidates
        a cell is a good candidate if (a) it is empty and (b) any neighbour is the opposite of self.turn
        """
        candidates = np.logical_and(
            self.board == CELL_EMPTY,
            convolve2d(self.board == self.opponent, NKERNEL, mode='same'),
            #convolve2d(self.board == self.player, DKERNEL, mode='same'),
        )
        
        return np.vstack(np.where(candidates)).T
    
    def move(self, r, c, check_only=False):
        """Attempt to place the next piece at (r, c)
        Turn is decided based on self.turn
        """
        # if we are trying to place in a non-empty cell, return
        if self.board[r, c]:
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
                if not self.board[rr, cc]: # terminate (unsuccesfully) at an empty cell
                    break
                elif self.board[rr, cc] == player: # terminate at our own stone
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
            self.board[ridx, cidx] = player
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
        counts = dict(zip(*np.unique(self.board, return_counts=True)))
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
        row_strings = [row_str(row) for row in self.board]
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
        
    def play(self, reset=False, verbose=0):
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
    
class Player(object):
    """Meta-class for a player"""
    def __init__(self, board=None):
        self.board = board
    
    def decide(self):
        """Return (r, c) of desired move"""
        return (None, None) # (none, none) for pass
    
    def play(self):
        r, c = self.decide()
        if r is None or c is None:
            self.board.pass_move()
            return False # pass
        legal = self.board.move(r, c)
        if not legal:
            raise ValueError("Illegal move attemted: (%d, %d)" % (r, c))
        return True

class Player_Human(Player):
    """A player following inputs from a human"""
    def __init__(self, board=None):
        super(Player_Human, self).__init__(board)
    
    def decide(self):
        # clear output
        try:
            __IPYTHON__
            from IPython.display import clear_output
            clear_output()
        except NameError:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
        print self.board
        moves = self.board.legal_moves()
        if not moves:
            print "No valid turns!"
            return (None, None)
        else:
            while True:
                human_input = raw_input('Enter valid row, column: ')
                human_input = re.split(';|,| |\(|\)|', human_input)
                try:
                    r, c = [int(elt) for elt in human_input]
                    if (r, c) in moves:
                        return (r, c)
                except:
                    continue
    
class Player_Random(Player):
    """A player who picks a valid turn at random"""
    def __init__(self, board=None):
        super(Player_Random, self).__init__(board)
    
    def decide(self):
        moves = self.board.legal_moves()
        if moves:
            return moves[np.random.randint(0, len(moves))]
        else:
            return (None, None)
        
class Player_Greedy(Player):
    """A player who picks a turn leading to maximum gains"""
    def __init__(self, board=None):
        super(Player_Greedy, self).__init__(board)
    
    def decide(self):
        self.board.stash()
        best_move = (None, None) # pass value
        best_score = -64
        for (mr, mc) in self.board.candidate_moves():
            if self.board.move(mr, mc):
                plr, opp = self.board.ordered_score
                score = opp - plr # board player has been updated!
                if score > best_score:
                    best_score = score
                    best_move = (mr, mc)
            self.board.pop()
        return best_move
    
class Player_Weighted(Player):
    """A player who picks a turn leading to maximum value as determined by weights
    see e.g. weights here: http://www.samsoft.org.uk/reversi/strategy.htm"""
    WEIGHTS = np.array([
        [99, -8, 8, 6, 6, 8, -8, 99],
        [-8,-24,-4, -3, -3, -4, -24, -8],
        [8, -4, 7, 4, 4, 7, -4, 8],
        [6, -3, 4, 0, 0, 4, -3, 6],
        [6, -3, 4, 0, 0, 4, -3, 6],
        [8, -4, 7, 4, 4, 7, -4, 8],
        [-8,-24,-4, -3, -3, -4, -24, -8],
        [99, -8, 8, 6, 6, 8, -8, 99]
    ])
    def __init__(self, board=None):
        super(Player_Weighted, self).__init__(board)
    
    def decide(self):
        self.board.stash()
        best_move = (None, None) # pass value
        best_score = -64*99
        for (mr, mc) in self.board.candidate_moves():
            if self.board.move(mr, mc):
                # board player has been updated!
                score = -self.board.player*(self.board.board * self.WEIGHTS).sum()
                if score > best_score:
                    best_score = score
                    best_move = (mr, mc)
            self.board.pop()
        return best_move