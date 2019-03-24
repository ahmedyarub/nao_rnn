# -*- coding utf-8 -*-
'''
NAME       : analysis_utils.py
AUTHOR     : Ryoichi Nakajo
LAST UPDATE: 2014/06/16
DESCRIPTION: tools for data analysis
'''
import numpy as np
from numpy import linalg

import sys
import tempfile
import subprocess
from optparse import OptionParser

def pca(data, 
        dim=2):
    """
    :type data: numpy.ndarray
    :param data: analyzing data

    :type dim: int
    :param dim: dimension of new analyzed data
                optional default = 2
    """
    center = np.mean(data, axis=0)
    centered_data = data - center

    cov = np.dot(centered_data.T, centered_data) / float(centered_data.shape[0])
    eig_value, eig_vector = linalg.eig(cov)
    eig_value_index = np.argsort(eig_value)[::-1]
    eig_vector = np.real(eig_vector[:,eig_value_index[0:dim]])

    return eig_vector, center

# 2014/06/16 commented out
"""
def ica(data,
        label):
#    :type data: numpy.ndarray
#    :param data: analyzing data
#
#    :type label: numpy.ndarray
#    :param label: labels for above data set
#
#    :type dim: int
#    :param dim: dimension of analyzed data
#                optional default = 2
    data_class = []
    for li in xrange(int(np.max(label)) + 1):
        each_data = data[np.where(label==li)]
        if not each_data.shape[0] == 0:
            data_class.append(each_data)
    axis_dimension = len(data_class) - 1

    class_size  = np.zeros((len(data_class),), dtype='int')
    within_mean = np.zeros((len(data_class),data.shape[1]))
    within_cov  = np.zeros((data.shape[1], data.shape[1]))
    between_mean = np.mean(data, axis=0)
    between_cov  = np.zeros((data.shape[1], data.shape[1]))
    for ci in xrange(len(data_class)):
        class_size[ci]  = int(data_class[ci].shape[0])
        within_mean[ci,:] = np.mean(data_class[ci], axis=0)

        within_centered_data = data_class[ci] - within_mean[ci]
        within_cov += np.dot(within_centered_data.T, within_centered_data)

        between_centered_mean = within_mean[ci,:] - between_mean
        between_cov += class_size[ci] * np.dot(between_centered_mean.T, 
                                               between_centered_mean)

    inv_within_cov = linalg.inv(within_cov)
    eig_value, eig_vector = linalg.eig(np.dot(inv_within_cov,
                                              between_cov))
    eig_value_index = np.argsort(eig_value)[::-1]
    eig_vector = np.real(eig_vector[:,0:axis_dimension])

    return eig_vector, between_mean
"""

def _generate_data_set_for_test(length):
    rng = np.random.RandomState(123)
    mid = int(length / 2)

    data = np.zeros((length, 2))
    data[0:mid,:] = rng.normal(loc  =(-4.0, -5.0),
                               scale=(2.0, 1.0),
                               size =(mid,2))
    data[mid:,:]  = rng.normal(loc  =(4.0, 5.0),
                               scale=(2.0, 1.0),
                               size =(mid,2))
    label = np.zeros((length,), dtype='int')
    label[mid:] = 1
    return data, label

def _plot_data_set_for_test(eig_vector,
                            center,
                            data,
                            label,
                            verbose=False):
    dir = eig_vector[1] / eig_vector[0]
    theta = np.tanh(dir)

    # axis
    x = np.arange(-10.0, 10.01, 0.01)
    y = np.tan(theta) * (x - center[0]) + center[1]

    projected_data = np.dot(data - center, eig_vector)
    prj_xy = np.zeros((data.shape[0], 2))
    prj_xy[:,0] = (projected_data * np.cos(theta) + center[0])[:,0]
    prj_xy[:,1] = (projected_data * np.sin(theta) + center[1])[:,0]

    if verbose:
        print '... show analyzed data set'
        print projected_data

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp

    for xy in data[np.where(label==0)]:
        print '%f\t%f\n' % (xy[0], xy[1])
    print '\n'

    for xy in data[np.where(label==1)]:
        print '%f\t%f\n' % (xy[0], xy[1])
    print '\n'

    for xy in prj_xy[np.where(label==0)]:
        print '%f\t%f\n' % (xy[0], xy[1])
    print '\n'

    for xy in prj_xy[np.where(label==1)]:
        print '%f\t%f\n' % (xy[0], xy[1])
    print '\n'

    for i in xrange(int(x.shape[0])):
        print '%f\t%f' % (x[i], y[i])
    print '\n'
    sys.stdout.flush()

    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    p.stdin.write('set terminal x11 0;')
    p.stdin.write('set terminal postscript enhanced color;')
    p.stdin.write('set output "test.eps";')
    p.stdin.write('set nokey;')
    p.stdin.write('set title "PCA";')
    p.stdin.write('set xlabel "x";')
    p.stdin.write('set ylabel "y";')
    p.stdin.write('set grid;')
    colors  = ['blue', 'orange', 'green', 'red']
    command = ['plot ']
    for x in xrange(0, len(colors)):
        command.append('"%s" index %d using 1:2 w p lc rgb "%s" pointtype %d,' 
                       % (tmp.name, x, colors[x], x%2+1))
    command.append('"%s" index 4 using 1:2 with lines lc rgb "black",' % (tmp.name))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('set terminal x11;')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__
    
def _pca_test(verbose=False):
    if verbose:
        print '... begin pca_test'

    data, label = _generate_data_set_for_test(100)

    if verbose:
        print '... show data set'
        print data

    v, c = pca(data, dim=1)
    if verbose:
        print '... show eigen vector'
        print v
        print '... show center of data set'
        print c

    _plot_data_set_for_test(v, c,
                            data, label,
                            verbose=verbose)
# 2014/06/16 commented out
"""
def _ica_test(verbose=False):
    if verbose:
        print '... begin ica_test'

    data, label = _generate_data_set_for_test(100)

    if verbose:
        print '... show data set'
        print data
        print '... show label of above data set '
        print label

    v, c = ica(data, label)
    if verbose:
        print '... show eigen vector'
        print v
        print '... show between mean of data set'
        print c

    _plot_data_set_for_test(v, c,
                            data, label,
                            verbose=verbose)
"""

def _get_parser():
    usage = '''python %prog [-piv]'''
    version = '''%prog 1.0
author     : Ryoichi Nakajo, Waseda University, Tokyo, Japan
last update: 2014/06/16'''

    parser = OptionParser(usage=usage, version=version)
    parser.add_option('-p', '--pca',
                      action='store_true', dest='pca',
                      help='run the test program of principle component analysis')
    # 2014/06/16 commented out
    #parser.add_option('-i', '--ica',
    #                  action='store_true', dest='ica',
    #                  help='run the test program of independent component analysis')
    parser.add_option('-v', '--verbose',
                      action='store_true', dest='verbose',
                      help='show the variables in each case')

    return parser

def main():
    parser = _get_parser()
    options, args = parser.parse_args()
    
    if options.pca and options.ica:
        parser.error("options -p (--pca) and -i (--ica) are mutually exclusive")
        sys.exit(-1)

    if options.pca:
        _pca_test(options.verbose)
    # 2014/06/16 commented out
    #elif options.ica:
    #    _ica_test(options.verbose)

if __name__ == '__main__':
    main()
