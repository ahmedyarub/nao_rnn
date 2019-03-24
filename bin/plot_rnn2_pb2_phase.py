#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

from optparse import OptionParser


X_FILENAME = 'generate_naomi000000.log'
Y_FILENAME = 'generate_naoichi000000.log'
IN_STATE_SIZE = 10
NEURON_NUM = 50


class plot_pb_phase(object):
    def __init__(self,
                 filename_x,
                 filename_y,
                 in_state_size,
                 neuron_num):
        self.x_filename = filename_x
        self.y_filename = filename_y
        self.in_state_size = in_state_size
        self.neuron_num = neuron_num

        self.data_x = np.loadtxt(self.x_filename)
        self.data_y = np.loadtxt(self.y_filename)

    def plot_pb(self):

        length_x = self.data_x.shape[0]
        length_y = self.data_y.shape[0]

        if length_x < length_y :
            self.data_y = self.data_y[:length_x, :]
        elif length_x > length_y :
            self.data_x = self.data_x[:length_y, :]

        pb_x_1 = np.tanh(self.data_x[:, self.in_state_size*3 + self.neuron_num])
        pb_x_2 = np.tanh(self.data_x[:, self.in_state_size*3 + self.neuron_num + 1])
        
        pb_y_1 = np.tanh(self.data_y[:, self.in_state_size*3 + self.neuron_num])
        pb_y_2 = np.tanh(self.data_y[:, self.in_state_size*3 + self.neuron_num + 1])
    
        fix, axes = plt.subplots(nrows=1, ncols=2, figsize=(12,5))
        plot1 = axes[0].plot(pb_x_1, pb_y_1, '+', markersize = 2)
        plot2 = axes[1].plot(pb_x_2, pb_y_2, '+', markersize = 2)
 
        #plot1 = axes[0].plot(pb_x_1, pb_y_1, 'o')
        #plot2 = axes[1].plot(pb_x_2, pb_y_2, 'o')
 
        axes[0].set_title('Phase for PB1')
        axes[1].set_title('Phase for PB2')

        for ax in axes:
            ax.set_xlabel('Robot1')
            ax.set_ylabel('Robot2')
            ax.set_xlim((-1, 1))
            ax.set_ylim((-1, 1))

        plt.savefig('PB_phase')
        plt.show()


def main():
    parser = OptionParser()
    parser.add_option("-x", "--file_x", dest="filename_x",
                      help="filename for plot x", metavar="FILENAME_X", default=X_FILENAME)
    parser.add_option("-y", "--file_y", dest="filename_y",
                      help="filename for plot y", metavar="FILENAME_Y", default=Y_FILENAME)
    parser.add_option("-i", "--in", dest="in_state_size",
                      help="number of input state size", metavar="IN", default=IN_STATE_SIZE)
    parser.add_option("-n", "--neuron", dest="neuron_num",
                      help="input number of neuron", metavar="NEURON_NUM", default=NEURON_NUM)
    
    (options, args) = parser.parse_args()

    filename_x = options.filename_x
    filename_y = options.filename_y
    in_state_size = int(options.in_state_size)
    neuron_num = int(options.neuron_num)

    plot = plot_pb_phase(filename_x, filename_y, in_state_size, neuron_num)
    plot.plot_pb()


if __name__ == "__main__":
    main()
