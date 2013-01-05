# /usr/bin/python

import sys
import threading
import time

from conf2 import *
from script.updateCounter import getUpdateNum
import matplotlib.pyplot as plt
import os, os.path

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler() #console
ch.setLevel(logging.WARN)
log.addHandler(ch)
#
fh = logging.FileHandler(__name__+".log", mode="w")
fh.setLevel(logging.INFO)
log.addHandler(fh)

import threading


DEBUG = False
def run():
    if DEBUG:
        MAX_DURATION = 3#15
        MAX_PRODUCER_NUM = 4#7
        OUT = "./output3-debug/"
    else :
        MAX_DURATION = 10
        MAX_PRODUCER_NUM = 7

    figs = []
                                    #ConsumerZipfMandelbrot
    for consumer in ["ConsumerCbr", "ConsumerZipfMandelbrot"]:
        for cs in [1, 10]:
            lines = []
            for producerNum in range(1, MAX_PRODUCER_NUM):
                dots =[]
                for duration in range(1, MAX_DURATION):
                    dot = Dot(duration, seed=3, producerNum=producerNum, consumerClass=consumer, cs=cs)
                    dots.append(dot)
                ld = {}
                ld["label"] = "Producer="+str(producerNum)
                line = Line(dots, ld)
                
                lines.append(line)
            fd = {}
            
            fd["xlabel"] = "Duration (second)"
            fd["ylabel"] = "# Update"
            fd["grid"] = True
            fd["title"] = "Consumer="+consumer+" cs="+str(cs)
            fig = Figure(lines, fd)
            figs.append(fig)
    pd = {}
    pd["title"] = "routing"
    paper = Paper(figs, pd)
    paper.Daemon = False
    paper.start()
    log.info("finish0")
    if DEBUG:
        while threading.active_count() > 1:
            time.sleep(5)
            log.info("waiting: active threads: "+str(threading.active_count()))
    else:
        paper.waitChildren()

    log.info("finish")
import signal 
import sys
  
def sigint_handler(signum, frame): 
    sys.exit();

signal.signal(signal.SIGINT, sigint_handler);    

if __name__=="__main__":
    t0 = time.time()
    run()
    t1 = time.time()
    log.info("Runnint Time: "+str(t1-t0)+" second(s). Begint at "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t0)))) 