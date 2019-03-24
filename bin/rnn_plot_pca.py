# -*- coding:utf-8 -*-
'''
NAME       : rnn_pca_init.py
AUTHOR     : Ryoichi Nakajo
LAST UPDATE: 2014/09/26
DESCRIPTION: This do principal component analysis the data of "STATE FILE," "INIT FILE" or
             orbit file generated from s-ctrnn and plotting them two or three dimension 
             surface. This program needs "analysis_utils.py," "rnn_print_log.py" 
             and "rnn_plot_log.py." "analysis_utils.py" is used for principal component 
             analysis. Then, "rnn_print_log.py" and "rnn_plot_log.py" are used to extract 
             data from log files.
'''
import sys
import re
import subprocess
import tempfile
import numpy as np
from optparse import OptionParser

import rnn_print_log
from analysis_utils import pca

window_number = 0

def data_extract_for_state(fp,
                           filename,
                           epoch,
                           layer_type):
    params = rnn_print_log.read_parameter(fp)
    r = re.compile(r'^# target')
    target_num = int(re.search('\d+', filename).group(0))
    target_length = int(params['target'][target_num])
    out_state_size = int(params['out_state_size'])

    if epoch == None:
        # get final epoch data
        lines = rnn_print_log.tail_n(fp, target_length+1, 1)
        values = []
        flag = False

        for line in lines:
            if flag:
                values.append([])
                value_elems = line.split('\t')[1:]
                if layer_type == 'OUTPUT_TYPE':
                    for elems in value_elems[1:out_state_size*3:3]:
                        values[-1].append(float(elems))
                elif layer_type == 'CONTEXT_TYPE':
                    for elems in value_elems[out_state_size*3:]:
                        values[-1].append(float(elems))
                else:
                    raise NotImplementedError
            if r.match(line):
                flag = True

    return values

def data_extract_for_init(fp,
                          epoch):
    params = rnn_print_log.read_parameter(fp)
    target_num = int(params['target_num'])

    rep_init_size = int(params['rep_init_size'])

    r = re.compile(r'^# epoch')
    if epoch == None:
        lines = rnn_print_log.tail_n(fp, target_num + 1)
        init_value = []
        flag = False

        for line in lines:
            if flag:
                init_value.append([])
                init_value_elems = line.split('\t')[1 + rep_init_size:]
                for elem in init_value_elems:
                    init_value[-1].append(float(elem))
            if r.match(line):
                flag = True
    #print init_value
    return init_value

def data_extract_for_orbit(fp):
    values = []
    
    for line in fp:
        values.append([])
        for elem in line.split('\t')[5:]:
            values[-1].append(float(elem))

    return values
    
def plot2d(data,
           filename,
           layer_type=None,
           tau=None,
           multi_color=False,
           plot_type='lines'):
    global window_number
    target_num = data.shape[0]

    title = 'Type PCA File=%s' % re.split('/', filename)[-1]
    if not layer_type is None:
        title = title + ' layer_type=%s' % layer_type
    if not tau is None:
        title = title + ' tau=%.2f' % tau

    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    #p.stdin.write('set nokey;')
    p.stdin.write('set title "%s";' % title)
    p.stdin.write('set xlabel "PC1";')
    p.stdin.write('set ylabel "PC2";')
    p.stdin.write('set grid;')

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp

    command = ['plot ']
    if multi_color:
        for d in data:
            print '%f\t%f\n\n' % (d[0], d[1])
        sys.stdout.flush()
        for x in xrange(0, target_num):
            command.append('"%s" index %d using 1:2 with point linetype %d pointsize 1,'
                           % (tmp.name, x, x+1))
    else:
        for d in data:
            print '%f\t%f' % (d[0], d[1])
        print '\n\n'
        print '%f\t%f\n\n' % (data[0][0], data[0][1])
        print '%f\t%f\n\n' % (data[-1][0], data[-1][1])
        sys.stdout.flush()
        command.append('"%s" index 0 using 1:2 with %s linetype %d,'
                       % (tmp.name, plot_type, window_number+1))
        command.append('"%s" index 1 using 1:2 with point linetype 1 pointsize 1,'
                       % (tmp.name))
        command.append('"%s" index 2 using 1:2 with point linetype 2 pointsize 1,'
                       % (tmp.name))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__
    window_number += 1

