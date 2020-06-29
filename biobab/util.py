import random
import time
import fractions
import math
import sys
import types

import params
import grbvalues
from functools import reduce

# timestamp function
def TS():
    t = time.process_time()
    hours = int( t / 3600 )
    t -= hours * 3600
    minutes = int( t / 60 )
    t -= minutes * 60
    result = '%02d' % hours + ':%02d' % minutes + ':%05.2f'% t
    return result
    
# GCD on a list
def listGCD(l):
    return reduce(lambda x, y: fractions.gcd(x, y), l)

epsilon = 1e-5

# is this number fractional?
def isFractional(x):
    return x > math.floor(x) + epsilon and x < math.ceil(x) - epsilon

def listAvg(l):
    return float(sum(l)) / len(l)

def roulette(values):
    total = sum(values)
    target = random.randint(0, total)
    currentTotal = 0
    index = 0
    while currentTotal < target:
        currentTotal += values[index]
        index += 1
    return index

# true if the two values are similar given a certain tolerance
def similarValues(ub, opt, tolerance):
    if opt < tolerance:
        return math.fabs(ub - opt) <= tolerance
    else:
        return math.fabs( (ub - opt) / opt ) <=  tolerance
    

# true if two points are super close
def closeEnough(p1, p2):
    return similarValues(p1[0], p2[0], epsilon) and \
        similarValues(p1[1], p2[1], epsilon)
    return math.fabs(1 - (p1[0] / p2[0])) < epsilon and \
        math.fabs(1 - (p1[1] / p2[1])) < epsilon

# output a point for later visualisation using an external program
def vizOutPoint(point, colour):
    return 'DPoint( ' + str(point[0]) + ', ' + str(point[1]) + ', colour=' + \
                    colour + ')'

class TimeLimitReachedException(Exception):
    pass

def isTimeUp(grbModel=None, raiseException=True):
    if time.process_time() > ticksAtStart + params.timeLimit:
        if raiseException:
            raise TimeLimitReachedException( \
                    '/!\\ Time limit reached: ' + str(params.timeLimit) + 's' )
        else:
            return True
    else:
        return False

def remainingTime():
    isTimeUp()
    return ticksAtStart + params.timeLimit - time.process_time()

def dumpParams():
    print('------------------------------------------------------------------')
    print('Parameters:')
    for p in [x for x in dir(params) if not x.startswith('__') ]:
        try:
            print('\t', p, '=', eval('params.' + p))
        except Exception as e:
            print()
    print('------------------------------------------------------------------')

# high enough value
infinity = sys.maxsize#float('inf')#sys.maxint

def loadProblemClasses(problemName):
    # try from a single file first, then from multiple files
    if not loadProblemClassesFromSingleFile(problemName):
        loadProblemClassesFromMultipleFiles(problemName)

# try to load all data classes from separate files
# return True if successful, False otherwise
def loadProblemClassesFromMultipleFiles(problemName):
    import basicdata, basiclp, integersolution
    print('Attempting to load data classes from multiple files')
    try:
        instanceClassLoaded, modelClassLoaded = False, False
        instanceModule = __import__(problemName + 'instance')
        modelModule = __import__(problemName + 'model')
        for name in dir(instanceModule):
            item = instanceModule.__getattribute__(name)
            if type(item) is type and \
               issubclass(item, basicdata.BasicData):
                params.instanceClass = item
                print('instance class:', item)
        for name in dir(modelModule):
            item = modelModule.__getattribute__(name)
            if type(item) is type and \
               issubclass(item, basiclp.BasicLP):
                params.modelClass = item
                print('model class:', item)
        try:
            solutionModule = __import__(problemName + 'solution')
            for name in dir(solutionModule):
                item = solutionModule.__getattribute__(name)
                if type(item) is type and \
                   issubclass(item, integersolution.IntegerSolution):
                    params.solutionClass = item
                    print('solution class:', item)
        except ImportError:
            pass
        return instanceClassLoaded and modelClassLoaded
    except Exception as e:
        print(e)
        return False        

# try to load all data classes from a single file
# return True if successful, False otherwise
def loadProblemClassesFromSingleFile(problemName):
    import basicdata, basiclp, integersolution
    print('Attempting to load data classes from a single file')
    try:
        dataModule = __import__(problemName + 'data')
        instanceClassLoaded, modelClassLoaded = False, False
        print('Loading all data classes from', problemName + 'data.py')
        for name in dir(dataModule):
            item = dataModule.__getattribute__(name)
            if type(item) is type and \
               issubclass(item, basicdata.BasicData):
                params.instanceClass = item
                instanceClassLoaded = True
            elif type(item) is type and \
                 issubclass(item, basiclp.BasicLP):
                params.modelClass = item
                modelClassLoaded = True
            elif type(item) is type and \
                 issubclass(item, integersolution.IntegerSolution):
                params.solutionClass = item
        return instanceClassLoaded and modelClassLoaded
    except Exception as e:
        print('Failed to load data classes from single file:', e)
        return False
