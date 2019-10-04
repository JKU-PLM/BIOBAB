import math

import util

validEpsilon = 0.9

class BasicData:
    # All these functions may be overloaded in derived classes to add
    # problem-specific pruning based on integrality of feasible integer
    # solutions
    # pre-condition: point corresponds to an integer solution
    z1Epsilon = 1
    z2Epsilon = 1
    def improveWithIntegrality(self, z1, z2):
        return z1 - validEpsilon * self.z1Epsilon, \
            z2 - validEpsilon *self.z2Epsilon

    def ceilCoords(self, z1, z2):
        return self.z1Epsilon * math.ceil(z1 / self.z1Epsilon), \
            self.z2Epsilon * math.ceil(z2 / self.z2Epsilon)
    
    def floorCoords(self, z1, z2):
        return self.z1Epsilon * math.floor(z1 / self.z1Epsilon), \
            self.z2Epsilon * math.floor(z2 / self.z2Epsilon)

    def roundCoords(self, z1, z2):
        return self.z1Epsilon * round(z1 / self.z1Epsilon), \
            self.z2Epsilon * round(z2 / self.z2Epsilon)

    def boundTop(self):
        return util.infinity

    def boundRight(self):
        return util.infinity    
