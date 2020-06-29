from gurobipy import *

import params

zero = 1e-5

class IntegerSolution:
    # significant digits after the dot
    digits = 5
    
    def __init__(self, lp=None, z1=None, z2=None, variables=None):
        if lp:
            # set objective values for this solution
            self.z1 = round(lp.z1(), self.digits) if z1 is None else z1
            self.z2 = round(lp.z2(), self.digits) if z2 is None else z2
            # collect variable information
            self.vars = lp.getNonZeros() if variables is None else variables
        else:
            self.z1, self.z2 = z1, z2
            self.vars = variables
        #
        self.setImprovedValues()

    def setImprovedValues(self):
        if params.integerDominance:
            self.improvedZ1, self.improvedZ2 = \
                params.inputData.improveWithIntegrality(self.z1, self.z2)
        else:
            self.improvedZ1, self.improvedZ2 = self.z1, self.z2
    
    def dominates(self, solution):
        if self.improvedZ1 > solution.z1:
            return False
        if self.improvedZ2 > solution.z2:
            return False
        return True
    
    def __repr__(self):
        return 'integer solution: (' + str(self.z1) + ',' + str(self.z2) + ')'

    def storeAsRaw(self, fName='solution', verbose=False):
        try:
            self.__class__.nSavedSolutions += 1
        except Exception as e:
            self.__class__.nSavedSolutions = 1
        fName += '-' + '%03d' % self.__class__.nSavedSolutions + '.raw'
        file = open(fName, 'w')
        for x in self.vars:
            if self.vars[x] > zero:
                file.write(x.getAttr(GRB.Attr.VarName) + '\t=\t' + \
                           str(self.vars[x]) + '\n')
        file.close()
        if verbose:
            print('stored solution to', fName)

    def storeSolution(self, fName='solution', verbose=False):
        self.storeAsRaw(fName, verbose)

# load it as default class for solutions
try:
    params.solutionClass
except Exception as e:
    params.solutionClass = IntegerSolution
