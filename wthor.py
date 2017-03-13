import datetime
import struct

class Header(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def __str__(self):
        return '<Header>' + str(self.__dict__)
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def from_fobj(self, fobj):
        fobj.seek(0)
        raw = fobj.read(16)
        s = struct.unpack(
            '<BBBBLHHBBBB', raw)
        fcentury, fyear, fmonth, fday, n1, n2, year, size, type, depth, _ = s
        if size == 10:
            raise Error('Size 10 not implemented')
        return Header(
            fdate=datetime.date(100*fcentury + fyear, fmonth, fday),
            n1=n1,
            n2=n2,
            year=year,
            size=size,
            type=type,
            depth=depth
        )

    
class Players(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def __str__(self):
        return '<Players>' + str(self.__dict__)
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def from_fobj(self, fobj):
        p = Players()
        # Read header
        p.header = Header.from_fobj(fobj)
        # read player entries
        p.players = [
            fobj.read(20).strip('\x00')
            for i in xrange(p.header.n2)
        ]
        return p
    
    
class Tournaments(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def __str__(self):
        return '<Players>' + str(self.__dict__)
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def from_fobj(self, fobj):
        t = Tournaments()
        # Read header
        t.header = Header.from_fobj(fobj)
        # read player entries
        t.tournaments = [
            fobj.read(26).strip('\x00')
            for i in xrange(t.header.n2)
        ]
        return t

    
class Game(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def __str__(self):
        return '<Game>' + str(self.__dict__)
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def from_fobj(self, fobj, header):
        if not header.size:
            header.size = 8
        if not header.depth:
            header.depth = 22
        g = Game(size=header.size,
                 type=header.type,
                 year=header.year,
                 depth=header.depth
                )
        raw = fobj.read(8)
        s = struct.unpack(
            '<HHHBB', raw)
        tournament, player_b, player_w, score, score_th = s
        
        arr = fobj.read(header.size**2-4)
        
        g.tournament=tournament
        g.player_b=player_b
        g.player_w=player_w
        g.score=score
        g.score_th=score_th
        #g.arr = arr
        
        return g

    
class Games(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    
    def __str__(self):
        return '<Players>' + str(self.__dict__)
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def from_fobj(self, fobj):
        g = Games()
        # Read header
        g.header = Header.from_fobj(fobj)
        # read game entries
        g.games = [
            Game.from_fobj(fobj, header=g.header)
            for i in xrange(g.header.n1)
        ]
        return g