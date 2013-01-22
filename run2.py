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
#update#(0)   Interest#(1)    DataNew#(2)    DataMet#(3)       Nack#(4)     
#record#(5)  ALastDelay(6)  AFullDelay(7)      AvgHop(8)    AvgRetx#(9)
YLABELS = ["UPDATE", "INTEREST", "DataNew", "DataMet", "Nack", 
          "Record", "Avg Last Delay", "Avg Full Delay", "Avg Hop Length", "Avg Retx"]
YLABEL_DIC = {}

for i in range(len(YLABELS)):
    YLABEL_DIC[i] = YLABELS[i]
    
YLABEL_DIC["0.3"] = "Update/Data"
YLABEL_DIC["4.3"] = "Nack/Data"
YLABEL_DIC["1.3"] = "Interest/Data"
#Yindex = 9

def run():
    #for Yindex in [7, 9, 3, 8, "0.3", "4.3"]:
    for Yindex in ["1.3", "0.3", "4.3"]:
        run2(Yindex)
        
def run2(Yindex):

    figs = []
    id0 = ""
    for consumer in CONSUMER_CLASS_LIST:
        id1 = id0 + "-"+consumer
        
        for cs in CS_LIST:
            id2 = id1 + "-cs"+str(cs)
            lines = []
            
            #
            # The following you can add more lines into one Figure
            #
            
            for producerNum in range(1, MAX_PRODUCER_NUM):
                id3 = id2 + "-producer"+str(producerNum)            
               
                for nack in ["true", "false"]:
                    id4 = id3 + "-nack"+nack
                #
                # The above you can add more lines into one Figure
                #
                                            
                    dots = []
                    for duration in range(1, MAX_DURATION):
                        id5 = id4+ "-duration"+str(duration)
    
                        dotid = "DOT"+id5
                        dd = {}
                        dd["duration"] = duration
                        dd["seed"] = 3
                        dd["producerNum"] = producerNum
                        dd["consumerClass"] = consumer
                        dd["csSize"] = cs
                        dd["nack"] = nack
                        dot = Dot(data=dd, id=dotid)
                        
                        #dot = Dot(duration, seed=3, producerNum=producerNum, consumerClass=consumer, cs=cs, id=dotid)    
                        dots.append(dot)
                
                    ld = {}
                    ld["label"] = "Producer="+str(producerNum)+", Nack="+nack
                    #update#(0)   Interest#(1)    DataNew#(2)    DataMet#(3)       Nack#(4)     
                    #record#(5)  ALastDelay(6)  AFullDelay(7)      AvgHop(8)    AvgRetx#(9)
                    ld["Yindex"] = Yindex
                    lineid ="LINE" + id4 + "-duration[1,"+str(MAX_DURATION-1)+"]"
#                    if producerNum == 3 and consumer== "ConsumerCbr":
#                        ld["tofit"] = True
                        
                    line = Line(dots, ld, id=lineid)
                    lines.append(line)
                #for duration    
            #for producernum
            fd = {}
            
            fd["xlabel"] = "Simulation Duration (second)"
            fd["ylabel"] = YLABEL_DIC[Yindex]
            fd["grid"] = True
            fd["title"] = fd["ylabel"] + "\nConsumer="+consumer+" cs="+str(cs)
            
            figid= "FIG-"+fd["ylabel"].replace(" ", "").replace("/", "=")+id2
            figid += "-producer[1,"+str(MAX_PRODUCER_NUM-1)+"]"
            fig = Figure(lines, fd, id=figid)
            figs.append(fig)
            #for cs
        #for nack
    #for consumer
    pd = {}
    pd["title"] = "CDNDN"
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
