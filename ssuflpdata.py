import sys
import math
import random
import itertools

from gurobipy import *

from biobab import basicdata, basiclp, integersolution, grbvalues, util

# used later to set Gurobi parameters
GurobiOptimalityTolerance = 1e-8
GurobiFeasibilityTolerance = 1e-8
GurobiIntFeasTol = GurobiFeasibilityTolerance
GurobiNumericFocus = 0

# classic single-source capacitated facility location problem
class SSCFLPInstance(basicdata.BasicData):
    def __init__(self, fName=None):
        self.loadFromFile(fName)
        self.z1Epsilon = util.listGCD( reduce(lambda x, y: x + y, self.c) )
        self.z2Epsilon = util.listGCD(self.f)
        print 'z1Epsilon =', self.z1Epsilon
        print 'z2Epsilon =', self.z2Epsilon

    def loadFromFile(self, fName):
        stage = 1
        for line in file.readlines(file(fName)):
            tokens = line.split()
            if len(tokens) == 0:
                continue
            else:
                if stage == 1:
                    self.n, self.m = int(tokens[0]), int(tokens[1])
                    self.s, self.f = [], []
                    self.c = []
                    stage = 2
                elif stage == 2:
                    self.s.append(int(tokens[0]))
                    self.f.append(int(tokens[1]))
                    if len(self.s) == self.n:
                        stage = 3
                elif stage == 3:
                    self.d = [ int(x) for x in tokens ]
                    stage = 4
                elif stage == 4:
                    row =  [ int(x) for x in tokens ]
                    self.c.append(row)
                    
    def __repr__(self):
        return 'SSCFLP instance with ' + str(self.n) + \
            ' facilities and ' + str(self.m) + ' customers'

    def boundRight(self):
        return util.infinity
        
    def boundTop(self):
        # return sum(self.f)
        return util.infinity


class SSUFLPModel(basiclp.BasicLP):
    def __init__(self, data, relaxed=False):
        self.model = Model('Single-source uncapacitated facility location problem')
        self.model._parent = self
        self.data = data
        # decision variables
        # fraction of the population at i assigned to j
        print util.TS() + '\tcreating x variables'
        self.x = {}
        vtype = GRB.CONTINUOUS if relaxed else GRB.BINARY
        for i, j in itertools.product(xrange(data.n), xrange(data.m)):
            self.x[i, j] = self.model.addVar( vtype=vtype,
                                              name='x_' + str(i) + '_' + \
                                              str(j), 
                                              ub=1 )
        self.y = {}
        for i in xrange(data.n):
            self.y[i] = self.model.addVar( vtype=vtype,
                                           name='y_' + str(i), 
                                           ub=1 )
        self.model.update()
        self.integerVars = self.y.values() + self.x.values()
        for i in xrange(data.n):
            self.y[i].setAttr(GRB.Attr.BranchPriority, 10)
        # Objective functions
        print util.TS() + '\tcreating objective expressions'
        # These attributes must be defined in order to benefit from methods
        # inherited from BasicLP
        self.z1Expr = quicksum( data.c[i][j] * self.x[i, j]
                                for i, j in \
                                itertools.product(xrange(data.n),
                                                  xrange(data.m)) )
        self.z2Expr = quicksum( data.f[i] * self.y[i]
                                for i in xrange(data.n) )
        # constraints
        print util.TS() + '\tcreating constraints'
        for j in xrange(data.m):
            self.model.addConstr( quicksum(self.x[i, j]
                                           for i in xrange(data.n)) == 1,
                                  name='coverage_' + str(j) )
        for i in xrange(data.n):
            for j in xrange(data.m):
                self.model.addConstr( self.x[i, j] <=  self.y[i],
                                      name='link_' + str(i) + '_' + str(j) )
        # stuff used in the bi-objective LB calculation
        self.wsEpsilon = 1e-4
        self.model.update()
        self.setSolverParameters()
        print util.TS() + '\tconstruction of the model is done'

    def setSolverParameters(self):
        self.model.setParam('Threads', 1)
        self.model.setParam('OptimalityTol', GurobiOptimalityTolerance)
        self.model.setParam('FeasibilityTol', GurobiFeasibilityTolerance)
        self.model.setParam('IntFeasTol', GurobiIntFeasTol)
        self.model.setParam('NumericFocus', GurobiNumericFocus)
        self.model.setParam('Outputflag', 0)

    def optimize(self):
        self.model.optimize()        

class SSUFLPSolution(integersolution.IntegerSolution):
    digits=5