def plot3d(data,
           filename,
           layer_type=None,
           tau=None,
           multi_color=False,
           plot_type='lines'):
    global window_number
    target_num = data.shape[0]

    title = 'Type PCA File=%s' % re.split('/', filename)[-1]
    if not layer_type is None:
        title = title + ' layer_type=%s' % layer_type
    if not tau is None:
        title = title + ' tau=%.2f' % tau

    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    #p.stdin.write('set nokey;')
    p.stdin.write('set title "%s";' % (title))
    p.stdin.write('set xlabel "PC1";')
    p.stdin.write('set ylabel "PC2";')
    p.stdin.write('set zlabel "PC3";')
    p.stdin.write('set grid;')

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp

    command = ['splot ']
    if multi_color:
        for d in data:
            print '%f\t%f\t%f\n\n' % (d[0], d[1], d[2])
        sys.stdout.flush()

        for x in xrange(0, target_num):
            command.append('"%s" index %d using 1:2:3 with point linetype %d pointsize 1,'
                           % (tmp.name, x, x+1))
    else:
        for d in data: 
            print '%f\t%f\t%f' % (d[0], d[1], d[2])
        print '\n\n'
        print '%f\t%f\t%f\n\n' % (data[0][0], data[0][1], data[0][2])
        print '%f\t%f\t%f\n\n' % (data[-1][0], data[-1][1], data[-1][2])
        sys.stdout.flush()

        command.append('"%s" index 0 using 1:2:3 with %s linetype %d,'
                       % (tmp.name, plot_type, window_number+1))
        command.append('"%s" index 1 using 1:2:3 with point linetype 1 pointsize 1,'
                       % (tmp.name))
        command.append('"%s" index 2 using 1:2:3 with point linetype 2 pointsize 1,'
                       % (tmp.name))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__
    window_number += 1

def extract_file_info(filenames):
    # format of filename: <filename_type><number>.log
    filename_type = re.split('[/.\d]*', filenames[0])[-2]

    min_idx = int(re.split('[/.\D]*', filenames[0])[-2])
    max_idx = min_idx
    for filename in filenames:
        idx = int(re.split('[/.\D]*', filename)[-2])
        if idx < min_idx:
            min_idx = idx
        elif idx > max_idx:
            max_idx = idx

    return filename_type, [min_idx, max_idx]

def plot2d_one_window(data,
                      filename,
                      layer_type=None,
                      tau=None,
                      plot_type='lines'):
    title = 'Type PCA File=%s' % re.split('/', filename)[-1]
    if not layer_type is None:
        title = title + ' layer_type=%s' % layer_type
    if not tau is None:
        title = title + ' tau=%.2f' % tau

    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    p.stdin.write('set nokey;')
    p.stdin.write('set title "%s";' % (title))
    p.stdin.write('set xlabel "PC1";')
    p.stdin.write('set ylabel "PC2";')
    p.stdin.write('set grid;')

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp

    command = ['plot ']
    for i in range(0, data.shape[0]):
        for x, y in data[i]:
            print '%f\t%f' % (x, y)
        print '\n\n'
        print '%f\t%f\n\n' % (data[i][0][0], data[i][0][1])
        print '%f\t%f\n\n' % (data[i][-1][0], data[i][-1][1])
        sys.stdout.flush()

        command.append('"%s" index %d using 1:2 with %s linetype %d,'
                       % (tmp.name, i*3, plot_type, i+1))
        command.append('"%s" index %d using 1:2 with point linetype 1 pointsize 1,'
                       % (tmp.name, i*3+1))
        command.append('"%s" index %d using 1:2 with point linetype 2 pointsize 1,'
                       % (tmp.name, i*3+2))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__

def plot3d_one_window(data,
                      filename,
                      layer_type=None,
                      tau=None,
                      plot_type='lines'):
    title = 'Type PCA File=%s' % re.split('/', filename)[-1]
    if not layer_type is None:
        title = title + ' layer_type=%s' % layer_type
    if not tau is None:
        title = title + ' tau=%.2f' % tau

    p = subprocess.Popen(['gnuplot -persist'], stdin=subprocess.PIPE,
                         shell=True)
    p.stdin.write('set nokey;')
    p.stdin.write('set title "%s";' % (title))
    p.stdin.write('set xlabel "PC1";')
    p.stdin.write('set ylabel "PC2";')
    p.stdin.write('set zlabel "PC3";')
    p.stdin.write('set grid;')

    tmp = tempfile.NamedTemporaryFile()
    sys.stdout = tmp

    command = ['splot ']
    for i in range(0, data.shape[0]):
        for x, y, z in data[i]:
            print '%f\t%f\t%f' % (x, y, z)
        print '\n\n'
        print '%f\t%f\t%f\n\n' % (data[i][0][0], data[i][0][1], data[i][0][2])
        print '%f\t%f\t%f\n\n' % (data[i][-1][0], data[i][-1][1], data[i][-1][2])
        sys.stdout.flush()

        command.append('"%s" index %d using 1:2:3 with %s linetype %d,'
                       % (tmp.name, i*3, plot_type, i+1))
        command.append('"%s" index %d using 1:2:3 with point linetype 1 pointsize 1,'
                       % (tmp.name, i*3+1))
        command.append('"%s" index %d using 1:2:3 with point linetype 2 pointsize 1,'
                       % (tmp.name, i*3+2))
    p.stdin.write(''.join(command)[:-1])
    p.stdin.write('\n')
    p.stdin.write('exit\n')
    p.wait()
    sys.stdout = sys.__stdout__

