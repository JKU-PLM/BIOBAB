import string
import sys
import itertools
import math

from biobab import util
from biobab import basicdata

validEpsilon = 0.9

class Instance(basicdata.BasicData):
    def __init__(self, fName):
        self.nPoints = 0
        for line in open(fName):
            # remove comments
            line = line[:line.find('#')]
            tokens = line.split()
            if len(tokens) != 0:
                # case where we read the first line
                if self.nPoints == 0:
                    self.nPoints = string.atoi(tokens[0])
                    self.nSamples, self.dmax1, self.dmax2, self.zeta = \
                        [ string.atoi(x) for x in tokens[3:] ] 
                    # at this point we can initialise our data
                    self.x, self.y, self.name = [], [], []
                    self.w = [ 0 ]
                    self.c = [ 0 ]
                    self.gamma = [ 0 ]
                    self.xi = {}
                    self.d = {}
                # case where we read info on a village
                elif len(self.x) < self.nPoints:
                    self.x.append( string.atof(tokens[1]) )
                    self.y.append( string.atof(tokens[2]) )
                    self.name.append( reduce( lambda x, y: x + ' ' + y,
                                              tokens[3:] ) )
                # one line of the distance matrix
                elif len(self.d) < self.nPoints ** 2:
                    row = len(self.d) / self.nPoints
                    for col, tok in enumerate(tokens):
                        self.d[row,col] = string.atof(tok)
                # read node cost
                elif len(self.c) < self.nPoints:
                    self.c.append( string.atoi(tokens[1]) )
                # read baseline demand
                elif len(self.w) < self.nPoints:
                    self.w.append( string.atoi(tokens[1]) )
                # read node capacity
                elif len(self.gamma) < self.nPoints:
                    self.gamma.append( string.atoi(tokens[1]) )
                # read sample scenario
                elif len(self.xi) < self.nPoints * self.nSamples:
                    scenario = len(self.xi) / self.nPoints
                    for j, tok in enumerate(tokens):
                        self.xi[0,scenario] = 0
                        self.xi[j+1,scenario] = string.atof(tok) / self.zeta
                else:
                    print 'error: unexpected input'
                    print line
                    sys.exit(9)
        # psi function for share of clients willing to go from i to j
        self.psi = lambda d: 1.0 if d <= self.dmax1 else \
            .5 if d <= self.dmax2 else 0
        # default values, could be modified by normalising
        self.costBound = sum(self.c)
        self.coverageBound = 0
        # deterministic version: only one sample, every xi value is 1
        self.nSamples = 1
        for i in xrange(self.nPoints):
            self.xi[i, 0] = 1
        #
        self.z1Epsilon = util.listGCD(self.c)
        self.z2Epsilon = 1.0 / self.nSamples
        #
        print 'z1Epsilon =', self.z1Epsilon
        print 'z2Epsilon =', self.z2Epsilon

    def boundRight(self):
        return util.infinity

    def boundTop(self):
        return util.infinity
