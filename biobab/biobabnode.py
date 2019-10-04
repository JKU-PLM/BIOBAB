import sys
import math

from gurobipy import *

import segment
import lowerboundset
import params
import util
import upperboundset

def scalar(p, beta, alpha):
    return p[0] * beta + p[1] * alpha

def definesValidLB(p1, p2):
    a = ( p2[1] - p1[1] ) / ( p2[0] - p1[0] )
    b = p1[1] - a * p1[0]
    x, y = params.inputData.ceilCoords( p1[0], p2[1] )
    return y > a * x + b

# used to determine if two solutions to the same weighted sum problem are
# close enough that we can say they are the same
def similarValues(ub, opt):
    if math.fabs(opt) < params.onSegmentTolerance:
        return math.fabs(ub - opt) <= params.onSegmentTolerance
    else:
        return math.fabs( (ub - opt) / opt ) <=  params.onSegmentTolerance

class Node:
    def __init__(self, lp, right=util.infinity, top=util.infinity,
                 branchingDecisions=[], depth=0):
        self.lp = lp
        self.right = right
        self.top = top
        self.branchingDecisions = branchingDecisions
        self.depth = depth
        # used for best-first tree exploration
        self.score = self.right * self.top

    def __repr__(self):
        return 'Node(' + str(self.lp) + ', ' + str(self.right) + ', ' + \
            str(self.top) + ', ' + str(self.branchingDecisions) + ')'
        
    def lowerBound(self, upperBound=None):
        # use an array as a stack to store segments that need to be processed
        C = []
        # use a set for segments that are part of the convex hull
        E = []
        # done in different places
        def addIfMustSub(c1, c2, E, metaData):
            # we can improve the value of 'right' using the fact that the
            # same space is also covered by the segment right of that one
            # we use C as a stack so if there is an item in C, there is an
            # segment right of this one
            s = segment.Segment(c1, c2,
                                c2[0] if len(C) > 0 else self.right,
                                self.top,
                                metaData[c1],
                                metaData[c2])
            if s.shouldBeConsidered():
                E.append(s)
        #
        metaData = {}
        # store user setting
        mc = params.mipCutoff
        params.mipCutoff = False
        # we give an empty ub set for calculating this point, in order to
        # avoid cutoff at this stage (we need metadat on this solution)
        e1 = self.lp.lexmin(1, self.right, self.top, upperBound)
        # case where the model is infeasible
        if e1 is None:
            return lowerboundset.LowerBoundSet([])
        metaData[e1] = lowerboundset.LBMetaData(self.lp)
        # regular case
        e2 = self.lp.lexmin(2, self.right, self.top, upperBound)
        if e2 is None:
            return lowerboundset.LowerBoundSet([])
        metaData[e2] = lowerboundset.LBMetaData(self.lp)
        params.mipCutoff = mc
        if params.verbosity > 2:
            print
            print '*** extreme points:'
            print '\te1 =', e1
            print '\te2 =', e2
        C.append((e1, e2))
        # main loop: process segments in the stack until it's empty
        while len(C) > 0:
            # pop the segment to process
            c1, c2 = C.pop()
            if util.closeEnough(c1, c2):
                c2 = c1
            if params.verbosity > 2:
                print
                print 'processing:', c1, c2
            if c1[0] > c2[0]:
                print 'Error: inconsistent segment:', c1, c2
                print util.closeEnough(c1, c2)
                sys.exit(8)
            # if these points already define a valid LB segment we don't need
            # to process this segment further
            if c1 == c2 or (params.lbLifting and definesValidLB(c1, c2)):
                if params.verbosity > 2:
                    print 'defines a valid LB!'
                addIfMustSub(c1, c2, E, metaData)
                continue
            # compute the new weights
            alpha = float(c2[0] - c1[0])
            beta = float(c1[1] - c2[1])
            # alpha, beta = 1, beta / alpha
            c3 = self.lp.solveWeightedSum(beta, alpha,
                                          self.right, self.top,
                                          upperBound)
            if params.verbosity > 2:
                print'\tbeta:', beta
                print'\talpha:', alpha
                if not c3 is None:
                    print '\tscalarised c1:', scalar(c1, beta, alpha)
                    print '\tscalarised c2:', scalar(c2, beta, alpha)
                    print '\tscalarised c3:', scalar(c3, beta, alpha)
                else:
                    print '\t/!\\ No feasible solution,',
                    print 'this should not occur unless we are solving a MIP'
            if c3 is None:
                pass
            # is this new point on the segment?
            elif similarValues(scalar(c1, beta, alpha),
                               scalar(c3, beta, alpha)):
                addIfMustSub(c1, c2, E, metaData)
                if params.verbosity > 2:
                    print '\t--> segment in hull:', (c1, c2)
            else:
                # otherwise: two new segments must be processed
                # when stacking them in this order E is automatically sorted
                # from left to right
                C.append((c3, c2))
                C.append((c1, c3))
                if params.verbosity > 2:
                    print '\t--> new point:', c3
                metaData[c3] = lowerboundset.LBMetaData(self.lp)
        return lowerboundset.LowerBoundSet(E)

    def applyBranchingDecisions(self):
        for decision in self.branchingDecisions:
            decision.apply(self)

    def cancelBranchingDecisions(self):
        for i in xrange(len(self.branchingDecisions)):
            self.branchingDecisions[len(self.branchingDecisions) - 1 - i].\
                cancel(self)