def plot_pca_state(fp,
                   filename,
                   dimension,
                   epoch,
                   layer_type,
                   init_tau,
                   connection):
    plot_func = {2: plot2d,
                 3: plot3d}
    plot = (plot_func[dimension] if dimension in plot_func
            else plot3d)

    state_data = np.asarray(data_extract_for_state(fp, filename, epoch, layer_type))
    if layer_type == 'CONTEXT_TYPE' and len(init_tau) >= 1:
        for i in xrange(len(init_tau)):
            itr_begin, itr_end = connection[i]
            eig_vector, _ = pca(state_data[:, itr_begin:itr_end], dim=dimension)
            pca_data = np.dot(state_data[:, itr_begin:itr_end], eig_vector)
            plot(pca_data, filename, layer_type=layer_type, 
                 tau=init_tau[i], plot_type='lines')
    else:
        eig_vector, _ = pca(state_data, dim=dimension)
        pca_data = np.dot(state_data, eig_vector)
        plot(pca_data, filename, layer_type=layer_type, plot_type='lines')

def plot_pca_init(fp,
                  filename,
                  dimension,
                  epoch,
                  init_tau,
                  connection):
    plot_func = {2: plot2d,
                 3: plot3d}
    plot = (plot_func[dimension] if dimension in plot_func
            else plot3d)

    init_data = np.asarray(data_extract_for_init(fp, epoch))
    if len(init_tau) >= 1:
        for i in xrange(len(init_tau)):
            itr_begin, itr_end = connection[i]
            eig_vector, _ = pca(init_data[:, itr_begin:itr_end], dim=dimension)
            pca_data = np.dot(init_data[:, itr_begin:itr_end], eig_vector)
            plot(pca_data, filename, tau=init_tau[i], multi_color=True)
    else:
        eig_vector, _ = pca(init_data, dim=dimension)
        pca_data = np.dot(init_data, eig_vector)
        plot(pca_data, filename, multi_color=True)

def plot_pca_orbit(fp,
                   filename,
                   dimension):
    plot_func = {2: plot2d,
                 3: plot3d}
    plot = (plot_func[dimension] if dimension in plot_func
            else plot3d)
    orbit_data = data_extract_for_orbit(fp)
    pca_data, _ = pca(orbit_data, dim=dimension)
    plot(pca_data, filename, plot_type='point')

def plot_log(fp, 
             filename, 
             dimension, 
             epoch, 
             layer_type,
             init_tau,
             connection):
    assert(dimension == 2 or dimension == 3)

    multiplot=False
    try:
        p = subprocess.Popen(['gnuplot --version'], stdout=subprocess.PIPE,
                             shell=True)
        version = p.communicate()[0].split()[1]
        if float(version) >= 4.2:
            multiplot=True
    except:
        pass

    line = fp.readline()
    if re.compile(r'^# STATE FILE').match(line):
        plot_pca_state(fp, filename, dimension, epoch, layer_type,
                       init_tau, connection)
    elif re.compile(r'^# INIT FILE').match(line):
        plot_pca_init(fp, filename, dimension, epoch, init_tau, connection)
    else:
        plot_pca_orbit(fp, filename, dimension)


