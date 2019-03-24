import numpy as np
import pylab as pyl
import sys

argvs = sys.argv
argc = len(argvs)

if(argc != 2):
    print 'Usage: python %s [filename].log' % argvs[0]
    quit()

orbit = np.loadtxt(argvs[1]+'.log')

ox = []
oy = []


for i in range(0, orbit.shape[0]):
    ox.append(orbit[i][0])
    oy.append(orbit[i][2])

pyl.plot(ox, oy)
pyl.title(argvs[1])
pyl.xlabel('x')
pyl.ylabel('y')
pyl.text(ox[0], oy[0], 'start', ha='center', va='bottom')
pyl.text(ox[-1], oy[-1], 'end', ha='center', va='bottom')
pyl.xlim(xmin=-1.0, xmax=1.0)
pyl.ylim(ymin=-1.0, ymax=1.0)
pyl.savefig(argvs[1]+'.png')
pyl.clf()
