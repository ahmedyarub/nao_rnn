#!/usr/bin/env python
# -*- coding: utf-8 -*-

# LAST UPDATE: 20150121
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
SLICE = 1
T_MIN = None
T_MAX = None
PHASE = 0
C_MAP = plt.cm.seismic

PB_NUM = 2

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

def read_parameter(f):
    r = {}
    r["c_state_size"] = re.compile(r"^# c_state_size")
    r["out_state_size"] = re.compile(r"^# out_state_size")
    r_comment = re.compile(r'^#')
    params = {}
    for line in f:
        for k,v in r.iteritems():
            if (v.match(line)):
                x = line.split('=')[1]
                if k == 'target':
                    m = int(v.match(line).group(1))
                    if (k in params):
                        params[k][m] = x
                    else:
                        params[k] = {m:x}
                else:
                    params[k] = x

        if (r_comment.match(line) == None):
            break
    f.seek(0)
    return params

def find_state_file():
    if os.path.isfile("./state000000.log"):
        state_filename = "./state000000.log"
    elif os.path.isfile("../state000000.log"):
        state_filename = "../state000000.log"
    elif os.path.isfile("../../state000000.log"):
        state_filename = "../../state000000.log"
    else:
        print "cannot find state000000.log"
        exit()
    state_file = open(state_filename, "r")
    return state_file

f = find_state_file()    
network_params = read_parameter(f)
c_state_size = int(network_params["c_state_size"])
out_state_size = int(network_params["out_state_size"])

