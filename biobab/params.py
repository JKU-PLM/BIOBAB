# time limit for biobab or epsilon-constraint, in seconds
timeLimit = None
# self explanatory
debug = False
# how much verbosity we want during execution
verbosity = 1

# Parameters for BIOBAB
# tolerance used to determine if a point is on a given segment
# in LB set calculation
onSegmentTolerance = 1e-6
# improve dominance of LB by UB using the fact that feasible integer solutions
# have objective with integer values only
integerDominance = True #and False
# tighten LB segments using integrality of feasible integer solutions
segmentTightening = True
# lift LB using integrality of feasible integer solutions
lbLifting = True
# how big a gap between two LB segments can be before we consider that the LB
# set is discontinuous
# this is assuming integer values for feasible solutions in the original data
lbMaxGap = .02
# True if objective space branching is activated
objectiveSpaceBranching = True
# a value of 0 means biobab is running as an exact method
# higher values mean less precision in LB calculation:
# Let a and b two points during LB calculation, z their local nadir point;
# if a new point c is found between a and b, (a,c) and (c,b) are further
# processed in LB calculation iff the area of (a,b,c) is at least a certain
# ratio of the area of (a,b,z)
biobabLbRatio = 0#0.1
# ws or lex
lexminMethod = 'lex'
# do we use the linear relaxation when computing LB sets?
useLinearRelaxation = True

# generic parameter, used among others in singlesolver
feasibilityTolerance = 1e-6

# should we cutoff MIPs using previously found solutions?
mipCutoff = True
