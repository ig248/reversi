# coding=utf-8
from game import *
import numpy as np
import re


class Player(object):
    """Meta-class for a player"""
    NAME = None
    
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
    NAME = 'Human'
    
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
    NAME = 'Random'
    
    def __init__(self, board=None):
        super(Player_Random, self).__init__(board)
    
    def decide(self):
        moves = self.board.legal_moves()
        if moves:
            return moves[np.random.randint(0, len(moves))]
        else:
            return (None, None)


class Player_Value(Player):
    """A player who seeks to maximize specified value function"""

    def value_function(self):
        """A signed value function indicating black player advantage"""        
        raise NotImplementedError
    
    def decide(self):
        self.board.stash()
        best_move = (None, None) # pass value
        best_score = None
        for (mr, mc) in self.board.candidate_moves():
            if self.board.move(mr, mc):
                # board player has been updated!
                score = self.value_function()
                if (best_score is None) or (score > best_score):
                    best_score = score
                    best_move = (mr, mc)
            self.board.pop()
        return best_move


def simple_value(board):
    """Simply return count advantage"""
    return -board.player * board.value.sum()


def linear_value(board, weights=1):
    """Using matrix of weights"""
    return -board.player * (board.value * weights).sum()


class Player_Greedy(Player_Value):
    """A player who picks a turn leading to maximum gains"""
    NAME = 'Greedy'
    
    def value_function(self):
        return simple_value(self.board)
    
    def __init__(self, board=None):
        super(Player_Greedy, self).__init__(board, va)
    
    
class Player_Weighted(Player_Value):
    """A player who picks a turn leading to maximum value as determined by weights
    see e.g. weights here: http://www.samsoft.org.uk/reversi/strategy.htm"""
    NAME = 'Weighted'
    
    def_packed_weights = [99,  -8,  8,  6,
                              -24, -4, -3,
                                    7,  4,
                                        0]
    
    def unpack_weights(self):
        assert len(self.packed_weights) == SIDE/2 * (SIDE/2 + 1) / 2
        quarter = np.zeros((SIDE/2, SIDE/2))
        # fill upper diagonal
        idx = np.triu_indices(SIDE/2)
        quarter[idx] = self.packed_weights
        # symmetrize
        quarter = quarter + quarter.T - np.diag(quarter.diagonal())
        # flip down
        half = np.vstack([quarter, np.flipud(quarter)])
        # flip right
        self.weights = np.hstack([half, np.fliplr(half)])
        return self.weights
        
    def value_function(self):
        return linear_value(self.board, self.weights)
    
    def __init__(self, board=None, packed_weights=None):
        super(Player_Weighted, self).__init__(board)
        if packed_weights:
            self.packed_weights = packed_weights
        else:
            self.packed_weights = self.def_packed_weights
                
        self.unpack_weights()