class plot_rnn(object):
    def __init__(self,
                 filename,
                 pb_num):
        self.state_filename = filename
        self.figure_name = self.state_filename.replace(".log", ".eps")
        self.pb_num = pb_num

    def add_info(self, ax, title, xlim, ylim, xlabel, ylabel):
        if title != None:
            ax.set_title(title)

        if xlim != None:
            ax.set_xlim(xlim)
            ax.set_xticks((xlim[0], (xlim[0] + xlim[1]) / 2.0, xlim[1]))

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
        fig_matrix = [5, 1]
        fig, gs, axes = self.configure(fig_matrix, width, height)

        data = np.loadtxt(self.state_filename)
        teach_state = data[:, 1:1 + 3 * out_state_size:3]
        #c_state = np.tanh(data[:, 1 + 3 * out_state_size:1 + 3 * out_state_size + c_state_size])
        c_state = np.tanh(data[:, 1 + 3 * out_state_size:1 + 3 * out_state_size + c_state_size - self.pb_num])
        #c_state = np.tanh(data[:, -4:])
       
        pb_state = data[:, 1 + 3 * out_state_size + c_state_size - self.pb_num :]
        pb_state = np.tanh(pb_state)

        out_state = data[:, 2:1 + 3 * out_state_size:3]
        var_state = data[:, 3:1 + 3 * out_state_size:3]

        axes[0].plot(teach_state[:, ::slice_num])
        self.add_info(axes[0], None, None, (-1, 1), None, "Teach")
        axes[1].plot(out_state[:, ::slice_num])
        self.add_info(axes[1], None, None, (-1, 1), None, "Output")
        axes[2].plot(var_state[:, ::slice_num])
        self.add_info(axes[2], None, None, None, None, "Variance")       
        axes[2].set_yscale("log")
            
        if use_colormap:
            """
            range = [-1, 1]
            im = self.plot_colormap(axes[0], teach_state[:, :], range)
            self.add_info(axes[0], None, None, None, None, "Index of\nteach")
            if teach_state.shape[1] is 1:
                self.set_no_yticks(axes[0])
            axins = inset_axes(axes[0],
                               width = "10%", # width = 5% of parent_bbox width
                               height = "100%", # height : 50%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[0].transAxes,
                               borderpad = 0,
                               )
            plt.colorbar(im, cax = axins, ticks = (-1, 0, 1))

            range = [-1, 1]
            im = self.plot_colormap(axes[1], out_state[:, :], range)
            self.add_info(axes[1], None, None, None, None, "Index of\nout")
            if out_state.shape[1] is 1:
                self.set_no_yticks(axes[1])            
            axins = inset_axes(axes[1],
                               width = "10%", # width = 5% of parent_bbox width
                               height = "100%", # height : 50%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[1].transAxes,
                               borderpad = 0,
                               )
            plt.colorbar(im, cax = axins, ticks = (-1, 0, 1))
            """
            range = [-1, 1]
            im = self.plot_colormap(axes[3], c_state[:, :], range)
            im_pb = self.plot_colormap(axes[4], pb_state[:, :], range)
            self.add_info(axes[3], None, None, None, "Time step", "Index of\ncontext")
            self.add_info(axes[4], None, None, None, "Time step", "PB")

            if c_state.shape[1] is 1:
                self.set_no_yticks(axes[3])

            if pb_state.shape[1] is 1:
                self.set_no_yticks(axes[4])

            axins = inset_axes(axes[3],
                               width = "5%", # width = 5% of parent_bbox width
                               height = "100%", # height : 50%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[3].transAxes,
                               borderpad = 0,
                               )
            axins_pb = inset_axes(axes[4],
                               width = "5%", # width = 5% of parent_bbox width
                               height = "100%", # height : 50%
                               loc = 3,
                               bbox_to_anchor = (1.05, 0, 1, 1),
                               bbox_transform = axes[4].transAxes,
                               borderpad = 0,
                               )
            
            plt.colorbar(im, cax = axins, ticks = (-1, 0, 1))
            plt.colorbar(im_pb, cax = axins_pb, ticks = (-1, 0, 1))
            gs.tight_layout(fig, rect = [0, 0, 0.95, 1]) # left, bottom, right, top

        else:
            axes[3].plot(c_state[:, :])
            axes[4].plot(pb_state[:, :])
            self.add_info(axes[3], None, None, (-1, 1), "Time step","Context")
            self.add_info(axes[4], None, None, (-1, 1), "Time step","PB")
            #self.add_info(axes[4], None, None, None, "Time step","PB")
            
            gs.tight_layout(fig, rect = [0, 0, 1, 1]) # left, bottom, right, top

        for ax in axes:
            ax.set_xlim(tmin, tmax)

        fig.savefig(self.figure_name)
        fig.show()

    def plot_phase(self, phase_plot_num, ax, state, label):
        for i in xrange(state.shape[1] / 2):
            if i == phase_plot_num:
                break            
            ax.plot(state[:, 2 * i], state[:, 2 * i + 1])
        self.add_info(ax, label, (-1, 1), (-1, 1), "i-th dim.", "(i+1)-th dim.")

    def phase(self, phase_plot_num, tmin, tmax, width, height):
        fig_matrix = [1, 4]
        fig, gs, axes = self.configure(fig_matrix, width, height)

        data = np.loadtxt(self.state_filename)
        if (tmin is not None) and (tmax is not None):
            data = data[tmin:tmax, :]
        elif tmin is not None:
            data = data[tmin:, :]
        elif tmax is not None:
            data = data[:tmax, :]

        teach_state = data[:, 1:1 + 3 * out_state_size:3]
        c_state = np.tanh(data[:, 1 + 3 * out_state_size:1 + 3 * out_state_size + c_state_size])
        pb_state = np.tanh(data[:, 1 + 3 * out_state_size + c_state_size - self.pb_num :]) 
        out_state = data[:, 2:1 + 3 * out_state_size:3]

        for ax in axes:
            ax.set_aspect("equal")
        if teach_state.shape[1] is not 1:
            self.plot_phase(phase_plot_num, axes[0], teach_state, "Teach")
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
    parser.add_option("-s", "--slice", dest="slice_num",
                      help="slice value for easy understanding", metavar="SLICE", default=SLICE)
    parser.add_option("-m", "--minimum", dest="tmin",
                      help="minimum value of time axis", metavar="MIN", default=T_MIN)
    parser.add_option("-M", "--maximum", dest="tmax",
                      help="maximum value of time axis", metavar="MAX", default=T_MAX)
    parser.add_option("-p", "--phase", dest = "phase_plot_num", metavar = "PHASE",
                      help="number of phase plot", default = PHASE)
    parser.add_option("-c", "--colormap", dest = "use_colormap", action = "store_false",
                      help="use colormap for context or not", default = True)
    parser.add_option("-b", "--pb", dest="pb_num", 
                      help="input number of PB", metavar="PB_NUM", default=PB_NUM)
    
    (options, args) = parser.parse_args()

    filename = options.filename
    slice_num = int(options.slice_num)
    pb_num = int(options.pb_num)

    if options.tmin is None:
        tmin = options.tmin
    else:
        tmin = int(options.tmin)
    if options.tmax is None:
        tmax = options.tmax
    else:
        tmax = int(options.tmax)
    phase_plot_num = int(options.phase_plot_num)
    use_colormap = options.use_colormap

    plot = plot_rnn(filename, pb_num)
    
    plot.state(slice_num, tmin, tmax, use_colormap, 5, 2)
    if 0 < phase_plot_num:
        plot.phase(phase_plot_num, tmin, tmax, 3, 3.1)
    
    raw_input()

if __name__ == "__main__":
    main()
