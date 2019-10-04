#!/usr/bin/env python

import sys
import string
import time

from biobab import biobabnode, upperboundset, treesearch
from biobab import epsilonconstraintframework
from biobab import balancedboxmethod
from biobab import util, params

import cliparser

def main():
    args = cliparser.parse()
    cliparser.setParams(args)
    # could be replaced, e.g. by a class that uses heuristics
    nodeClass = biobabnode.Node
    if params.outputFilePrefix == '':
        params.outputFilePrefix = params.algorithm
    #
    util.loadProblemClasses(params.problemType)
    #
    try:
        d = params.instanceClass(params.inputFile)
    except IOError:
        print 'Error: cannot read file', params.inputFile
        sys.exit(0)
    params.inputData = d
    print util.TS() + '\t' + 'read data'
    util.ticksAtStart = time.clock()
    # construct model
    relaxed = params.useLinearRelaxation
    m = params.modelClass(d, relaxed=relaxed)
    params.model = m
    print util.TS() + '\t' + 'constructed model'
    # initial valid objective bounds
    boundRight = params.boundRight or m.validBoundRight
    boundTop = params.boundTop or m.validBoundTop
    # upper bound set where we store search results
    ub = upperboundset.UpperBoundSet()
    # store results when we exit, whenever that is
    # ub.storePoints(ubPointsFile)
    import atexit
    atexit.register(ub.storePoints, params.outputFilePrefix + '-ub.txt')
    atexit.register(ub.storeSolutions, params.outputFilePrefix)
    #
    util.dumpParams()
    print util.TS() + '\tstarting optimisation'
    # algorithm-dependent section
    if params.algorithm == 'biobab':
        # construct and run biobab
        rootNode = nodeClass(m, right=boundRight, top=boundTop)
        ts = treesearch.TreeSearch(params.strategy, nodeClass=nodeClass)
        ts.search(rootNode, ub)
    elif params.algorithm == 'epsilon':
        params.integerDominance = False
        params.objectiveSpaceBranching = False
        e = epsilonconstraintframework.EpsilonConstraintFramework(relaxed)
        e.solve(m, ub, params.epsilonFirstObjective)
    elif params.algorithm == 'bdepsilon':
        params.integerDominance = False
        params.objectiveSpaceBranching = False
        e = epsilonconstraintframework.BDEpsilonConstraintFramework(relaxed)
        e.solve(m, ub, params.epsilonFirstObjective)
    elif params.algorithm == 'balancedbox':
        params.integerDominance = False
        params.objectiveSpaceBranching = False
        b = balancedboxmethod.BalancedBoxMethod(relaxed, params.strategy)
        b.search(m, ub)
    elif params.algorithm == 'root':
        rootNode = nodeClass(m, right=boundRight, top=boundTop)
        lb = rootNode.lowerBound(ub)
        print lb
        lb.storePoints(params.outputFilePrefix + '-lb.txt')
    else:
        print 'Error: unknown algorithm:', algorithm
        sys.exit(1)

    print 'Solved', params.modelClass.nLPs, 'LPs in total'
    print 'Solved', treesearch.TreeSearch.nNodes, 'nodes in total'
    
if __name__ == '__main__':
    main()
