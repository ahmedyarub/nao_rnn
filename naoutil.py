#! /usr/bin/env python
# -*- coding:utf-8 -*-

import time
from naoqi import ALProxy
import vision_definitions
import cv2 as cv
from multiprocessing import Process, Queue
import os


def stiffness_on(motionProxy):
    pNames = "Body"
    pStiffnessLists = 1.0
    pTimeLists = 1.0
    motionProxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)

def stiffness_off(motionProxy):
    pNames = "Body"
    pStiffnessLists = 0.0
    pTimeLists = 1.0
    motionProxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)

def nao_set_stiffness(motionProxy, val):
    # We use the "Body" name to signify the collection of all joints
    pNames = "Body"
    pStiffnessLists = val
    pTimeLists = 1.0
    motionProxy.stiffnessInterpolation(pNames, pStiffnessLists, pTimeLists)

        
def nao_crouch_posture(motionProxy):
    names = ["LHipYawPitch", "RHipYawPitch", "LHipRoll", "RHipRoll"]
    target_angles = [-0.27, -0.27, 0.0, 0.0]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["LHipPitch", "RHipPitch", "LKneePitch", "RKneePitch"]
    target_angles = [-0.65, -0.65, 2.11, 2.11]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["LAnklePitch", "RAnklePitch", "LAnkleRoll", "RAnkleRoll"]
    target_angles = [-1.18, -1.18, -0.1, -0.1]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["HeadYaw", "HeadPitch"]
    target_angles = [0.0, 0.0]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["LShoulderPitch", "RShoulderPitch", "LShoulderRoll", "RShoulderRoll"]
    target_angles = [0.2, 0.2, 1.0, -1.0]
    motionProxy.setAngles(names, target_angles, 0.2)
    names = ["LElbowYaw", "RElbowYaw"]
    target_angles = [-1.8, 1.8]
    motionProxy.setAngles(names, target_angles, 0.2)
    time.sleep(1)

    names = ["LShoulderPitch", "RShoulderPitch", "LShoulderRoll", "RShoulderRoll"]
    target_angles = [1.5, 1.5, 0.2, -0.2]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["LElbowYaw", "RElbowYaw", "LElbowRoll", "RElbowRoll"]
    target_angles = [-1.2, 1.2, -1.5, 1.5]
    motionProxy.setAngles(names, target_angles, 0.2)

    names = ["LWristYaw", "RWristYaw"], "LHand", "RHand"]
    target_angles = [0.0, -0.0, 1.0, 1.0]
    motionProxy.setAngles(names, target_angles, 0.2)


def nao_camera_calibration(robotIP, port):
    if port == None:
        port = 9559

    width = 160
    height = 120
    raw_img = cv.CreateImage((width, height), cv.IPL_DEPTH_8U, 3)

    videoProxy = ALProxy("ALVideoDevice", robotIP, port)
    resolution = vision_definitions.kQQVGA
    colorSpace = vision_definitions.kRGBColorSpace
    fps = 30
    img_client = videoProxy.subscribe("calib_client", resolution, colorSpace, fps)
    videoProxy.setActiveCamera("_client", 1)

    alImg = video_proxy.getImageRemote(img_client)
    rgb_img = cv.CreateImageHeader((width, height), cv.IPL_DEPTH_8U, 3)
    cv.SetData(rgb_img, alImg[6])
    cv.CvtColor(rgb_img, raw_img, cv.CV_RGB2BGR)

    videoProxy.unsubscribe(img_client)

def nao_print_joint_limits(motionProxy):
    name = "Body"
    limits = motionProxy.getLimits(name)
    jointNames = motionProxy.getBodyNames(name)
    for i in range(0, len(limits)):
        print jointNames[i] + ":"
        print "minAngle", limits[i][0], \
            "maxAngle", limits[i][1],\
            "maxVelocity", limits[i][2],\
            "maxTorque", limits[i][3]
