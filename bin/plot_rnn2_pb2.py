#!/usr/bin/env python
# -*- coding: utf-8 -*-

# LAST UPDATE: 20150601
# by Shingo Murata, Waseda Univ., Tokyo, Japan

import numpy as np
import pylab
import re
import os


import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# http://matplotlib.org/examples/axes_grid/demo_colorbar_with_inset_locator.html

from optparse import OptionParser

STATE_FILENAME = "orbit.log"
IN_STATE_SIZE = 10
SLICE = 1
T_MIN = None
T_MAX = None
PHASE = 0
DELAY = 5
C_MAP = plt.cm.seismic

PB_NUM = 2
NEURON_NUM = 70

params = {"backend": "eps",
          "axes.titlesize": 10,
          "axes.labelsize": 10,
          "text.fontsize": 10,
          "legend.fontsize": 10,
          "xtick.labelsize": 10,
          "ytick.labelsize": 10,
          "text.usetex": False,
          "savefig.facecolor": "1"}
pylab.rcParams.update(params)

class plot_rnn(object):
    def __init__(self,
                 filename,
                 in_state_size,
                 delay_length,
                 pb_num,
                 neuron_num):
        self.state_filename = filename
        self.in_state_size = in_state_size
        self.delay_length = delay_length

        self.data = np.loadtxt(self.state_filename)
        self.figure_name = self.state_filename.replace(".log", ".eps")

        self.pb_num = pb_num
        self.neuron_num = neuron_num

    def add_info(self, ax, title, xlim, ylim, xlabel, ylabel):
        if title != None:
            ax.set_title(title)

        if xlim != None:
            ax.set_xlim(xlim)
            #ax.set_xticks((xlim[0], (xlim[0] + xlim[1]) / 2.0, xlim[1]))

        if xlabel != None:
            ax.set_xlabel(xlabel)

        if ylim != None:
            ax.set_ylim(ylim)
            ax.set_yticks((ylim[0], (ylim[0] + ylim[1]) / 2.0, ylim[1]))
        if ylabel != None:
            ax.set_ylabel(ylabel)

        ax.grid(True) 

    def set_no_yticks(self, ax):
        ax.set_yticks([])

    def configure(self, fig_matrix, width, height):
        fig = plt.figure(figsize = (width * fig_matrix[1], height * fig_matrix[0]))
        gs = gridspec.GridSpec(fig_matrix[0], fig_matrix[1])
        axes = [fig.add_subplot(gs[i, j]) for i in xrange(fig_matrix[0]) for j in xrange(fig_matrix[1])]
        return fig, gs, axes

    def plot_colormap(self, ax, state, range):
        im = ax.imshow(state.T, vmin = range[0], vmax = range[1], aspect = "auto", interpolation = "nearest", cmap = C_MAP)
        if state.shape[0] is not 1:
            ax.set_xlim(0, state.shape[0])
            ax.set_ylim(-0.5, state.shape[1] - 0.5)
            ax.set_yticks((0, state.shape[1] -1))
        return im

    def state(self, slice_num, tmin, tmax, use_colormap, width, height):
        fig_matrix = [8, 2]
        fig, gs, axes = self.configure(fig_matrix, width, height)
        delay_length = self.delay_length

        in_state = self.data[:, :self.in_state_size]
        out_state = self.data[:, self.in_state_size:self.in_state_size * 2]
        var_state = self.data[:, self.in_state_size * 2:self.in_state_size * 3] + 0.001
        c_state = np.tanh(self.data[:, self.in_state_size * 3: self.in_state_size * 3 + self.neuron_num] )
        pb_state = np.tanh(self.data[:, self.in_state_size*3 + self.neuron_num :] ) 
        #pb_state = self.data[:, self.in_state_size*3 + self.neuron_num :]          

        #print :-self.pb_num
        #print self.in_state_size*3 + self.neuron_num - self.pb_num

        #print in_state[delay_length:, :]
        #print out_state[:-delay_length, :]
        error = (in_state[delay_length:, :] - out_state[:-delay_length, :]) * (in_state[delay_length:, :] - out_state[:-delay_length, :]) / 2.0

        #print error
    
        precision_error = error[:, :] / var_state[:-delay_length, :]
        
        likelihood = (1 / (np.sqrt( 2 * np.pi * var_state[:-delay_length, :]))) *  np.exp( -1 * precision_error[:, :])
        likelihood = -np.log(likelihood)
 
        #print precision_error
        #print likelihood

        axes[0].plot(in_state[:, :8:slice_num])
        self.add_info(axes[0], "Proprioception", (0, in_state.shape[0]), (-1, 1), None, "Input")
        #self.add_info(axes[0], None, (0, in_state.shape[0]), (-1, 1), None, "Input\n Proprioception")

        axes[1].plot(in_state[:, 8::slice_num])
        self.add_info(axes[1], "Vision", (0, in_state.shape[0]), (-1, 1), None, "Input")
        #self.add_info(axes[1], None, (0, in_state.shape[0]), (-1, 1), None, "Input\n Vision")

        #self.add_info(axes[0], None, None, (-1, 1), None, "Input")
        axes[2].plot(out_state[:, :8:slice_num])
        self.add_info(axes[2], None, (0, out_state.shape[0]), (-1, 1), None, "Output")
        
        axes[3].plot(out_state[:, 8::slice_num])
        self.add_info(axes[3], None, (0, out_state.shape[0]), (-1, 1), None, "Output")
        
        #self.add_info(axes[1], None, None, (-1, 1), None, "Output")
        axes[4].plot(var_state[:, :8:slice_num])
        self.add_info(axes[4], None, (0, var_state.shape[0]), None, None, "Variance")       
        axes[5].plot(var_state[:, 8::slice_num])
        self.add_info(axes[5], None, (0, var_state.shape[0]), None, None, "Variance")       
        #self.add_info(axes[2], None, None, None, None, "Variance")       
        axes[4].set_yscale("log")
        axes[5].set_yscale("log")
            
        if use_colormap:
            range = [-1, 1]
            im_joint = self.plot_colormap(axes[6], c_state[:, :], range)
            im_vision = self.plot_colormap(axes[7], c_state[:, :], range)
            im_pb_joint = self.plot_colormap(axes[8], pb_state[:, :], range)
            im_pb_vision = self.plot_colormap(axes[9], pb_state[:, :], range)

            self.add_info(axes[6], None, None, None, None, "Index of\nContext")
            self.add_info(axes[7], None, None, None, None, "Index of\nContext")
                        
            #self.add_info(axes[4], None, None, None, None, "PB")
            self.add_info(axes[8], None, None, None, None, "Index of\n PB")
            self.add_info(axes[9], None, None, None, None, "Index of\n PB")

            if c_state.shape[1] is 1:
                self.set_no_yticks(axes[6])
                self.set_no_yticks(axes[7])

            if pb_state.shape[1] is 1:
                self.set_no_yticks(axes[8])
                self.set_no_yticks(axes[9])

            axins_vision = inset_axes(axes[7],
                               width = "5%", # width = 5% of parent_bbox width
                               height = "100%", # height : 50%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                                      bbox_transform = axes[7].transAxes,
                               borderpad = 0,
                               )
                            
            axins_pb_vision = inset_axes(axes[9],
                               width = "5%", 
                               height = "100%",
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[9].transAxes,
                               borderpad = 0,
                               )           
                                
            plt.colorbar(im_vision, cax = axins_vision, ticks = (-1, 0, 1))
            plt.colorbar(im_pb_vision, cax = axins_pb_vision, ticks = (-1, 0, 1))
            gs.tight_layout(fig, rect = [0, 0, 0.95, 1]) # left, bottom, right, top
            

        else:
            axes[6].plot(c_state[:, :])
            axes[7].plot(c_state[:, :])
            axes[8].plot(pb_state[:, :])
            axes[9].plot(pb_state[:, :])

            self.add_info(axes[6], None, (0, c_state.shape[0]), (-1, 1), None, "Context")
            self.add_info(axes[7], None, (0, c_state.shape[0]), (-1, 1), None, "Context")
            #self.add_info(axes[4], None, (0, c_state.shape[0]), (-1, 1), None, "PB")
            
            #self.add_info(axes[8], None, (0, pb_state.shape[0]), None, None, "PB")
            #self.add_info(axes[9], None, (0, pb_state.shape[0]), None, None, "PB")

            self.add_info(axes[8], None, (0, pb_state.shape[0]), (-1, 1), None, "PB")
            self.add_info(axes[9], None, (0, pb_state.shape[0]), (-1, 1), None, "PB")


            #self.add_info(axes[3], None, None, (-1, 1), "Time step", "Context")
            gs.tight_layout(fig, rect = [0, 0, 1, 1]) # left, bottom, right, top

        #axes[10].plot(error[:, ::slice_num])
        axes[10].plot(error[:, :8:slice_num])
        #self.add_info(axes[10], None, (0, in_state.shape[0]), None, "Time step", "Prediction Error")
        self.add_info(axes[10], None, (0, in_state.shape[0]), (0, 1), "Time step", "Prediction Error")


        axes[11].plot(error[:, 8::slice_num])
        #self.add_info(axes[11], None, (0, in_state.shape[0]), None, "Time step", "Prediction Error")
        self.add_info(axes[11], None, (0, in_state.shape[0]), (0, 1), "Time step", "Prediction Error")


        axes[12].plot(precision_error[:, :8:slice_num])
        self.add_info(axes[12], None, (0, in_state.shape[0]), None, None, "PE/Var")

        axes[13].plot(precision_error[:, 8::slice_num])
        self.add_info(axes[13], None, (0, in_state.shape[0]), None, None, "PE/Var")

        axes[14].plot(likelihood[:, :8:slice_num])
        self.add_info(axes[14], None, (0, in_state.shape[0]), None, None, "Likelihood")

        axes[15].plot(likelihood[:, 8::slice_num])
        self.add_info(axes[15], None, (0, in_state.shape[0]), None, None, "Likelihood")
        
        #axes[14].set_yscale("log")
        #axes[15].set_yscale("log")



        for ax in axes:
            ax.set_xlim(tmin, tmax)

        fig.savefig(self.figure_name)
        fig.show()

    def plot_phase(self, phase_plot_num, ax, state, label):
        for i in xrange(state.shape[1] / 2):
            if i == phase_plot_num:
                break            
            ax.plot(state[:, 2 * i], state[:, 2 * i + 1])
        self.add_info(ax, label, (-1, 1), (-1, 1), "2*i-th dim.", "(2*i+1)-th dim.")

    def phase(self, phase_plot_num, tmin, tmax, width, height):
        fig_matrix = [1, 4]
        fig, gs, axes = self.configure(fig_matrix, width, height)

        if (tmin is not None) and (tmax is not None):
            data = self.data[tmin:tmax, :]
        elif tmin is not None:
            data = self.data[tmin:, :]
        elif tmax is not None:
            data = self.data[:tmax, :]
        else: 
            data = self.data

        in_state = data[:, :self.in_state_size]
        out_state = data[:, self.in_state_size: 2 * self.in_state_size]
        c_state = np.tanh(data[:, 3 * self.in_state_size: 3 * self.in_state_size + self.neuron_num])
        pb_state = np.tanh(data[ 3 * self.in_state_size + self.neuron_num:])
        

        for ax in axes:
            ax.set_aspect("equal")
            ax.set_xticks((-1, 0, 1))
            ax.set_yticks((-1, 0, 1))

        if in_state.shape[1] is not 1:
            self.plot_phase(phase_plot_num, axes[0], in_state, "Input")
        if out_state.shape[1] is not 1:
            self.plot_phase(phase_plot_num, axes[1], out_state, "Output")
        if c_state.shape[1] is not 1:
            self.plot_phase(phase_plot_num, axes[2], c_state, "Context")
        if pb_state.shape[1] is not 1:
            self.plot_phase(phase_plot_num, axes[3], pb_state, "PB")
        

        gs.tight_layout(fig, rect = [0, 0, 1, 1]) # left, bottom, right, top
        fig.savefig(self.figure_name.replace(".eps", "_phase.eps"))
        fig.show()

