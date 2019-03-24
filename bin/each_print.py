#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os
import subprocess
import glob
import time
import re
import sys

if os.path.isfile("./orbit*.log"):
    os.remove("./orbit*.log")

argc = len(sys.argv)
if argc == 2:
    epoch = "-e " + sys.argv[1] + " "
else:
    epoch = ""

command_init = "rnn-print-log "
filenames = glob.glob('./*closed*state*.log')
filenames.sort()

for i, filename in enumerate(filenames):
    id_s = str(i)
    id_s = id_s.rjust(6, "0")
    new_filename = "orbit" + id_s + ".log"
    command = command_init + epoch + filename + " > " + new_filename
    print command
    p = subprocess.Popen([command], stdin=subprocess.PIPE, shell=True)
    p.wait()
