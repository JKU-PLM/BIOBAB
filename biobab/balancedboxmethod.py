import sys

import params
import util
import integersolution
import flexiblequeue
import treesearch
import biobabnode
import upperboundset

from weightedsumsolver import WeightedSumSolver, LexminSolver

class Rectangle:
    def __init__(self, z1, z2):
        self.z1 = z1
        self.z2 = z2
        # area * -1 _ we want to consider rectangles in non-decreasing order
        # of their area
        self.score = (z1[0] - z2[0]) * (z1[1] - z2[1])
        
    def __repr__(self):
        return 'Rectangle(' + str(self.z1) + ', ' + str(self.z2) + ')'

    # point is a (x, y) tuple
    def __contains__(self, point):
        return point[0] >= self.z1[0] and point[0] <= self.z2[0] and  \
            point[1] >= self.z2[1] and point[1] <= self.z1[1]
        
class BalancedBoxMethod(treesearch.TreeSearch):
    def __init__(self, relaxed, strategy='breadth', nodeClass=biobabnode.Node):
        treesearch.TreeSearch.__init__(self,
                                       strategy='best',
                                       nodeClass=nodeClass)
        self.relaxed = relaxed
        # used multiple times
        if relaxed:
            self.wsSolver = WeightedSumSolver()
            self.lmSolver = LexminSolver()
            
    def solveLexmin(self, lp, firstObj, right, top, ub, R=None):
        if self.relaxed:
            return self.lmSolver.solve(lp, firstObj, right, top, ub)
        else:
            return lp.lexmin(firstObj, right, top, ub)
            
    def solveWS(self, lp, w1, w2, right, top, ub):
        self.harvested = upperboundset.UpperBoundSet()
        if self.relaxed:
            point = self.wsSolver.solve(lp, w1, w2, right, top, self.harvested)
        else:
            point = lp.solveWeightedSum(w1, w2, right, top, self.harvested)
        for u in self.harvested.solutions:
            ub.updateWithSolution(u)
        return point

    # push rectangle R into the queue of rectangles to process, but only if
    # there is an actual possibility that it contains a non-dominated
    # integer solution
    def pushIfMust(self, R):
        if R.z2[0] - R.z1[0] > params.inputData.z1Epsilon and \
           R.z1[1] - R.z2[1] > params.inputData.z2Epsilon:
            if params.verbosity > 1:
                print '(BBM)\tPushing', R
            self.queue.push(R)
            
    def search(self, lp, ubSet):
        # initialisations...
        self.right = lp.validBoundRight or params.inputData.boundRight()
        self.top = lp.validBoundTop or params.inputData.boundTop()
        print 'Starting balanced box method with boundRight =', self.right,
        print 'and boundTop =', self.top
        # queue of boxes that still need to be processed
        try:
            # extreme points
            #zT = lp.lexmin(1, self.right, self.top, ubSet)
            zT = self.solveLexmin(lp, 1, self.right, self.top, ubSet)
            print  util.TS() + '\t\tzT:\tz1 =', zT[0], '\tz2 =', zT[1]
            #zB = lp.lexmin(2, self.right, self.top, ubSet)
            zB = self.solveLexmin(lp, 2, self.right, self.top, ubSet)
            print  util.TS() + '\t\tzB:\tz1 =', zB[0], '\tz2 =', zB[1]
            self.area = (zB[0] - zT[0]) * (zT[1] - zB[1])
            if params.verbosity > 1:
                print 'Area of initial rectangle:', self.area
            # add the first box to the list of boxes that need to be processed
            self.pushIfMust( Rectangle(zT, zB) )
            # main loop
            while not self.queue.empty():
                R = self.queue.pop()
                self.exploreRectangle(R, lp, ubSet)
        # we're done
        except util.TimeLimitReachedException as e:
            print e
        print util.TS() + '\tbalanced box method is over'        

    # explore rectangle R
    # side effect: self.queue is updated with new rectangles that
    # should be explored
    def exploreRectangle(self, R, lp, ubSet):
        if params.verbosity > 1:
            print '(BBM)'
            print '(BBM) processing rectangle:', R,
            print 'with area', - R.score,
        if R.z2[0] - R.z1[0] <= params.inputData.z1Epsilon or \
           R.z1[1] - R.z2[1] <= params.inputData.z2Epsilon:
            if params.verbosity > 1:
                print '\t--> skipping'
                return
        elif self.area * params.balancedBoxBeta < - R.score:
            if params.verbosity > 1:
                print 'with harvest'
            self.exploreRectangleWithHarvesting(R, lp, ubSet)
        else:
            if params.verbosity > 1:
                print 'without harvest'
            self.exploreRectangleBasically(R, lp, ubSet)

    # basic version
    def exploreRectangleBasically(self, R, lp, ubSet):
        newY = (R.z1[1] + R.z2[1]) / 2.0
        if params.verbosity > 1:
            print '(BBM) \tnewY:', newY
        boundRight = self.right
        if newY - R.z2[1] >= params.inputData.z2Epsilon:
            z1Bar = self.solveLexmin(lp, 1, self.right, newY, ubSet, R)
        else:
            if params.verbosity > 1:
                print '(BBM)\tskipping too small bottom rectangle'
            z1Bar = R.z2
        if params.verbosity > 1:
            print '(BBM) \tz1Bar:', z1Bar
        if z1Bar and z1Bar[0] <= R.z2[0] - params.inputData.z1Epsilon:
            self.pushIfMust( Rectangle(z1Bar, R.z2) )
            print util.TS() + '\tNew solution:\tz1 =', z1Bar[0], \
                                                     '\tz2 =', z1Bar[1]
        newX = z1Bar[0] - params.inputData.z1Epsilon
        if params.verbosity > 1:
            print '(BBM) \tnewX:', newX
        boundTop = self.top
        if newX - R.z1[0] >= params.inputData.z1Epsilon:
            z2Bar = self.solveLexmin(lp, 2, newX, boundTop, ubSet, R)
        else:
            if params.verbosity > 1:
                print '(BBM)\tskipping too small top rectangle'
            z2Bar = R.z1
        if params.verbosity > 1:
            print '(BBM) \tz2Bar:', z2Bar
        if z2Bar and z2Bar[0] >= R.z1[0] + params.inputData.z1Epsilon:
            self.pushIfMust( Rectangle(R.z1, z2Bar) )
            print util.TS() + '\tNew solution:\tz1 =', z2Bar[0], \
                                                     '\tz2 =', z2Bar[1]

    # version with solution harvesting
    def exploreRectangleWithHarvesting(self, R, lp, ubSet):
        # step 1: solve a weighted sum with equal weights
        self.solveWS(lp, 1, 1, R.z2[0], R.z1[1], ubSet)
        # step 2: harvest solutions
        if self.relaxed:
            lHat = self.getIntegerSolutionsFromRect(R, self.harvested)
        else:
            lHat = self.getIntegerSolutionsFromRect(R,
                                                    lp.getSolutionPoolVectors())
        lHat.filterWith(ubSet)
        # special case: no solution was harvested
        if len(lHat.solutions) == 0:
            self.exploreRectangleBasically(R, lp, ubSet)
            return
        done = False
        # main loop
        while len(lHat.solutions) > 0 and not done:
            z1Hat = lHat.solutions[-1]
            Rb = Rectangle( (R.z1[0], z1Hat.z2 - params.inputData.z2Epsilon),
                            R.z2 )
            z1Bar = self.solveLexmin(lp, 1, R.z2[0], Rb.z1[1], ubSet, R)
            if not z1Bar:
                return
            if z1Bar and not util.closeEnough(z1Bar, R.z2):
                # no need to add z1Bar, it's already in ubSet
                print util.TS() + '\tNew solution:\tz1 =', z1Bar[0], \
                                                         '\tz2 =', z1Bar[1]
                self.pushIfMust(Rectangle(z1Bar, R.z2))
            Rt = Rectangle( R.z1,
                            (z1Bar[0] - params.inputData.z1Epsilon, z1Hat.z2) )
            if z1Hat.z1 < z1Bar[0] - util.epsilon:
                z2Bar = self.solveWS(lp, 1, 0, Rt.z2[0], z1Hat.z2, ubSet)
            else:
                lHat.solutions = [ zi for zi in lHat.solutions
                                   if (zi.z1, zi.z2) in Rt and zi != z1Hat ]
                z2Bar = self.solveLexmin(lp, 2, Rt.z2[0], Rt.z1[1], ubSet, R)
            if z2Bar and not util.closeEnough(z2Bar, R.z1):
                tmpR = Rectangle(R.z1, z2Bar)
                lHat.solutions = [ zi for zi in lHat.solutions
                                   if (zi.z1, zi.z2) in tmpR and zi != z1Hat
                                   and (zi.z1, zi.z2) != z2Bar ]
                if len(lHat.solutions) == 0:
                    done = True
                    # no need to add z2Bar here, it's already in ubSet
                    print util.TS() + '\tNew solution:\tz1 =', z2Bar[0], \
                                                             '\tz2 =', z2Bar[1]
                    self.pushIfMust( Rectangle(R.z1, z2Bar) )
                else:
                    R.z2 = z2Bar
                    
    def getIntegerSolutionsFromRect(self, R, ubSet):
        ub = upperboundset.UpperBoundSet()
        z1 = ( R.z1[0] + params.inputData.z1Epsilon,
               R.z1[1] - params.inputData.z2Epsilon )
        z2 = ( R.z2[0] - params.inputData.z1Epsilon,
               R.z2[1] + params.inputData.z2Epsilon )
        newRect = Rectangle(z1, z2)
        for u in ubSet.solutions:
            if (u.z1, u.z2) in newRect:
                ub.updateWithSolution(u)
        return ub
