import numpy as np
import pylab as pyl

target = np.loadtxt("target.txt")

tx = []
ty = []


for i in range(0, target.shape[0]):
    tx.append(target[i][0])
    ty.append(target[i][1])

pyl.plot(tx, ty)
pyl.text(tx[0],ty[0], 'start', ha='center', va='top')
pyl.text(tx[-1], ty[-1], 'end', ha='center', va='top')
pyl.title('target')
pyl.xlabel('x')
pyl.ylabel('y')
pyl.xlim(xmin=-1.0, xmax=1.0)
pyl.ylim(ymin=-1.0, ymax=1.0)
pyl.savefig('target.png')
pyl.clf()

