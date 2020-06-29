import util

class UpperBoundSet:
    def __init__(self):
        # keep solutions sorted according to first then second objective
        # every element in this list should have z1 and z2 as attributes
        self.solutions = []

    # update self.solutions with solution, checking for dominance and keeping it
    # a non-dominated set
    def updateWithSolution(self, solution):
        # special case: existing ub set is empty
        if len(self.solutions) == 0:
            self.solutions = [ solution ]
        # other special case: only one solution in the list
        elif len(self.solutions) == 1:
            if self.solutions[0].dominates(solution):
                pass
            elif solution.dominates(self.solutions[0]):
                self.solutions = [ solution ]
            else:
                self.solutions.append(solution)
                self.solutions.sort(key=lambda x: x.z1)
        # general case
        else:
            # step 1: binary search on first objective value
            # special subcases
            if solution.z1 <= self.solutions[0].z1:
                left, right = -1, 0
            elif solution.z1 == self.solutions[-1].z1:
                left, right = len(self.solutions) - 2, len(self.solutions) - 1
            elif solution.z1 > self.solutions[-1].z1:
                left, right = len(self.solutions) - 1, len(self.solutions)
            else:
                # do binary search here
                left, right = 0, len(self.solutions) - 1
                while right - left > 1:
                    middle = (left + right) // 2
                    if self.solutions[middle].z1 == solution.z1:
                        left, right = middle - 1, middle
                    elif self.solutions[middle].z1 < solution.z1:
                        left = middle
                    else:
                        right = middle
            # now check for dominance
            if self.solutions[left].dominates(solution) or \
                    (right < len(self.solutions) and \
                         self.solutions[right].dominates(solution) ):
                pass
            else:
                nDom = 0
                while right+nDom < len(self.solutions) and \
                        solution.dominates(self.solutions[right+nDom]):
                    nDom += 1
                self.solutions = self.solutions[:left+1] + \
                    [ solution ] + self.solutions[right+nDom:]
        

    def storePoints(self, fName):
        with open(fName, 'w') as f:
            for s in self.solutions:
                f.write(str(s.z1) + '\t' + str(s.z2) + '\n')
        print(util.TS(), '\tStored UB set to', fName, end=' ')
        print('(' + str(len(self.solutions)) + ' solutions)')
                
    def storeSolutions(self, baseName):
        for i, s in enumerate(self.solutions):
            s.storeSolution(baseName)
        print(util.TS(), '\tStored', len(self.solutions), end=' ')
        print('solutions with basename:', baseName)
        
    def __repr__(self):
        return str(self.solutions)

    # remove from this set the solutions dominated by solutions from ubSet
    def filterWith(self, ubSet):
        newSols = []
        for sol in self.solutions:
            good = True
            for s2 in ubSet.solutions:
                if s2.dominates(sol):
                    good = False
                    break
            if good:
                newSols.append(sol)
        self.solutions = newSols
    
    # special output for visualisation in another script
    def vizOut(self, colour='ubColour'):
        result = 'UBDFront( [ '
        for s in self.solutions:
            result += util.vizOutPoint( (s.z1, s.z2), colour ) + ', '
        result += ' ], colour=' + colour + ')'
        return result
