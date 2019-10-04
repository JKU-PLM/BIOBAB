import argparse

from biobab import params

def parse():
    parser = argparse.ArgumentParser()
    # tuples contain short flag, long flag, description and data type for that
    # argument
    parser.add_argument('-v', '--verbosity',
                        help='verbosity level', type=int, default=1,
                        dest='verbosity')
    parser.add_argument('-i', '--input-file', help='input file',
                        dest='inputFile')
    parser.add_argument('-o', '--output-file-prefix', help='output file',
                        dest='outputFilePrefix',
                        default='')
    parser.add_argument('-tl', '--time-limit',
                        dest='timeLimit',
                        help='CPU time limit', type=float, default=None)
    parser.add_argument('-ml', '--memory-limit',
                        dest='memoryLimit',
                        help='RAM limit', type=str, default=None)
    parser.add_argument('-a', '--algorithm',
                        help='bi-objective optimisation algorithm',
                        choices=['biobab', 'epsilon', 'root',
                                 'balancedbox', 'bdepsilon'],
                        default='biobab' )
    parser.add_argument('-lm', '--lexmin-method',
                        help='lexmin calculation method (BIOBAB & epsilon-constraint)',
                        dest='lexminMethod',
                        choices=['lex', 'ws'], default='lex' )
    parser.add_argument('-pt', '--problem-type',
                        help='problem type',
                        dest='problemType',
                        default='ap' )
    parser.add_argument('-efo', '--epsilon-first-objective',
                        dest='epsilonFirstObjective',
                        help='first objective to optimise (epsilon-constraint)',
                        type=int, choices=[1, 2], default=1)
    parser.add_argument('-s', '--strategy',
                        help='tree exploration strategy (BIOBAB & balanced box)',
                        choices=['depth', 'breadth', 'best'], default='breadth')
    parser.add_argument('-bbb', '--balancedbox-beta',
                        dest='balancedBoxBeta',
                        help='beta ratio for solution harvesting (balanced box)',
                        type=float, default=.15)
    parser.add_argument('-lr', '--linear-relaxation',
                        dest='useLinearRelaxation',
                        help='use linear relaxation for LB set (BIOBAB)',
                        action='store_true')
    parser.add_argument('-nlr', '--no-linear-relaxation',
                        dest='useLinearRelaxation',
                        help='use linear relaxation for LB set (BIOBAB)',
                        action='store_false')
    parser.add_argument('-id', '--integer-dominance',
                        dest='integerDominance',
                        help='activate integer dominance (BIOBAB)',
                        action='store_true')
    parser.add_argument('-nid', '--no-integer-dominance',
                        dest='integerDominance',
                        help='deactivate integer dominance (BIOBAB)',
                        action='store_false')
    parser.add_argument('-st', '--segment-tightening',
                        dest='segmentTightening',
                        help='activate segment tightening (BIOBAB)',
                        action='store_true')
    parser.add_argument('-nst', '--no-segment-tightening',
                        dest='segmentTightening',
                        help='deactivate segment tightening (BIOBAB)',
                        action='store_false')
    parser.add_argument('-ll', '--lb-lifting',
                        dest='lbLifting',
                        help='activate LB set lifting (BIOBAB)',
                        action='store_true')
    parser.add_argument('-nll', '--no-lb-lifting',
                        dest='lbLifting',
                        help='deactivate LB set lifting (BIOBAB)',
                        action='store_false')
    parser.add_argument('-osb', '--objective-space-branching',
                        dest='objectiveSpaceBranching',
                        help='activate objective space branching (BIOBAB)',
                        action='store_true')
    parser.add_argument('-nosb', '--no-objective-space-branching',
                        dest='objectiveSpaceBranching',
                        help='deactivate objective space branching (BIOBAB)',
                        action='store_false')
    parser.add_argument('-br', '--bound-right',
                        help='initial bound: right (BIOBAB)',
                        dest='boundRight',
                        type=float, default=None)
    parser.add_argument('-bt', '--bound-top',
                        help='initial bound: top (BIOBAB)',
                        dest='boundTop',
                        type=float, default=None)
    parser.add_argument('-d', '--debug', help='activate debug mode',
                        action='store_true')
    parser.add_argument('-mc', '--mip-cutoff',
                        dest='mipCutoff',
                        help='activate MIP cutoff with found integer solutions',
                        action='store_true')
    parser.add_argument('-nmc', '--no-mip-cutoff',
                        dest='mipCutoff',
                        help='deactivate MIP cutoff',
                        action='store_false')
    # now we get defaults from params.py
    defaults = [ x for x in dir(params) if not x.startswith('__') ]
    for i in defaults:
        try:
            exec('parser.set_defaults(' + i + '=params.' + i + ')')
        except Exception as e:
            print 'Error while reading default parameters:', e
            sys.exit(9)
    
    args = parser.parse_args()
    return args

def setParams(args):
    paramsAndValues = vars(args)
    for key, value in paramsAndValues.iteritems():
        t = 'params.' + key + ' = ' + repr(value)
        # print t
        try:
            exec(t)
        except Exception as e:
             # doesn't work with classes but if a class is set in params.py
             # it should not be changed anyway
             pass
            #print 'Error while setting parameter', key, ':', e
    # if a memory limit is requested, set it
    if not params.memoryLimit is None:
        import resource
        limit = humanToBytes(params.memoryLimit)
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            
# convert memory size in human format to bytes
# size is given as a string
def humanToBytes(size):
    units = { 'K': 1024,
              'M': 1024 ** 2,
              'G': 1024 ** 3,
              'T': 1024 ** 4,
    }
    if size[-1].isdigit():
        return int(size)
    else:
        return int(size[:-1]) * units[size[-1].upper()]
