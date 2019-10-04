import sys

import params
import util
from weightedsumsolver import WeightedSumNode, WeightedSumSolver, LexminSolver

class EpsilonConstraintFramework:
    def __init__(self, relaxed):
        self.relaxed = relaxed
        if relaxed:
            self.solver = LexminSolver()
        
    def solve(self, lp, ub, singleObj):
        # initialisations...
        right = lp.validBoundRight or params.inputData.boundRight()
        top = lp.validBoundTop or params.inputData.boundTop()
        print util.TS(), '\tStarting epsilon-constraint',
        print 'with boundRight =', right, 'and boundTop =', top
        if singleObj == 1:
            print '\t\tOptimising z1 first'
        elif singleObj == 2:
            print '\t\tOptimising z2 first'
        else:
            print 'Error: invalid objective:', singleObj
            sys.exit(22)
        try:
            while True:
                z1, z2 = None, None
                if self.relaxed:
                    point = self.solver.solve(lp, singleObj, right, top, ub)
                else:
                    point = lp.lexmin(singleObj, right, top, ub)
                if point:
                    z1, z2 = point
                #
                if z1 is None:
                    print util.TS() + '\tepsilon-constraint',
                    print 'framework is over'
                    return
                else:
                    if params.verbosity > 0:
                        print util.TS() + '\tNew solution:\tz1 =', z1, \
                                                        '\tz2 =', z2
                    if singleObj == 1:
                        top = z2 - params.inputData.z2Epsilon
                    else:
                        right = z1 - params.inputData.z1Epsilon
        except util.TimeLimitReachedException as e:
            print e
        print util.TS() + '\tepsilon-constraint framework is over'        

# Bi-directional epsilon constraint framework
class BDEpsilonConstraintFramework(EpsilonConstraintFramework):
    def solve(self, lp, ub, firstObj):
        # initialisations...
        right = lp.validBoundRight or params.inputData.boundRight()
        top = lp.validBoundTop or params.inputData.boundTop()
        localRight, localTop = right, top
        print util.TS(), '\tStarting bi-directional epsilon-constraint',
        print 'with boundRight =', right, 'and boundTop =', top
        currentObj = firstObj
        lastFound = None
        try:
            while True:
                z1, z2 = None, None
                r, t = (right, localTop) if currentObj == 1 else (localRight, top)
                if self.relaxed:
                    point = self.solver.solve(lp, currentObj, r, t, ub)
                else:
                    point = lp.lexmin(currentObj, r, t, ub)
                if point:
                    z1, z2 = point
                if lastFound and util.closeEnough(point, lastFound):
                    print util.TS() + '\tepsilon-constraint',
                    print 'framework is over'
                    return
                else:
                    lastFound = point
                    if params.verbosity > 0:
                        print util.TS() + '\tNew solution:\tz1 =', z1, \
                                                        '\tz2 =', z2
                    if currentObj == 1:
                        localTop = z2 - params.inputData.z2Epsilon
                        currentObj = 2
                    else:
                        localRight = z1 - params.inputData.z1Epsilon
                        currentObj = 1
        except util.TimeLimitReachedException as e:
            print e
        print util.TS() + '\tepsilon-constraint framework is over'        
