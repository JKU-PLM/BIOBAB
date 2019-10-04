import sys
import math

import params
import util
import treesearch
import biobabnode
import lowerboundset
import upperboundset
import segment
import basiclp

# This class allows us to solve a single-objective version of a
# bi-objective problem
# w1 and w2 are the weights used to produce a weighted-sum objective
# if one of them is zero, then both are considered in a lexicographic fashion
class WeightedSumNode(biobabnode.Node):

    # weight for each objective
    # they are set externally
    w1 = 1
    w2 = 1

    def wsValue(self, z1, z2):
        return self.w1 * z1 + self.w2 * z2
    
    def lowerBound(self, upperBound=None):
        e1 = self.lp.solveWeightedSum(self.w1, self.w2,
                                      self.right, self.top, upperBound)
        # case where the model is infeasible
        if e1 is None:
            return lowerboundset.LowerBoundSet([])
        else:
            # look for a better existing UB
            for u in upperBound.solutions:
                if self.wsValue(u.z1, u.z2) <= self.wsValue(*e1):
                    # cutoff
                    return lowerboundset.LowerBoundSet([])
            # ugly but necessary
            x, y = e1
            if self.right < x and \
               x - self.right < params.feasibilityTolerance:
                x = self.right
            if self.top < y and \
               y - self.top < params.feasibilityTolerance:
                y = self.top
            e1 = (x, y)
            #
            md = lowerboundset.LBMetaData(self.lp)
            s = segment.Segment(e1, e1,
                                self.right,
                                self.top,
                                md,
                                md)
            return lowerboundset.LowerBoundSet( [ s ] )

class WeightedSumBounder(treesearch.Bounder):
    def __init__(self, w1, w2):
        self.w1 = w1
        self.w2 = w2

    def bound(self, node, ub):
        lb = node.lowerBound(ub)
        if len(lb.segments) == 0:
            return lb
        # lb should contain only one point
        point = lb.segments[0].p1
        wsum = self.w1 * point[0] + self.w2 * point[1]
        # weighted-sum single-objective filtering
        for u in ub.solutions:
            if self.w1 * u.z1 + self.w2 * u.z2 < wsum:
                return lowerboundset.LowerBoundSet([])
        return lb

class WeightedSumSolver:
    def solve(self, lp, w1, w2, right, top, ub):
        if params.verbosity > 2:
            print util.TS(),
            print '*** optimising weighted sum:', w1, w2, '\t|\tz1 <=', \
                right, '\t|\tz2 <=', top
            print '\tUB:', ub
        WeightedSumNode.w1, WeightedSumNode.w2 = w1, w2
        rootNode = WeightedSumNode(lp, right=right, top=top)
        bounder = WeightedSumBounder(w1, w2)
        ts = treesearch.TreeSearch(nodeClass=WeightedSumNode,
                                   strategy=params.strategy)
        params.verbosity -= 2
        thisUb = upperboundset.UpperBoundSet()
        ts.search(rootNode, thisUb, wrapped=True, bounder=bounder,
                  branchers=[
                      treesearch.FractionalAverageBinaryPriorityBrancher(),
                      treesearch.ClosestToOneBinaryPriorityBrancher(),
                      treesearch.FurthestToOneBinaryPriorityBrancher(),
                      treesearch.OftenFractionalBinaryPriorityBrancher(),
                      treesearch.FractionalOnAverageBinaryPriorityBrancher(),
                  ]
        )
        params.verbosity += 2
        # now find the solution
        best = None
        for u in thisUb.solutions:
            if u.z1 <= right and u.z2 <= top:
                if best is None:
                    best = u
                elif u.z1 * w1 + u.z2 * w2 < best.z1 * w1 + best.z2 * w2:
                    best = u
            # add newly found solutions to existing ub set
            ub.updateWithSolution(u)
        #
        if params.verbosity > 2 and best:
            print '\tobjective values:', best.z1, best.z2
            print '\tweighted sum:', best.z1 * w1 + best.z2 * w2
        # finally, return best solution found
        if best is None:
            return None
        else:
            return best.z1, best.z2

class LexminSolver:
    def __init__(self):
        self.wsSolver = WeightedSumSolver()

    def solve(self, lp, firstObj, right, top, ub):
        if params.lexminMethod == 'lex':
            return self.solveLex(lp, firstObj, right, top, ub)
        elif params.lexminMethod == 'ws':
            return self.solveWS(lp, firstObj, right, top, ub)
        else:
            print 'Error: unknown method for calculating lexmin points:',
            print params.lexMinMethod
            sys.exit(22)
        
    def solveLex(self, lp, firstObj, right, top, ub):
        w1, w2 = (1, 0) if firstObj == 1 else (0, 1)
        point = self.wsSolver.solve(lp, w1, w2, right, top, ub)
        if point is None:
            return None
        else:
            r = point[0] if firstObj == 1 else util.infinity
            t = point[1] if firstObj == 2 else util.infinity
            return self.wsSolver.solve(lp, w2, w1, r, t, ub)
        
    def solveWS(self, lp, firstObj, right, top, ub):
        w1, w2 = (1, lp.wsEpsilon) if firstObj == 1 else (lp.wsEpsilon, 1)
        return self.wsSolver.solve(lp, w1, w2, right, top, ub)
