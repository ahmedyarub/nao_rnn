# -*- coding:utf-8 -*-

import numpy as np
import sys
import re
import subprocess
import tempfile
import rnn_print_log
import rnn_plot_log
import pdb

def pca(data, dimension=2):
    averaging_data = np.array(data)
    for column in range(0, averaging_data.shape[1]):
        column_mean = np.mean(averaging_data[:, column])
        averaging_data[:, column] -= column_mean

    covariance_matrix = np.dot(averaging_data.T, averaging_data) / float(averaging_data.shape[0])
    eig_value, eig_vector = np.linalg.eig(covariance_matrix)
    eig_value  = np.real(eig_value[0:dimension])
    eig_vector = np.real(eig_vector[:, 0:dimension])
    pca_data = np.dot(averaging_data, eig_vector)

    return pca_data
    

def plot_pca_init(f, filename, epoch):
    params = rnn_print_log.read_parameter(f)
    target_num = int(params['target_num'])

    r = re.compile(r'^# epoch')
    if epoch == None:
        lines = rnn_print_log.tail_n(f, target_num + 1)
        init_value = []
        init_value_end_index = 0
        flag = 0
        for line in lines:
            if flag:
                init_value.append([])
                init_value_elems = line.split('\t')
                for elem in init_value_elems:
                    init_value[init_value_end_index].append(float(elem))
                init_value[init_value_end_index].remove(init_value_end_index)
                init_value_end_index += 1
            if r.match(line):
                flag = 1
    print init_value            
    pca_data = pca(init_value)
    print pca_data

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp
    for data in pca_data:
        print '%f\t%f\n\n' % (data[0], data[1])
    sys.stdout.flush()
    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    p.stdin.write('set nokey;')
    p.stdin.write('set key right top;')
    p.stdin.write("set title 'Type PCA_Init File=%s';" % filename)
    p.stdin.write("set xlabel 'x';")
    p.stdin.write("set ylabel 'y';")
    p.stdin.write('set pointsize 3;')
    p.stdin.write('set grid;')
    command =['plot ']
    for x in xrange(0, target_num):
        command.append("'%s' i %d u 1:2 w p t '%d'," % (tmp.name, x, x))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__

def plot_log(f, file, epoch):
    try:
        p = subprocess.Popen(['gnuplot --version'], stdout=subprocess.PIPE,
                             shell = True)
        version = p.communicate()[0].split()[1]
        if float(version) >= 4.2:
            multiplot=True
    except:
        pass
    line = f.readline()
    if re.compile(r'^# INIT FILE').match(line):
        plot_pca_init(f, file, epoch)
    else:
        rnn_plot_log.plot_unknown(f, file)

def main():
    epoch = None
    if str.isdigit(sys.argv[1]):
        epoch = int(sys.argv[1])
    for file in sys.argv[2:]:
        f = open(file, 'r')
        plot_log(f, file, epoch)
        f.close()

if __name__ == '__main__':
    main()
