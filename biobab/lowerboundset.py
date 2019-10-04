import params
import segment

class LowerBoundSet:
    def __init__(self, segments):
        self.segments = segments

    def right(self):
        return self.segments[-1].right

    def top(self):
        return self.segments[0].top

    # compute metaData based on segments in the LB set
    def computeMetaData(self):
        self.metaDataForPoint = {}
        for s in self.segments:
            self.metaDataForPoint[s.p1] = s.metaData1
            self.metaDataForPoint[s.p2] = s.metaData2
        self.metaData = lambda: self.metaDataForPoint.itervalues()
    
    # filter this LB set with an UB set
    def filter(self, ubSet):
        for u in ubSet.solutions:
            self.filterPoint(u)

    # filter this LB set with an UB point
    def filterPoint(self, solution):
        newSegments = []
        for s in self.segments:
            tmp = s.filter(solution)
            newSegments += tmp
        self.segments = newSegments

    def __repr__(self):
        if self.segments == []:
            return ''
        return str(reduce(lambda x, y: str(x) + '\n' + str(y),
                          self.segments))

    def vizOut(self, colour='lbColour'):
        result = 'LBDFront( [ '
        for s in self.segments:
            result += s.vizOut(colour) + ', '
        result += ' ], colour=' + colour + ')'
        return result
    
    def storePoints(self, fName):
        f = file(fName, 'w')
        for s in self.segments:
            f.write(str(s.p1[0]) + '\t' + str(s.p1[1]) + '\n')
        if len(self.segments) > 0:
            f.write( str(self.segments[-1].p2[0]) + '\t' + \
                         str(self.segments[-1].p2[1])  + '\n' )
        f.close()
        print 'Stored LB set to', fName

    # returns right- and top-bounds for discontinuous regions of this LB set
    def discontinuousRegions(self):
        if len(self.segments) == 0:
            return []
        regions = []
        top = self.segments[0].top
        i = 0
        while i < len(self.segments) - 1:
            if (self.segments[i+1].p1[0] - self.segments[i].p2[0] \
                >= params.lbMaxGap or \
                self.segments[i+1].p1[1] - self.segments[i].p2[1] \
                >= params.lbMaxGap) and (self.segments[i+1].top !=
                                         self.segments[i].top):
                regions.append( (self.segments[i].p2[0], top) )
                top = self.segments[i+1].top
            i += 1
        # let's not forget the last region
        # regions.append( (self.segments[-1].p2[0], top) )
        regions.append( (self.segments[-1].right, top) )
        return regions

    # produce metadata, i.e. various values taken by each variable for this
    # LB set (useful for branching)
    def getVarValues(self):
        try:
            self.metaData
        except AttributeError:
            self.computeMetaData()
        try:
            self.varValues
        except AttributeError:
            self.varValues = {}
            for s in self.metaData():
                for x, v in s.data:
                    if x in self.varValues:
                        self.varValues[x].append(v)
                    else:
                        self.varValues[x] = [ v ]
            if params.verbosity > 4:
                for x in self.varValues:
                    print x, self.varValues[x]
                print
        return self.varValues
    
    def isLeaf(self):
        return len(self.segments) == 0 or \
        (len(self.segments) == 1 and \
             self.segments[0].p1 == self.segments[0].p2) and\
             self.segments[0].metaData1.isInteger

    # split the LB set into disjoint LB sets
    # missing lexicographic points are recalculated using provided Node object
    def split(self, node, ubSet):
        epsilon = 1e-8
        regions = self.discontinuousRegions()
        if len(regions) == 1:
            return [ self ]
        else:
            result = []
            self.computeMetaData()
            for r in regions:
                points = set()
                metaDataForPoint = {}
                for s in self.segments:
                    if s.p1[0] <= r[0] + epsilon and s.p1[1] <= r[1] + epsilon:
                        points.add(s.p1)
                        metaDataForPoint[s.p1] = self.metaDataForPoint[s.p1]
                    if s.p2[0] <= r[0] + epsilon and s.p2[1] <= r[1] + epsilon:
                        points.add(s.p2)
                        metaDataForPoint[s.p2] = self.metaDataForPoint[s.p2]
                points = sorted([ p for p in points ])
                segments = [ segment.Segment(p1, p2,
                                             p2[0], r[1],
                                             metaDataForPoint[p1],
                                             metaDataForPoint[p2])
                             for p1, p2 in zip(points[:-1], points[1:]) ]
                segments[-1].right = r[0]
                lb = LowerBoundSet(segments)
                lb.metaDataForPoint = metaDataForPoint
                lb.metaData = lambda: metaDataForPoint.itervalues()
                result.append(lb)
            return result
                
class LBMetaData:
    def __init__(self, lp):
        self.data = lp.getDataOnIntegers()
        self.isInteger = lp.integerSolution()

    def __repr__(self):
        return str(self.data)
