import collections
import re
import sys

import cv2
import numpy as np


class ImageProc:
    color_name = ['HOLE', 'YELLOW', 'GREEN', 'BLUE', 'COLOR_NUM']
    Colors = {}
    for i in xrange(0, len(color_name)):
        Colors.setdefault(color_name[i], i)
    del i

    COLOR_CONFIG = collections.namedtuple('color_config', 'range_h range_s range_v')
    CONTOUR_DATA = collections.namedtuple('contour_data', 'x y area')
    CONTOUR_DATA_RANGE = collections.namedtuple('contour_data_range', 'x y area')

    def __init__(self):
        self._verbose = 0
        self._col_conf = []
        self._intensity_th = 0
        self._area_th = 0
        self._debug_img = None

        self._contours = []
        for i in xrange(self.Colors['COLOR_NUM']):
            self._contours.append(self.CONTOUR_DATA(0, 0, 0))
        self._contours_range = self.CONTOUR_DATA_RANGE(x=[-1, 1],
                                                       y=[-1, 1],
                                                       area=[-1, 1])

    def initialize(self, filename, verbose=0):
        self._InitConfig(filename)
        self._verbose = verbose

        if self._verbose:
            cv2.NamedWindow('src_image', cv2.CV_WINDOW_AUTOSIZE)
            cv2.MoveWindow('src_image', 50, 50)
            cv2.NamedWindow('dst_image', cv2.CV_WINDOW_AUTOSIZE)
            cv2.MoveWindow('des_image', 50, 350)

    def SetVerbose(self, val):
        self._verbose = val

    def GetColorConfig(self, ind):
        return self._col_conf[ind]

    def SetColorConfig(self, ind, conf):
        self._col_conf[ind] = conf

    def Process(self, src_img):
        self._contours_range = self.CONTOUR_DATA_RANGE(x=[0, src_img.shape[0]],
                                                       y=[0, src_img.shape[1]],
                                                       area=[0, src_img.shape[1] * src_img.shape[0] / 4])

        dst_img = cv2.cvtColor(src_img, cv2.COLOR_RGB2HSV)

        lower_color = np.array([self._col_conf[0].range_h[0], self._col_conf[0].range_s[0], self._col_conf[0].range_v[0]])
        upper_color = np.array([self._col_conf[0].range_h[1], self._col_conf[0].range_s[1], self._col_conf[0].range_v[1]])

        mask = cv2.inRange(dst_img, lower_color, upper_color)
        imask = mask > 0

        filtered = np.zeros_like(src_img, np.uint8)
        filtered[imask] = src_img[imask]

        self._Labeling(mask, filtered, src_img, self._intensity_th, 0, 1)

        del dst_img

    def GetContourDataSize(self):
        return self.Colors['COLOR_NUM']

    def GetContourData(self, index):
        return self._contours[index]

    def GetXMin(self):
        return self._contours_range.x[0]

    def GetXMax(self):
        return self._contours_range.x[1]

    def GetYMin(self):
        return self._contours_range.y[0]

    def GetYMax(self):
        return self._contours_range.y[1]

    def GetAreaMin(self):
        return self._contours_range.area[0]

    def GetAreaMax(self):
        return self._contours_range.area[1]

    def SaveParameters(self, filename):
        try:
            fpw = open(filename, 'w')
        except:
            print 'Config file open error'
            sys.exit(1)

        for i in xrange(0, self.Colors['COLOR_NUM']):
            fpw.write('%s %d %d %d %d %d %d\n' %
                      (self.color_name[i],
                       self._col_conf[i].range_h[0], self._col_conf[i].range_h[1],
                       self._col_conf[i].range_s[0], self._col_conf[i].range_s[1],
                       self._col_conf[i].range_v[0], self._col_conf[i].range_v[1]))
        fpw.write('INTNS_TH %d\n' % self._intensity_th)
        fpw.write('AREA_TH %d\n' % self._area_th)

        fpw.close()

    # -------------------- PRIVATE FUNCTIONS --------------------

    def _InitConfig(self, filename):
        for i in range(0, self.Colors['COLOR_NUM']):
            self._col_conf.append(self.COLOR_CONFIG(range_h=[0, 0],
                                                    range_s=[0, 0],
                                                    range_v=[0, 0]))
        self._LoadParameters(filename)

    def _LoadParameters(self, filename):
        try:
            fpr = open(filename, 'r')
        except:
            print 'Config file open error!!'
            sys.exit(1)
        while True:
            string = fpr.readline()
            if string == '':
                break
            if not string[0] == '\n':
                arg = re.split('[ ]+', string)
                if not arg[0][0] == '#':
                    self._SetParameter(arg)
        fpr.close()
        return 0

    def _SetParameter(self, arg):
        if arg[0] in self.color_name:
            i = self.Colors[arg[0]]
        elif arg[0] == 'INTNS_TH':
            self._intensity_th = int(arg[1])
            return 0
        elif arg[0] == 'AREA_TH':
            self._area_th = int(arg[1])
            return 0
        else:
            print 'unknown parameter tag %s\n' % (arg[0])
            return 0
        self._col_conf[i] = self.COLOR_CONFIG(range_h=[int(arg[1]), int(arg[4])],
                                              range_s=[int(arg[2]), int(arg[5])],
                                              range_v=[int(arg[3]), int(arg[6])])
        return 0

    def _Labeling(self, mask, filtered, src_img, threshold,
                  c_ind=0, debug_view=0):
        imgray = mask
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) != 0:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(src_img, (x, y), (x + w, y + h), (255, 0, 0), 3)
            cv2.imshow('filtered', filtered)