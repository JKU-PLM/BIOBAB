import sys

import params
import util

aboveSegmentTolerance = 1e-8

class Segment:
    # a point is a 2-uple
    def __init__(self, p1, p2, right, top, metaData1, metaData2):
        self.p1, self.p2 = p1, p2
        self.right, self.top =  right, top
        if self.p1 != self.p2 and not util.closeEnough(p1, p2):
            self.a = (self.p2[1] - self.p1[1]) / (self.p2[0] - self.p1[0])
            self.b = self.p1[1] - self.a * self.p1[0]
        else:
            self.a, self.b = None, None
        self.metaData1 = metaData1
        self.metaData2 = metaData2

    # u is a feasible integer solution
    # filtering a segment with a solution results in a list of segments
    def filter(self, u):
        res = []
        if params.integerDominance:
            z1, z2 = u.improvedZ1, u.improvedZ2
        else:
            z1, z2 = u.z1, u.z2
        # case where p1 and p2 don't change for sure
        if z2 >= self.p1[1] or z1 >= self.p2[0] or \
           (self.a and z2 >= self.a * z1 + self.b):
            if z1 <= self.p1[0]:
                s = Segment(self.p1, self.p2, self.right, min(self.top, z2),
                            self.metaData1, self.metaData2)
                if s.shouldBeConsidered():
                    res.append(s)
            elif z2 <= self.p2[1]:
                s = Segment( self.p1, self.p2, min(self.right, z1), self.top,
                             self.metaData1, self.metaData2 )
                if s.shouldBeConsidered():
                    res.append(s)
            else:
                if self.shouldBeConsidered():
                    res.append(self)
        # general case
        else:
            # left part of the segment still here
            if z1 > self.p1[0]:
                s = Segment(self.p1, (z1, self.a * z1 + self.b),
                            z1, self.top,
                            self.metaData1, self.metaData2)
                if s.shouldBeConsidered():
                    res.append(s)
            # right part of the segment still here
            if z2 > self.p2[1]:
                s = Segment( ( (z2 - self.b) / self.a, z2), self.p2,
                             self.right, z2,
                             self.metaData1, self.metaData2 )
                if s.shouldBeConsidered():
                    res.append(s)
        return res

    # True if this segment should be considered, False otherwise
    def shouldBeConsidered(self):
        return (not params.segmentTightening) or self.containsIntegerPoint()

    # True if there is an integer point in the space covered by that segment
    def containsIntegerPoint(self):
        x, y = params.inputData.floorCoords(self.right, self.top)
        return ( self.p1 == self.p2 or util.closeEnough(self.p1, self.p2) or \
                     y + aboveSegmentTolerance >= self.a * x + self.b ) \
            and y >= self.p2[1] and x >= self.p1[0]
    
    def __lt__(self, s):
        return self.p1[0] < s.p1[0]

    def __repr__(self):
        return '[ ' + str(self.p1) + ' - ' + str(self.p2) + ' \t|\t (' + \
            str(self.right) + ', ' + str(self.top) + ') ]'

    # special output for visualisation in another script
    def vizOut(self, colour):
        return 'DLine( ' + \
            util.vizOutPoint(self.p1, colour) + ', ' + \
            util.vizOutPoint(self.p2, colour) + \
            ', boundTop=' + str(self.top) + \
            ', boundRight=' + str(self.right) + \
            ', colour=' + colour + ')'
