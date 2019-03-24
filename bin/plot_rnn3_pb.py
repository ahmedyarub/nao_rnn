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

PB_NUM = 4
NEURON_NUM = 50

params = {"backend": "eps",
          "axes.titlesize": 10,
          "axes.labelsize": 10,
          "text.fontsize": 10,
          "legend.fontsize": 10,
          "xtick.labelsize": 10,
          "ytick.labelsize": 10,
          "text.usetex": False,
          "savefig.facecolor": "0.75"}
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
        fig_matrix = [6, 1]
        fig, gs, axes = self.configure(fig_matrix, width, height)
        delay_length = self.delay_length
        
        in_state = self.data[:, :self.in_state_size]
        out_state = self.data[:, self.in_state_size:self.in_state_size * 2]
        #var_state = self.data[:, self.in_state_size * 2:self.in_state_size * 3] + 0.001
        var_state = self.data[:, self.in_state_size * 2:self.in_state_size * 3] + 0.000001
        c_state = np.tanh(self.data[:, self.in_state_size * 3: self.in_state_size * 3 + self.neuron_num] )
        pb_state = np.tanh(self.data[:, self.in_state_size*3 + self.neuron_num :] ) 
        #pb_state = self.data[:, self.in_state_size*3 + self.neuron_num :]          

        #print :-self.pb_num
        #print self.in_state_size*3 + self.neuron_num - self.pb_num

        #print in_state[delay_length:, :]
        #print out_state[:-delay_length, :]
        
 
        #error = 1.0/np.sqrt(2.0*np.pi*var_state[:-delay_length, :]) * np.exp(-(in_state[delay_length:, :] - out_state[:-delay_length, :]) * (in_state[delay_length:, :] - out_state[:-delay_length, :]) / 2.0 / var_state[:-delay_length, :])
        error = (in_state[delay_length:, :] - out_state[:-delay_length, :]) * (in_state[delay_length:, :] - out_state[:-delay_length, :]) / 2.0
        #print error

	precision_error = (in_state[delay_length:, :] - out_state[:-delay_length, :]) * (in_state[delay_length:, :] - out_state[:-delay_length, :]) / 2.0 / var_state[:-delay_length, :]
	#likelihood = 0.5 * np.log(2 * np.pi * (var_state[:, :]+0.000001)) + 0.5 * precision_error[:, :]

        axes[0].plot(in_state[:, :8])

        self.add_info(axes[0], None, (0, in_state.shape[0]), (-1, 1), None, "Predicted" + "\nJoint")

        #axes[0].plot(in_state[:, ::slice_num])

        #self.add_info(axes[0], None, (0, in_state.shape[0]), (-1, 1), None, "Input")
        #self.add_info(axes[0], None, None, (-1, 1), None, "Input")
        #axes[1].plot(out_state[:, ::slice_num])
        #self.add_info(axes[1], None, (0, out_state.shape[0]), (-1, 1), None, "Output")
        axes[1].plot(in_state[:, 8],"g")
        axes[1].plot(in_state[:, 9],"r")
        self.add_info(axes[1], None, (0, in_state.shape[0]), (-1, 1), None, "Input"+ "\nVision")

        #self.add_info(axes[1], None, None, (-1, 1), None, "Output")
 

        #axes[2].plot(var_state[:, :8])

        axes[2].plot(var_state[:,8],"g")
        axes[2].plot(var_state[:,9],"r")
        #self.add_info(axes[2], None, (0, var_state.shape[0]), None, None, "Variance")       
        self.add_info(axes[2], None, (0, var_state.shape[0]), (10**(-6),10**(-1)), None, "Variance")       
        #self.add_info(axes[2], None, None, None, None, "Variance")       
        axes[2].set_yscale("log")
            
        if use_colormap:

            range = [-1, 1]
            im = self.plot_colormap(axes[3], c_state[:, :], range)
            im_pb = self.plot_colormap(axes[4], pb_state[:, :], range)

            self.add_info(axes[3], None, None, None, None, "Index of\ncontext")
            #self.add_info(axes[4], None, None, None, None, "PB")
            self.add_info(axes[4], None, None, None, None, "Index of\n pb")

            if c_state.shape[1] is 1:
                self.set_no_yticks(axes[3])

            if pb_state.shape[1] is 1:
                self.set_no_yticks(axes[4])

            axins = inset_axes(axes[3],
                               width = "5%", # width = 5% of parent_bbox width
                               height = "100%", # height : 100%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[3].transAxes,
                               borderpad = 0,
                               )
            axins_pb = inset_axes(axes[4],
                               width = "5%", 
                               height = "100%",# height = "100%"
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[4].transAxes,
                               borderpad = 0,
                               )
            
            plt.colorbar(im, cax = axins, ticks = (-1, 0, 1))
            plt.colorbar(im_pb, cax = axins_pb, ticks = (-1, 0, 1))
            gs.tight_layout(fig, rect = [0, 0, 0.95, 1]) # left, bottom, right, top
            

        else:
            axes[3].plot(c_state[:, 0:10])
            #axes[3].plot(c_state[:, ::slice_num])
            axes[4].plot(pb_state[:, :])

            self.add_info(axes[3], None, (0, c_state.shape[0]), (-1.2, 1.2), None, "Context")
            #self.add_info(axes[4], None, (0, c_state.shape[0]), (-1, 1), None, "PB")
            #self.add_info(axes[4], None, (0, pb_state.shape[0]), None, None, "PB")
            #self.add_info(axes[4], None, (0, pb_state.shape[0]), (-1, 1), None, "PB")
            self.add_info(axes[4], None, (0, pb_state.shape[0]), (-1.2, 1.2), None, "PB")
            #self.add_info(axes[3], None, None, (-1, 1), "Time step", "Context")
            gs.tight_layout(fig, rect = [0, 0, 1, 1]) # left, bottom, right, top

 
       
        #axes[5].plot(error[:, 9],"r")
	#axes[5].plot(precision_error[:, ::slice_num])
        axes[5].plot(error[:, ::slice_num])
        #self.add_info(axes[5], None, (0, in_state.shape[0]), (0,5000), "Time step", "MSPE\n"+"Vision")
	self.add_info(axes[5], None, (0, in_state.shape[0]), None, "Time step", "MSPE\n"+"Vision")
        #self.add_info(axes[5], None, (0, in_state.shape[0]), (0, 0.2), "Time step", "Prediction error")
        #self.add_info(axes[5], None, (0, in_state.shape[0]), (0, 1.0), "Time step", "Prediction error")
        #axes[2].set_yscale("log")
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
        fig_matrix = [1, 3]
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
