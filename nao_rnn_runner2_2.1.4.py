#! /usr/bin/env python
# -*- coding:utf-8 -*-

import math
import sys

import numpy as np
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QWidget, QApplication
from naoqi import ALProxy
import vision_definitions

import cv2

import rnn_runner2_pb


def normalize(radian, limit1, limit2):
    return (radian - limit1) / (limit2 - limit1) * 1.6 - 0.8
    # return math.degrees(radian)


class ImageWidget(QWidget):
    """
    Tiny widget to display camera images from Naoqi.
    """

    def __init__(self, ip, port, rnn_file, time_series_id, video_service, CameraID, app_mode='playback', parent=None):
        """
        Initialization.
        """

        self.last_sum = 0
        self.rnn_file = rnn_file
        self.time_series_id = time_series_id
        self.output_init = False
        self.change_rate = 0
        self.movements = []
        self.frames = []

        QWidget.__init__(self, parent)
        self.mode = app_mode
        self._image = QImage()
        self.setWindowTitle('Mode ' + self.mode)

        self.video_service = video_service
        self._imgWidth = 320
        self._imgHeight = 240
        self._cameraID = CameraID
        self.resize(self._imgWidth, self._imgHeight)
        self._imgClient = ""
        self._alImage = None

        self._registerImageClient()

        self._fps = 30
        self.counter = 0

        self.body_names = ['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll', 'RWristYaw',
                           'LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll', 'LWristYaw']

        # Parameters for regression
        self._timeseriesid = time_series_id

        self._windowlength = 10
        self._regcount = 20
        self._rhoinit = 0.0001
        self._momentum = 0.9

        self.points_init_flag = False

        """
        self._windowlength = 20
        self._regcount = 20
        self._rhoinit = 0.0001
        self._momentum = 0.9
        """

        self._gammabp = 1.0
        self._gammatop = 0.0
        self._beta = 0.0

        self._videoProxy = None
        self._motionProxy = None
        try:
            self._motionProxy = ALProxy('ALMotion', ip, port)
        except Exception, e:
            print 'Could not create proxy to ALMotion'
            print 'Error was: ', e

        self.joint_limits = []
        for n in self.body_names:
            self.joint_limits.append(self._motionProxy.getLimits(n)[0])

        self.rnn_orbit = None
        self.filename = None
        self.file = None

        # ----
        self._is_rnn_run = False
        self._time_step = 0
        self._runner = rnn_runner2_pb.RNNRunner()
        self._runner.init(self.rnn_file, self._windowlength)
        self._runner.set_time_series_id(time_series_id)
        self._in_state = self._runner.in_state()
        self._in_state = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0]
        self._out_state_queue = []
        for _ in xrange(self._runner.delay_length()):
            self._out_state_queue.append(self._runner.in_state())

        self.startTimer(40)

    def paintEvent(self, event):
        """
        Draw the QImage on screen.
        """
        painter = QPainter(self)
        painter.drawImage(painter.viewport(), self._image)


    def _updateImage(self):
        """
        Retrieve a new image from Nao.
        """
        self._alImage = self.video_service.getImageRemote(self._imgClient)
        self._image = QImage(self._alImage[6],           # Pixel array.
                             self._alImage[0],           # Width.
                             self._alImage[1],           # Height.
                             QImage.Format_RGB888)

    def _registerImageClient(self):
        """
        Register our video module to the robot.
        """
        resolution = vision_definitions.kQVGA  # 320 * 240
        colorSpace = vision_definitions.kRGBColorSpace
        self._imgClient = self.video_service.subscribe("_client", resolution, colorSpace, 5)

        # Select camera.
        self.video_service.setParam(vision_definitions.kCameraSelectID,
                                  self._cameraID)

    def _unregisterImageClient(self):
        """
        Unregister our naoqi video module.
        """
        if self._imgClient != "":
            self.video_service.unsubscribe(self._imgClient)

    def getHoleCoordinates(self, src_img):
        dst_img = cv2.cvtColor(src_img, cv2.COLOR_RGB2HSV)

        lower_color = np.array([88, 70, 253])
        upper_color = np.array([92, 190, 255])

        mask = cv2.inRange(dst_img, lower_color, upper_color)
        imask = mask > 0

        filtered = np.zeros_like(src_img, np.uint8)
        filtered[imask] = src_img[imask]

        imgray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(imgray, 1, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        c = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(c)
        thresh = thresh[y:y + h, x:x + w]
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        contours.remove(max(contours, key=cv2.contourArea))
        c = max(contours, key=cv2.contourArea)

        M = cv2.moments(c)
        height, width, channels = src_img.shape

        cv2.drawContours(src_img, c, -1, (0, 0, 255), 3, offset=(x, y))

        cv2.imshow("image", src_img)

        return [(float(M['m10'] / M['m00']) + x) / width, (float(M['m01'] / M['m00']) + y) / height]

    def convertQImageToMat(self, incomingImage):
        '''  Converts a QImage into an opencv MAT format  '''

        incomingImage = incomingImage.convertToFormat(4)

        width = incomingImage.width()
        height = incomingImage.height()

        ptr = incomingImage.bits()
        ptr.setsize(incomingImage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
        return arr

    def mouseReleaseEvent(self, event):
        if not self._is_rnn_run:
            print 'Start Mode: ', self.mode

            print 'Setting head position and getting hole coordinates'
            self._motionProxy.stiffnessInterpolation(["HeadPitch", "HeadYaw"], 1.0, 1.0)
            self._motionProxy.angleInterpolation(["HeadPitch", "HeadYaw"], [math.radians(11.7), math.radians(89.9)],
                                                 [1, 1], True)

            img = self.convertQImageToMat(self._image)
            img = cv2.imread('P2.jpg')
            [self.hole_x, self.hole_y] = self.getHoleCoordinates(img)

            print "Starting motion"

            self.counter = 0
            # self.file = open('target.txt', 'w')
            self.output_init = False
            self._is_rnn_run = True

        else:
            print 'Stop ', self.mode
            self._is_rnn_run = False

    def recording(self):
        if self.file is not None:
            joint_angles = self._motionProxy.getAngles(self.body_names, True)
            if sum(joint_angles) != self.last_sum and self.last_sum != 0:
                self.output_init = True
                for i in xrange(len(self.body_names)):
                    self.file.write(str(normalize(joint_angles[i], self.joint_limits[i][0], self.joint_limits[i][1])))

                    if i != len(self.body_names) - 1:
                        self.file.write('\t')

                self.file.write('\n')

                self.counter += 1
                print self.counter
            else:
                if self.output_init and self.counter > 80:
                    self._is_rnn_run = False
                    print 'Stop ', self.mode
                    self.file.close()

            self.last_sum = sum(joint_angles)

    def run_rnn(self):
        if self._is_rnn_run:
            # if len(self._out_state_queue) >= self._runner.delay_length():
            out_state = self._out_state_queue.pop(0)

            # print out_state[4]

            if self._time_step > 5:
                if not self.output_init:
                    self.output_init = True
                    self.change_rate = np.array(out_state[:10]) - np.array(self._in_state[:10])

                    self.movements = []
                    self.frames = []
                    for j in range(0, 10):
                        self.movements.append([])
                        self.frames.append([])

                        self.movements[j].append(
                            (self._in_state[j] + 0.8) * (
                                    self.joint_limits[j][1] - self.joint_limits[j][0]) / 1.6 +
                            self.joint_limits[j][0]
                        )
                        self.frames[j].append(self._time_step / 25.0)

                stopped = True
                for i in range(10):
                    if abs(out_state[i] - self._in_state[i]) > 0.01 or self._time_step < 30:
                        stopped = False
                        break

                for i in range(10):
                    if abs(out_state[i] - self._in_state[i] - self.change_rate[i]) > 0.15 or stopped:
                        self.movements[i].append(
                            (self._in_state[i] + 0.8) * (
                                    self.joint_limits[i][1] - self.joint_limits[i][0]) / 1.6 +
                            self.joint_limits[i][0]
                        )
                        self.frames[i].append(self._time_step / 25.0)
                        self.change_rate[i] = out_state[i] - self._in_state[i]

                if (stopped and self._time_step > 30):
                    print 'Finished collecting RNN data'
                    self._is_rnn_run = False
                    self._time_step = 0
                    self._runner = rnn_runner2_pb.RNNRunner()
                    self._runner.init(self.rnn_file, self._windowlength)
                    print 'time_series_id', self.time_series_id
                    self._runner.set_time_series_id(self.time_series_id)
                    self._in_state = self._runner.in_state()
                    self._in_state = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    self._out_state_queue = []
                    for _ in xrange(self._runner.delay_length()):
                        self._out_state_queue.append(self._runner.in_state())

                    for i in range(len(self.movements)):
                        print self.body_names[i]
                        for j in range(len(self.movements[i])):
                            print self.frames[i][j] * 25, ': ', math.degrees(self.movements[i][j])

                    print 'Movement playback'
                    p_stiffness_lists = 1.0
                    p_time_lists = 1.0

                    p_names = ["Head", 'RArm', 'LArm']

                    self._motionProxy.stiffnessInterpolation(p_names, p_stiffness_lists, p_time_lists)
                    self._motionProxy.setAngles("RHand", 0, 1)
                    self._motionProxy.angleInterpolation(self.body_names, self.movements, self.frames, True)
                    print 'Finished playback!'
                    return

            # print self._time_step

            self._time_step += 1
            # print out_state

            # print list(np.array(out_state) - np.array(self._in_state[:10]))

            # vision: open-loop, arm: closed-loop
            # self._in_state[:len(self.body_names)] = out_state[:len(self.body_names)]
            # all: closed-loop
            self._in_state[:] = out_state[:]
            self._in_state[10] = self.hole_x
            self._in_state[11] = self.hole_y

            # Regression
            self._runner.update(self._timeseriesid, self._time_step, self._in_state, self._regcount, self._rhoinit,
                                self._momentum, self._gammabp, self._gammatop, self._beta)

            out_state = self._runner.out_state()
            self._out_state_queue.append(out_state)
            # prev_out_state = self._out_state_queue[0]

            # print out_state
            # target_angle = []
            # for (val, s) in zip(out_state, scale):
            #    target_angle.append(val * s)
            # for i, val in enumerate(prev_out_state[:len(self.body_names)]):
            #     angle = (val + 0.8) * (self.joint_limits[i][1] - self.joint_limits[i][0]) / 1.6 + \
            #             self.joint_limits[i][0]
            #
            #     target_angle.append(angle)
            # print target_angle[4]
            # self._motionProxy.setAngles(self.body_names, target_angle, 0.2)
            # time.sleep(0.01)

    def timerEvent(self, event):
        self._updateImage()
        self.update()
        if self._is_rnn_run:
            if self.mode == 'recording':
                self.recording()
            else:
                self.run_rnn()

    def __del__(self):
        """
        When the widget is deleted, we unregister our naoqi video module.
        """
        self._unregisterImageClient()


if __name__ == '__main__':
    IP = '127.0.0.1'
    PORT = 9559

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'playback'

    CameraID = 0

    video_service = ALProxy('ALVideoDevice', IP, PORT)

    app = QApplication(sys.argv)
    # myWidget = ImageWidget(IP, PORT, CameraID, filename)
    myWidget = ImageWidget(IP, PORT, 'rnn50_300k.dat', 0, video_service, CameraID, mode)
    myWidget.show()
    sys.exit(app.exec_())
