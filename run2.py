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



def run():

    figs = []
    id0 = "-"
                                    #ConsumerZipfMandelbrot
    for consumer in ["ConsumerCbr", "ConsumerZipfMandelbrot"]:
        id1 = id0 +consumer
        for cs in ["Zero", 1,3,5, 10, 0]:
            id2 = id1 + "-cs"+str(cs)
            figid= "FIG-DATA=IST"+id2
            lines = []
            for producerNum in range(1, MAX_PRODUCER_NUM):
                id3 = id2 + "-producer"+str(producerNum)
                lineid = "LINE"+id3
                
                dots =[]
                for duration in range(1, MAX_DURATION):
                    id4 = id3+ "-duration"+str(duration)
                    dotid = "DOT"+id4 
                    
                    dot = Dot(duration, seed=3, producerNum=producerNum, consumerClass=consumer, cs=cs, id=dotid)
                    
                    
                    dots.append(dot)
                ld = {}
                ld["label"] = "Producer="+str(producerNum)
                
                lineid += "-duration[1,"+str(MAX_DURATION)+"]"
                if producerNum == 3 and consumer== "ConsumerCbr":
                    ld["tofit"] = True
                    
                line = Line(dots, ld, id=lineid)
                lines.append(line)
            fd = {}
            
            fd["xlabel"] = "Duration (second)"
            fd["ylabel"] = "# Update"
            fd["grid"] = True
            fd["title"] = "Consumer="+consumer+" cs="+str(cs)
            
            figid += "-producer[1,"+str(MAX_PRODUCER_NUM)+"]"
            fig = Figure(lines, fd, id=figid)
            figs.append(fig)
    pd = {}
    pd["title"] = "routing"
    paper = Paper(figs, pd)
    paper.Daemon = False
    paper.start()
    #time.sleep(5)
    log.info("finish0")
    if True:
        while threading.active_count() > 1:
            if DEBUG:
                time.sleep(10)
            else:
                time.sleep(5)
            log.info("waiting: active threads: "+str(threading.active_count()))
            if threading.active_count() <3:
                for t in threading.enumerate():
                    log.info("threading name = "+t.getName())
    else:
        log.info("main threading waiting ... threads count="+str(threading.active_count()))
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