def plot_pca_all_state(filenames,
                       dimension,
                       epoch,
                       layer_type,
                       init_tau,
                       connection):
    assert(len(filenames) >= 1)
    assert(dimension == 2 or dimension == 3)

    multiplot=False
    try:
        p = subprocess.Popen(['gnuplot --version'], stdout=subprocess.PIPE,
                             shell=True)
        version = p.communicate()[0].split()[1]
        if float(version) >= 4.2:
            multiplot=True
    except:
        pass

    filename_type, ranges = extract_file_info(filenames)

    plot_func = {2: plot2d_one_window,
                 3: plot3d_one_window}
    plot = (plot_func[dimension] if dimension in plot_func
            else plot3d_one_window)

    list_state_data = []
    all_state_data = []
    for filename in filenames:
        fpr = open(filename, 'r')
        list_state_data.append(data_extract_for_state(fpr, filename, epoch, layer_type))
        for data in list_state_data[-1]:
            all_state_data.append(data)
        fpr.close()

    list_state_data = np.asarray(list_state_data, dtype=np.float32)
    all_state_data = np.asarray(all_state_data, dtype=np.float32)

    if layer_type == 'CONTEXT_TYPE' and len(init_tau) >= 1:
        for i in xrange(len(init_tau)):
            itr_begin, itr_end = connection[i]
            eig_vector, _ = pca(all_state_data[:, itr_begin:itr_end], dim=dimension)
            pca_data = []
            for j in range(0, len(filenames)):
                pca_data.append(np.dot(list_state_data[j][:, itr_begin:itr_end],
                                       eig_vector))
            pca_data = np.asarray(pca_data, dtype=np.float32)
            plot(pca_data, '%s%06d-%06d' % (filename_type, ranges[0], ranges[1]),
                 layer_type=layer_type, tau=init_tau[i], plot_type='lines')
    else:
        eig_vector, _ = pca(all_state_data, dim=dimension)
        pca_data = []
        for i in range(0, len(filenames)):
            pca_data.append(np.dot(list_state_data[i], eig_vector))
        pca_data = np.asarray(pca_data, dtype=np.float32)
        plot(pca_data, '%s%06d-%06d' % (filename_type, ranges[0], ranges[1]), 
             layer_type=layer_type, plot_type='lines')


def read_tau(fp):
    r = {'init_tau'    : re.compile(r'init_tau'),
         'c_state_size': re.compile(r'c_state_size')}

    # default value is that of Mr. Namikawa's source code of RNN
    c_state_size = 10
    for line in fp:
        for key, value in r.iteritems():
            if value.match(line):
                if key == 'init_tau':
                    str_init_tau = line.split('=')[-1]
                else:
                    str_c_state_size = line.split('=')[-1]
                    c_state_size = int(str_c_state_size)
    
    def split_tau_connection(str_init_tau):
        tau, connection = str_init_tau.split(':')
        itr_begin, itr_end = connection.split('-')
        return tau, itr_begin, itr_end

    tau = []
    connection = []
    if 'str_init_tau' in locals():
        if ',' in str_init_tau:
            list_str_init_tau = str_init_tau.split(',')
            for init_tau in list_str_init_tau:
                t, itr_begin, itr_end = split_tau_connection(init_tau)
                tau.append(float(t))
                connection.append([int(itr_begin)-1, int(itr_end)])
        else:
            if ':' in str_init_tau:
                t, itr_begin, itr_end = split_tau_connection(str_init_tau)
                tau.append(float(t))
                connection.append([int(itr_begin)-1, int(itr_end)])
            else:
                tau.append(float(str_init_tau))
                connection.append([0, c_state_size])

    return tau, connection

if __name__ == '__main__':
    usage = '''python %prog'''
    version = '''%prog 1.1.4
    author     : Ryoichi Nakajo
    last update: 2014/09/26'''
    parser = OptionParser(usage=usage, version=version)
    parser.add_option('-e', '--epoch', action='store',
                      type='int', dest='epoch',
                      help='set the plotting epoch number')
    parser.add_option('-d', '--dimension', action='store',
                      type='int', dest='dimension',
                      help='set the dimmention of plotting')
    parser.add_option('-c', '--config', action='store',
                      type='string', dest='config',
                      help='set the config file that is written parameters `tau`')
    parser.add_option('-l', '--layer-type', action='store',
                      type='string', dest='layer_type',
                      help="set the layer type of state file('OUTPUT_TYPE' or 'CONTEXT_TYPE')")
    parser.add_option('--pca-all-state', '--pca_all_state',
                      action='store_true',
                      dest='pca_all_state', default=False,
                      help='set if plotting all state data of log files or not')
    opt, args = parser.parse_args()

    # setting parameters for plotting
    epoch          = opt.epoch
    dimension      = (opt.dimension if not opt.dimension is None
                      else 3)
    layer_type     = (opt.layer_type if not opt.layer_type is None
                      else 'OUTPUT_TYPE')

    init_tau   = []
    connection = []
    if not opt.config is None:
        try:
            fpr = open(opt.config, 'r')
            init_tau, connection = read_tau(fpr)
            fpr.close()
        except Exception, e:
            print '%s No such file or directory' % (opt.config)
            pass

    if opt.pca_all_state:
        plot_pca_all_state(args, dimension, epoch, layer_type,
                           init_tau, connection)
    else:
        for filename in args:
            fpr = open(filename, 'r')
            plot_log(fpr, filename, dimension, epoch, layer_type,
                     init_tau, connection)
            fpr.close()
