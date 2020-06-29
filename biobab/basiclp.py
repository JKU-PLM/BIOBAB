import time

import integersolution
import upperboundset
import grbvalues
import params
import util

from gurobipy import *

integralityEpsilon = 1e-6
# true if value represents a fractional value for a binary variable
def isFractional(value):
    return value > integralityEpsilon and value < 1 - integralityEpsilon

# main callback wrapper
def callbackWrapper(model, where):
    for contexts, callback in model._parent.callbacks:
        if where in contexts:
            callback(model, where)

# callbacks always take two parameters, model and where
# this simple callback checks the CPU time limit
def checkTimeLimitCallback(model, where):
    if params.timeLimit and util.isTimeUp(raiseException=False):
        model.terminate()
        
class BasicLP:

    nLPs = 0
    lastSavedModel=0

    validBoundRight = util.infinity
    validBoundTop = util.infinity

    # list of pairs of the form: ( set([contexts]), callback )
    # then every time the main callback is called, it checks the context and
    # calls the callbacks accordingly
    callbacks = [ ( set([ GRB.Callback.MIPNODE ]), checkTimeLimitCallback) ]
    
    def showSol(self):
        for var in self.model.getVars():
            if var.getAttr(GRB.Attr.X) > 0:
                print(var.getAttr(GRB.Attr.VarName), var.getAttr(GRB.Attr.X))
                
    def exportModel(self, fName='debug'):
        self.model.update()
        BasicLP.lastSavedModel += 1        
        modelFileName = fName + ('-%04d' % BasicLP.lastSavedModel) + '.lp'
        self.model.write(modelFileName)
        print('Exported model to', modelFileName)
            
    def integerSolution(self):
        for z in self.integerVars:
            if isFractional( z.getAttr(GRB.Attr.X) ):
                return False
        return True
                                
    # pre-condition: the model has been solved
    def getDataOnIntegers(self):
        return [ ( z, z.getAttr(GRB.Attr.X) ) for z in self.integerVars ]

    # pre-condition: the model has been solved
    def getNonZeros(self):
        vars = {}
        for var in self.model.getVars():
            if var.getAttr(GRB.Attr.X) > 0:
                vars[var] = var.getAttr(GRB.Attr.X)
        return vars
        
    # get objective value of the current solution
    # pre-condition: the model has been solved
    def getObjectiveValue(self):
        return self.model.getObjective().getValue()

    # Add a constraint to the model
    # The added constraint is returned so that it can later be removed
    def addConstraint(self, constraint):
        return self.model.addConstr(constraint)

    # Remove a constraint from the model
    def removeConstraint(self, constraint):
        self.model.remove(constraint)

    # was a feasible solution found when last solving this model?
    def optimumFound(self):
        return self.model.getAttr('status') == GRB.OPTIMAL

    def updateBounds(self, right, top):
        # do we need to update the model at the end?
        atLeastOne = False
        # do we need a right bound?
        if right < util.infinity:
            try:
                self.z1Bound.setAttr('RHS', right)
            except Exception:
                self.z1Bound = self.model.addConstr( self.z1Expr <= right,
                                                     name='boundRight' )
                atLeastOne = True
        else: # if not...
            try:
                atLeastOne = True
                self.model.remove(self.z1Bound)
            except Exception as e:
                pass
        # now do we need a top bound?
        if top < util.infinity:
            try:
                self.z2Bound.setAttr('RHS', top)
            except Exception:
                self.z2Bound = self.model.addConstr( self.z2Expr <= top,
                                                     name='boundTop' )
                atLeastOne = True
        else:
            try:
                atLeastOne = True
                self.model.remove(self.z2Bound)
            except Exception as e:
                pass
        # update model if necessary
        if atLeastOne:
            self.model.update()

    def feasibleSolution(self, sol):
        # check if non-zeros are allowed
        for var, value in sol.vars.items():
            if value > var.getAttr(GRB.Attr.UB):
                return False
        # check if variables that should be non-zeros actually are non-zero
        for var in self.integerVars:
            if var.getAttr(GRB.Attr.LB) > 0:
                if (not var in sol.vars) or \
                   sol.vars[var] < var.getAttr(GRB.Attr.LB):
                    return False
        return True
    
    def solveWeightedSum(self, w1, w2, right, top, upperBound):
        if params.verbosity > 2:
            print('*** optimising weighted sum:', w1, w2, '\t|\tz1 <=', \
                right, '\t|\tz2 <=', top)
        # update bounds
        self.updateBounds(right, top)
        # update objective function
        self.model.setObjective(w1 * self.z1Expr + w2 * self.z2Expr,
                                GRB.MINIMIZE)
        self.model.update()
        #
        # help the MIP solver in case we're solving a MIP:
        # use best known upper bound
        if params.mipCutoff:
            cutoff = GRB.INFINITY
            if len(upperBound.solutions) > 0:
                for u in upperBound.solutions:
                    if u.z1 <= right and u.z2 <= top and \
                       u.z1 * w1 + u.z2 * w2 < cutoff:
                        # it is a good candidate for cutoff, let's make sure it
                        # respects all current branching decisions
                        if self.feasibleSolution(u):
                            cutoff = u.z1 * w1 + u.z2 * w2
                            cutoffPoint = (u.z1, u.z2)
            self.model.params.Cutoff = cutoff - 1e-7
        # solve it ffs
        self.optimize()
        if params.mipCutoff:
            self.model.params.Cutoff = GRB.INFINITY
        # Gurobi doesn't count the root node
        self.__class__.nLPs += 1 + int(self.model.getAttr('NodeCount'))
        # check if time limit was reached
        if params.timeLimit:
            util.isTimeUp(self.model)
        if params.debug:
            self.exportModel(params.outputFilePrefix + '-debug')
        # return newly found point
        if self.model.getAttr('status') == GRB.OPTIMAL:
            if params.verbosity > 3:
                print(self.getNonZeros())
            if params.verbosity > 2:
                print('\tobjective values:', self.z1(), self.z2())
                print('\tweighted sum:', self.getObjectiveValue())
            # if it is integer, update upperBound with it
            if self.integerSolution():
                newSol = params.solutionClass(self)
                upperBound.updateWithSolution(newSol)
            else:
                try:
                    # stop right here if there doesn't exist a heuristic for
                    # this problem
                    params.solutionClass.integerHeuristic
                    # otherwise make integer solutions out of this
                    # fractional solution
                    newSol = params.solutionClass(self)
                    harvest = newSol.integerHeuristic(self)
                    for newHeuristicSolution in harvest:
                        upperBound.updateWithSolution(newHeuristicSolution)
                except Exception as e:
                    pass
            if w1 == 0:
                return self.z1(), self.getObjectiveValue() / w2
            elif w2 == 0:
                return self.getObjectiveValue() / w1, self.z2()
            else:
                return self.z1(), self.z2()
        elif params.mipCutoff and self.model.getAttr('status') == GRB.CUTOFF:
            if params.verbosity > 2:
                print('\tcutoff point', cutoffPoint, 'is optimal')
            return cutoffPoint
        else:
            if self.model.getAttr('status') != GRB.INFEASIBLE and \
               self.model.getAttr('status') != GRB.INF_OR_UNBD:
                print('Unexpected status:', end=' ')
                print(grbvalues.status[self.model.getAttr('status')])
                self.exportModel('unexpected')
            return None

    # wrapper for calling gurobi to solve the current model ; important to
    # encapsulate it so that callbacks are easily added
    # (by overloading this method)
    def optimize(self):
        self.model.optimize(callbackWrapper)

    def z1(self):
        return self.z1Expr.getValue()
    
    def z2(self):
        return self.z2Expr.getValue()

    # lexicographic min with specified objective as first objective
    def lexmin(self, objective, boundRight, boundTop, upperBound):
        if params.lexminMethod == 'lex':
            return self.lexminLexicographic(objective, boundRight, boundTop,
                                            upperBound)
        elif params.lexminMethod == 'ws':
            return self.lexminWeightedSum(objective, boundRight, boundTop,
                                          upperBound)
        else:
            print('Error: unknow method for lexmin:', params.lexminMethod)
            sys.exit(22)

    # lexmin computed using a weighted sum
    def lexminWeightedSum(self, objective, boundRight, boundTop, upperBound):
        if objective == 1:
            w1, w2 = 1, self.wsEpsilon
        else:
            w1, w2 = self.wsEpsilon, 1
        return self.solveWeightedSum(w1, w2,
                                     boundRight, boundTop, upperBound)

    # lexmin computed optimising objectives one after the other
    def lexminLexicographic(self, objective, boundRight, boundTop, upperBound):
        if objective == 1:
            w1, w2 = 1, 0
        else:
            w1, w2 = 0, 1
        eTmp = self.solveWeightedSum(w1, w2, boundRight, boundTop, upperBound)
        if eTmp is None:
            return None
        if objective == 1:
            right, top = eTmp[0], self.data.boundTop()
        else:
            right, top = self.data.boundRight(), eTmp[1]
        return self.solveWeightedSum(w2, w1, right, top, upperBound)

    # objective values of each solution in the solution pool
    def getSolutionPoolVectors(self):
        nSolutions = self.model.getAttr('SolCount')
        ub = upperboundset.UpperBoundSet()
        for n in range(nSolutions):
            z1, z2 = 0, 0
            variables = {}
            self.model.params.solutionNumber = n
            for var in self.model.getVars():
                if var.getAttr(GRB.Attr.Xn) > 0:
                    variables[var] = var.getAttr(GRB.Attr.Xn)
            for i in range(self.z1Expr.size()):
                z1 += self.z1Expr.getCoeff(i) * \
                      self.z1Expr.getVar(i).getAttr(GRB.Attr.Xn)
            for i in range(self.z2Expr.size()):
                z2 += self.z2Expr.getCoeff(i) * \
                      self.z2Expr.getVar(i).getAttr(GRB.Attr.Xn)
            ub.updateWithSolution(params.solutionClass(z1=z1, z2=z2,
                                                       variables=variables))
        #
        return ub

    # export instance to fit Charkhgard's format
    def exportToCharkhgard(self, fName='exported.lp'):
        # sanitise variable names
        def sanitise(v):
            return v.replace(',', '_').replace('^','_')
        # convert gurobi linear expresion to human readable string
        def exprToString(e):
            r = ''
            for i in range(e.size()):
                coeff, var = e.getCoeff(i), e.getVar(i)
                if coeff != 0:
                    if coeff > 0 and len(r) > 0:
                        r += ' +'
                    r += ' ' + str(coeff) + ' ' + var.getAttr('VarName')
                    if i % 50 == 49 and i +1 < e.size():
                        r += '\n '
            return sanitise(r)
        # fix file name if needed
        if fName[-3:] != '.lp':
            fName += '.lp'
        # craft the right model
        with open(fName, 'w') as f:
            f.write('Minimize\n')
            f.write(' obj: ' + exprToString(self.z1Expr) + '\n')
            f.write('Subject To\n')
            # first constraint: second objective
            f.write(' obj_2:\t' + exprToString(self.z2Expr) + '\t= 0\n')
            # regular constraints
            for c in self.model.getConstrs():
                f.write(' ' + c.getAttr('ConstrName') + ':\t')
                f.write(exprToString(self.model.getRow(c)))
                sense = c.getAttr('Sense')
                if sense != '=':
                    sense += '='
                f.write(' ' + sense + ' ' + str(c.getAttr('RHS')) + '\n')
            # variable bounds
            f.write('Bounds\n')
            binaries = []
            integers = []
            for v in self.model.getVars():
                f.write(' ' + str(v.getAttr('LB')))
                f.write(' <= ' + sanitise(v.getAttr('VarName')))
                f.write(' <= ' + str(v.getAttr('UB')) + '\n')
                vType = v.getAttr('VType')
                if vType == 'B':
                    binaries.append(v)
                elif vType == 'I':
                    integers.append(v)
            if binaries:
                f.write('Binaries\n')
                for i, v in enumerate(binaries):
                    f.write(' ' + sanitise(v.getAttr('VarName')))
                    if i % 50 == 49 and i +1 < len(binaries):
                        f.write('\n')
                f.write('\n')
            if integers:
                f.write('Integers\n')
                for v in integers:
                    f.write(' ' + sanitise(v.getAttr('VarName')))
                f.write('\n')
            f.write('End\n')
        print(util.TS() + '\t' + 'Converted instance to', fName)
