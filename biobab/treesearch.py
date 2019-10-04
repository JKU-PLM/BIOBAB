import sys
import math

import flexiblequeue
import util
import params
import biobabnode

from gurobipy import *

zero = 1e-6

class Bounder:

    nSaved = 0
    
    def __init__(self):
        pass

    def bound(self, node, ub):
        lb =  node.lowerBound(ub)
        if params.debug:
            Bounder.nSaved += 1
            fName = 'bounds-' + '%05d' % Bounder.nSaved + '.py'
            f = open(fName, 'w')
            f.write('from bounds import *\n\n')
            f.write('originalLB = ' + lb.vizOut('lbColour') + '\n\n')
            f.write('UB = ' + ub.vizOut('ubColour') + '\n\n')
        if params.verbosity > 2:
            print 'LB before:', lb
        lb.filter(ub)
        if params.verbosity > 2:
            print 'LB after:', lb
        if params.debug:
            f.write('filteredLB = ' + lb.vizOut('newLbColour') + '\n\n')
            f.close()
            print 'Saved debug filtering information to', fName
        return lb

class Brancher:
    def branch(self, lb):
        if params.verbosity > 2:
            print 'trying to branch:', self.__class__
        return self.genBranches(lb)

    
class BinaryPriorityBrancher(Brancher):
    # generate two branches
    def genBranches(self, lb):
        # branch on lp variable
        bestVar = self.bestCandidate(lb.getVarValues())
        if bestVar is None:
            return []
        else:
            return [ GurobiBinaryBoundBranching( bestVar, GRB.Attr.UB, 0 ),
                     GurobiBinaryBoundBranching( bestVar, GRB.Attr.LB, 1 ) ]
        
    # branch on the binary variable with the highest score
    def bestCandidate(self, varValues):
        bestVar, bestScore = None, 0
        for var in varValues:
            if bestVar and \
               bestVar.getAttr('BranchPriority') > \
               var.getAttr('BranchPriority'):
                continue
            else:
                avg = util.listAvg(varValues[var])
                if avg <= zero or avg >= 1 - zero:
                    continue
                else:
                    score = self.score(var, varValues)
                    if score > bestScore or \
                       ( bestScore > 0 and score > 0 and \
                         var.getAttr('BranchPriority') > \
                         bestVar.getAttr('BranchPriority') ):
                        bestVar, bestScore = var, score
        return bestVar

    # abstract version: must be overloaded in subclasses
    # returns the score of a variable
    # the higher the score, the more likely it will be selected for branching
    def score(self, var, varValues):
        return 0

class ClosestToOneBinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        best = 0
        for value in varValues[var]:
            # fractional, we look at it
            if value < 1 - zero and value > best:
                best = value
        return best

class FurthestToOneBinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        best = 0
        for value in varValues[var]:
            # fractional, we look at it
            if value < 1 - zero and (best == 0 or value < best):
                best = 1 - value
        return best
                    
class OftenFractionalBinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        nTimesFractional = 0
        for value in varValues[var]:
            if util.isFractional(value):
                nTimesFractional += 1
        return nTimesFractional

class FractionalOnAverageBinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        avgDistanceToHalf = util.listAvg( [ math.fabs(x - .5)
                                            for x in varValues[var] ] )
        # we relate small values to high score
        return 1.0 / max(avgDistanceToHalf, zero)
    
class FractionalAverageBinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        avg = float(sum(varValues[var])) / len (varValues[var])
        distanceToHalf = math.fabs(avg - .5)
        # we relate small values to high score
        return 1.0 / max(distanceToHalf, zero)

class SABinaryPriorityBrancher(BinaryPriorityBrancher):
    def score(self, var, varValues):
        return var.getAttr('SAObjUp') - var.getAttr('SAObjLow')
    
class ObjectiveSpaceBrancher(Brancher):
    message = 'Objective space'
    # branch on objective space if LB set is not continuous
    def genBranches(self, lb):
        if params.objectiveSpaceBranching:
            regions = lb.discontinuousRegions()
            if len(regions) > 1:
                return [ ObjectiveSpaceBranching(region)
                         for region in regions ]
            else:
                return []

class LocalBrancher(Brancher):
    message = 'Local Branch'
    def branch(self, lb):
        tolerance = 1e-5
        fixedVars = []
        bestVar, bestVal = None, 0
        varValues = lb.getVarValues()
        for var in varValues:
            values = sorted(varValues[var])
            # var is always set to 1
            if math.fabs(values[0] - 1) <= tolerance:
                fixedVars.append(var)
            # var sometimes takes value 1
            elif math.fabs(values[-1] - 1) <= tolerance:
                bestVar = var
                bestVal = values[-1]
            elif bestVar is None:
                bestVar = var
                bestVal = values[-1]
        if len(fixedVars) == 0 or bestVar is None:
            return []
        else:
            return [ LocalBranching( sum(fixedVars) + bestVar <= \
                                     len(fixedVars) ),
                     LocalBranching( sum(fixedVars) + bestVar >= \
                                     1 + len(fixedVars) ) ]
            
