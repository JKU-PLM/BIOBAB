from gurobipy import *

import basiclp
import integersolution
import util

import uboflpinstance

# MIPGap for Gurobi (min, max = 0, +inf)
GurobiMIPGap = 1e-8
GurobiOptimalityTolerance = 1e-8
# feasibility tolerance for Gurobi (min, max = 1e-9, 1e-2)
GurobiFeasibilityTolerance = 1e-6
GurobiIntFeasTol = GurobiFeasibilityTolerance
# Gurobi numeric focus (0, 1, 2 or 3)
GurobiNumericFocus = 3

basiclp.integralityEpsilon = 1e-8

class UBOFLPModel(basiclp.BasicLP):
    def __init__(self, data, relaxed=False):
        self.model = Model('Bi-objective stochastic facility location problem')
        self.model._parent = self
        self.data = data
        # decision variables
        # fraction of the population at i assigned to j
        print(util.TS() + '\tcreating y variables')
        self.y = {}
        for i in range(data.nPoints):
            for j in range(data.nPoints):
                for k in range(data.nSamples):
                    self.y[i,j,k] = \
                    self.model.addVar( vtype=GRB.CONTINUOUS,
                                       name='y_' + str(i) + \
                                       ',' + str(j) + \
                                       ',' + str(k),
                                       ub=1 if data.d[i,j] <= data.dmax1 else 0)
        # 1 if facility is built, 0 otherwise
        print(util.TS() + '\tcreating z variables')
        self.z = [ self.model.addVar(
                vtype=GRB.CONTINUOUS if relaxed else GRB.BINARY,
                lb=0.0, ub=1.0,
                name='z_' + str(i) )
                   for i in range(data.nPoints) ]
        self.integerVars = self.z
        # demand covered by facility j in sample k
        print(util.TS() + '\tcreating u variables')
        self.u = {}
        for j in range(data.nPoints):
            for k in range(data.nSamples):
                self.u[j,k] = self.model.addVar( vtype=GRB.CONTINUOUS,
                                                 name='u_' + str(j) + \
                                                     ',' + str(k) )
        print(util.TS() + '\tupdating model')
        self.model.update()
        # objective functions
        print(util.TS() + '\tcreating objective expressions')
        self.cost = LinExpr( [ c * 1.0 for c in data.c ], self.z )
        self.coverage = LinExpr( [ 1.0  / data.nSamples
                                   for i in self.u ],
                                 list(self.u.values()) )
        # constraints
        # link demand covered and actual demand
        print(util.TS() + '\tcreating constraints: link demand')
        for j in range(data.nPoints):
            for k in range(data.nSamples):
                self.model.addConstr( \
                    self.u[j,k] <= quicksum( self.y[i,j,k] * \
                                             data.w[i] * data.xi[i,k]
                                             for i in range(data.nPoints) ) )
        # only go to a facility if it is open
        print(util.TS() + '\tcreating constraints: y < z')
        for i in range(data.nPoints):
            for j in range(data.nPoints):
                for k in range(data.nSamples):
                    self.model.addConstr( self.y[i,j,k] <= self.z[j] )
        # don't cover demand more than once
        print(util.TS() + '\tcreating constraints: covered at most once')
        for i in range(data.nPoints):
            for k in range(data.nSamples):
                self.model.addConstr( quicksum( self.y[i,j,k]
                                                for j in range(data.nPoints)) \
                                      <= 1 )
        print(util.TS() + '\tsetting various parameters')
        # stuff used in the bi-objective LB calculation
        self.wsEpsilon = 1e-5
        self.model.update()
        self.setSolverParameters()
        # must be defined in order to benefit from methods inherited
        # from BasicLP
        self.z1Expr = self.cost
        self.z2Expr = data.coverageBound - self.coverage
        print(util.TS() + '\tconstruction of the model is done')

    def setSolverParameters(self):
        self.model.setParam('Threads', 1)
        self.model.setParam('MIPGap', GurobiMIPGap)
        self.model.setParam('FeasibilityTol', GurobiFeasibilityTolerance)
        self.model.setParam('IntFeasTol', GurobiIntFeasTol)
        self.model.setParam('NumericFocus', GurobiNumericFocus)
        self.model.setParam('Outputflag', 0)

