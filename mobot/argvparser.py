import sys
import getopt

# Parses the input arguments and sets mode of operation
STANDALONE = False
CVMODE = 'alpha'

argv = sys.argv
try:
    # --help, --standalone, --mode: 'alpha' or 'beta'
    # h: help; s: standalone; m: either 'alpha' or 'beta'
    opts, args = getopt.getopt(argv[1:], 'hsm:', [])
except getopt.GetoptError:
    print 'usage: framework.py (-s (-m <mode>))'
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print 'usage: framework.py (-s (-m <mode>))'
    elif opt in ('-s', '--standalone'):
        STANDALONE = True
    elif opt in ('-m', '--mode'):
        if arg == 'alpha':
            print 'alpha chosen!'
            CVMODE = 'alpha'
        elif arg == 'beta':
            print 'beta chosen!'
            CVMODE = 'beta'
        else:
            print 'not a valid mode, default to alpha.'
            CVMODE = 'alpha'
    else:
        assert False, 'unhandled option.'


print STANDALONE
print CVMODE