class SimpleLocalBrancher(Brancher):
    message = 'Local Branch'
    def branch(self, lb):
        tolerance = 1e-5
        fixedVars = []
        varValues = lb.getVarValues()
        for var in varValues:
            values = sorted(varValues[var])
            # var is always set to 1
            if math.fabs(values[0] - 1) <= tolerance:
                fixedVars.append(var)
        if len(fixedVars) == 0:
            return []
        else:
            return [ LocalBranching( sum(fixedVars) <= len(fixedVars) - 1 ),
                     LocalBranching( sum(fixedVars) >= len(fixedVars) ) ]

class BranchingDecision:
    def __init__(self):
        pass

    def apply(self, node):
        pass

    def cancel(self, node):
        pass

    def __repr__(self):
        return self.description
    
class ObjectiveSpaceBranching(BranchingDecision):
    def __init__(self, bounds):
        self.bounds = bounds
        self.description = 'f1 <= ' + str(bounds[0]) + \
            ', f2 <= ' + str(bounds[1])

    def apply(self, node):
        right, top = self.bounds
        node.right, node.top = min(right, node.right), min(top, node.top)

    def cancel(self, node):
        # these branching decisions have no impact on the LP
        pass
    
class LPBranching(BranchingDecision):
    def __init__(self, branch):
        self.branch = branch
        tokens = str(branch).split()
        self.description = tokens[2][:-1] + ' ' + tokens[3] + ' ' + \
            tokens[4][:-1]
        
    def apply(self, node):
        self.constraint = node.lp.addConstraint(self.branch)
        
    def cancel(self, node):
        node.lp.removeConstraint(self.constraint)

class GurobiBinaryBoundBranching(BranchingDecision):
    def __init__(self, var, boundType, boundValue):
        self.var = var
        self.boundType = boundType
        self.boundValue = boundValue
        self.description = str(var.getAttr(GRB.Attr.VarName)) + \
                           (' >= ' if boundType == GRB.Attr.LB else ' <= ') + \
                           str(boundValue)
        
    def apply(self, node):
        self.previousValue = 1.0 if self.boundType == GRB.Attr.UB else 0.0
        self.var.setAttr(self.boundType, self.boundValue)
        
    def cancel(self, node):
        self.var.setAttr(self.boundType, self.previousValue)
        

class LocalBranching(LPBranching):
    def __init__(self, branch):
        self.branch = branch
        tokens = str(branch).split()
        self.description = 'sum(...) ' + tokens[-2] + ' ' + tokens[-1][:-1]
        
class TreeSearch:

    nNodes = 0
    
    def __init__(self, strategy='breadth', nodeClass=biobabnode.Node):
        self.strategy = strategy
        self.nodeClass = nodeClass
        if strategy == 'breadth':
            self.queue = flexiblequeue.Queue('fifo')
        elif strategy == 'depth':
            self.queue = flexiblequeue.Queue('lifo')
        elif strategy == 'best':
            self.queue = flexiblequeue.Queue('best')
        else:
            print 'Unknown queue type:', strategy
            sys.exit(8)

    # perform a tree search!
    def search(self, node, ub,
               branchers=[
                   ClosestToOneBinaryPriorityBrancher(),
                   OftenFractionalBinaryPriorityBrancher(),
                   FractionalOnAverageBinaryPriorityBrancher(),
                   FractionalAverageBinaryPriorityBrancher(),
               ],
               bounder=Bounder(),
               wrapped=False ):
        #
        def updateStatusIfNeeded():
            if self.__class__.nNodes % 50 == 0:
                print util.TS(), '\tBIOBAB:\t', len(self.queue),
                print 'nodes \t|UB|:',len(ub.solutions)
        #
        osbStats = []
        if not wrapped:
            print util.TS() + '\tstarting bi-objective branch-and-bound (' + \
                self.strategy + ')'
        self.queue.push(node)
        while not self.queue.empty():
            node = self.queue.pop()
            self.__class__.nNodes += 1
            if params.verbosity == 1 and not wrapped:
                updateStatusIfNeeded()
            elif params.verbosity > 1:
                prefix = len(node.branchingDecisions) * '+-'
                print util.TS() + '\t', prefix,
                print '[f1 <=', str(node.right), '| f2 <=', str(node.top) + ']',
                print node.branchingDecisions, \
                    '(' + str(len(self.queue)) + ' nodes, |UB| =', \
                    str(len(ub.solutions)) + ')'
            node.applyBranchingDecisions()
            try:
                lb = bounder.bound(node, ub)
            except util.TimeLimitReachedException as e:
                if not wrapped:
                    print e
                    return
                else:
                    raise e
            node.cancelBranchingDecisions()
            #
            if params.verbosity > 2:
                print
                print 'LB:', lb
                print
            #
            if not lb.isLeaf():
                if not params.objectiveSpaceBranching:
                    subLBs = [ lb ]
                else:
                    subLBs = lb.split(node, ub)
                    if len(subLBs) > 1:
                        osbStats.append((node.depth, len(subLBs)))
                for slb in subLBs:
                    for brancher in branchers:
                        branches = brancher.branch(slb)
                        if len(branches) > 0: 
                            for branch in branches:
                                self.queue.push(\
                                    self.nodeClass(node.lp,
                                                   min(node.right, slb.right()),
                                                   min(node.top, slb.top()),
                                                   node.branchingDecisions + \
                                                   [ branch ],
                                                   node.depth + 1 ) )
                            break
        if not wrapped:
            print util.TS() + '\tbi-objective branch-and-bound is over'
        if params.verbosity > 0 and not wrapped:
            print 'stats on OSB:', osbStats