def main():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="filename for plot", metavar="FILENAME", default=STATE_FILENAME)
    parser.add_option("-i", "--in", dest="in_state_size",
                      help="number of input state size", metavar="IN", default=IN_STATE_SIZE)
    parser.add_option("-s", "--slice", dest="slice_num",
                      help="slice value for easy understanding", metavar="SLICE", default=SLICE)
    parser.add_option("-m", "--minimum", dest="tmin",
                      help="minimum value of time axis", metavar="MIN", default=T_MIN)
    parser.add_option("-M", "--maximum", dest="tmax",
                      help="maximum value of time axis", metavar="MAX", default=T_MAX)
    parser.add_option("-p", "--phase", dest = "phase_plot_num", metavar = "PHASE",
                      help="number of phase plot", default = PHASE)
    parser.add_option("-d", "--delay", dest = "delay_length", metavar = "DELAY",
                      help="delay_length used in the training phase", default = DELAY)
    parser.add_option("-c", "--colormap", dest = "use_colormap", action = "store_true",
                      help="use colormap for context or not", default = False)
    parser.add_option("-b", "--pb", dest="pb_num", 
                      help="input number of PB", metavar="PB_NUM", default=PB_NUM)
    parser.add_option("-n", "--neuron", dest="neuron_num",
                      help="input number of neuron", metavar="NEURON_NUM", default=NEURON_NUM)

    (options, args) = parser.parse_args()

    filename = options.filename
    in_state_size = int(options.in_state_size)
    slice_num = int(options.slice_num)
    pb_num = int(options.pb_num)
    neuron_num = int(options.neuron_num)

    if options.tmin is None:
        tmin = options.tmin
    else:
        tmin = int(options.tmin)
    if options.tmax is None:
        tmax = options.tmax
    else:
        tmax = int(options.tmax)
    phase_plot_num = int(options.phase_plot_num)
    delay_length = int(options.delay_length)
    use_colormap = options.use_colormap
    
    
    plot = plot_rnn(filename, in_state_size, delay_length, pb_num, neuron_num)
    
    plot.state(slice_num, tmin, tmax, use_colormap, 6, 2)
    if 0 < phase_plot_num:
        plot.phase(phase_plot_num, tmin, tmax, 3, 3.1)
    
    raw_input()

if __name__ == "__main__":
    main()
