# /usr/bin/python

import sys
import threading
import time

from conf import *
from script.updateCounter import getUpdateNum
import matplotlib.pyplot as plt
import os, os.path

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler() #console
ch.setLevel(logging.INFO)
log.addHandler(ch)
#
fh = logging.FileHandler(__name__+".log", mode="w")
fh.setLevel(logging.INFO)
log.addHandler(fh)

import threading
class Dot(threading.Thread):
    def __init__(self, case):
        threading.Thread.__init__(self)
        self.case = case
        
    def run(self):
        testcase = self.case
        log.info(">Dot "+testcase.getID()+" begins")
        if os.path.exists(testcase.output):
            log.debug("dot data ready: "+testcase.output)
        else:
            log.debug("cmd="+testcase.cmd)
            os.system(testcase.cmd)
            
        self.case.y = self.processData()
        log.debug(" dot.y="+str(self.case.y))
        log.info("<Dot "+self.case.getID()+" finishes")
        
    def processData(self):
        case = self.case
        return getUpdateNum(case.output)
        
lockrd = threading.RLock()    

class Line(threading.Thread):
    def __init__(self, group):
        threading.Thread.__init__(self)
        self.group = group
        self.dots = [Dot(case) for case in group.cases]
    
    
    def drawFigure(self):
        group = self.group
        
        log.debug(group.xs)
        log.debug(group.ys)
        if (os.path.exists(group.outFig)):
            log.info("alread "+str(group.outFig))
            return
    
        plt.clf()
        
        plt.xlabel(group.xlabel);
        plt.ylabel(group.ylabel);
        plt.plot(group.xs, [float(y)/group.max for y in group.ys],
                 group.style, label=group.label)
        
        plt.grid(group.grid, group.gridWhich)
        if (group.title != None):
            plt.title(group.title)
        plt.legend()
    
        plt.ylim(group.ymin, group.ymax)
        #plt.show()
        log.info("fig save to "+group.outFig)
        
        plt.savefig(group.outFig)
    

    def readData(self):
        infile = self.group.outData
        #assert len(xs)==len(ys), "len(xs)!=len(ys) xs="+str(xs)+", ys="+str(ys)
        xs = []
        ys = []
        max = 0
        f = open(infile)
        for rd in f.readlines():
            if rd.startswith(DATA_LINE_IGNORE_FLAG):
                continue
            rd = rd.strip()
            [x, y] = rd.split()
            x = int(x)
            y = int(y)
            xs.append(x)
            ys.append(y)
            if y>max:
                max = y
        f.close()
        return xs, ys, max


    def writeData(self):
        group = self.group
        xs = group.xs
        ys = group.ys
        outfile = group.outData
        assert len(xs)==len(ys),  "len(xs)!=len(ys) xs="+str(xs)+", ys="+str(ys)
        f = open(outfile, "w")
        f.write(DATA_LINE_IGNORE_FLAG+"\t"+group.id+"\n");
        for cmd in group.getCMDs():
            f.write(DATA_LINE_IGNORE_FLAG + "\t" + cmd+"\n")
        f.write(DATA_LINE_IGNORE_FLAG+"\t"+group.xlabel+"\t"+group.ylabel+"\n")
        for i in range(len(xs)):
            x = xs[i]
            y = ys[i]
            f.write(str(x)+"\t"+str(y)+"\n")
        f.flush()
        f.close()
    
    def run(self):
        group = self.group
        log.info(">Line "+self.group.getID()+" begin")
        
#        global lockrd
#        lock = lockrd
#        
        hasfile = os.path.exists(group.outData)
#        
        if (hasfile):
            log.debug( "line data alread "+str(group.outData))
#            for cmd in group.getCMDs():
#                log.info( ">> "+cmd)
#                
            xs, ys, max = self.readData()
            assert group.xs == xs, "x is not the same data in file. xs="+str(group.xs)+", file.xs="+str(xs)
            group.ys = ys
            group.max = max    
            log.debug("line read data from file: "+group.outData)
        else:
            for dot in self.dots:
                dot.start()
        
            self.wait_all_complete()        
        log.info("<Line "+self.group.getID()+" finishes")
        
    def wait_all_complete(self):            
        for dot in self.dots:
            if dot.isAlive():
                dot.join()
        
        # not ok if already have file
        group = self.group        
        for case in group.cases:
            #assert case.y != -1, "group: "+group.getID()+" case.y == -1"
            group.ys.append(case.y)
            
            log.debug("group "+group.getID()+" add ys="+str(case.y)+" xs="+str(group.xs)+" ys="+str(group.ys))
        if (not os.path.exists(self.group.outData)):
            self.writeData()
        
               
lockplt=threading.RLock()        

class Figure(threading.Thread):
    def __init__(self, merger):
        threading.Thread.__init__(self)
        self.merger = merger
        self.lines = [Line(group) for group in merger.groups]
        
        
    def run(self):
        merger = self.merger
        log.info(">Figure "+merger.getName("-")+" begins")
        if (os.path.exists(merger.outFig)):
            log.debug( "Figure "+merger.getName("-")+" data alread")
            #return
        
        for line in self.lines:
            line.start()
        
        self.wait_all_complete()
        
        global lockplt
        lock = lockplt
        lock.acquire()
        log.debug("begin to draw ")
        plt.clf()
        log.debug("1")
        #plt.figure(figsize=(5,9))
        log.debug("2")
        for line in self.lines:
            group = line.group
            log.info("group "+group.getID()+" xs="+str(group.xs)+" ys="+str(group.ys)+ " label="+group.label)
            plt.plot(group.xs, group.ys, group.style, label=group.label)


            
        merger = self.merger
        plt.grid(group.grid, group.gridWhich)
        plt.xlabel(group.xlabel);
        plt.ylabel(group.ylabel);
        
        plt.title(self.merger.title)
        plt.legend()
        log.debug("fig save to "+merger.outFig) 
        plt.savefig(merger.outFig)
        #plt.close()
        
        log.info("<Figure "+self.merger.getName("-")+" finishes")
        log.debug("end to draw")
        lock.release()
        
    def wait_all_complete(self):
        for line in self.lines:
            if line.isAlive():
                line.join()

        
        
        
    

class Paper(threading.Thread):
    def __init__(self, demos):
        threading.Thread.__init__(self)
        self.demos = demos
        self.figures = [Figure(demo) for demo in demos]
        
    def run(self):
        log.info(">Paper begin")
        for figure in self.figures:
            figure.start()
            
        self.wait_all_complete()
        log.info("<Paper finishes")
            
    def wait_all_complete(self):
        for figure in self.figures:
            if figure.isAlive():
                figure.join()
        

def clear(path):
    if os.path.exists(path):
        os.remove(path)        
        
if __name__ == "__main__":
    t0 = time.clock()
    paper = Paper([fig1, fig2, fig3, fig4])
    av = sys.argv
    if (len(av) > 1):
        value = av[1]
        if (value == "clear"):
            for demo in paper.demos:
                clear(demo.outFig)
                for group in demo.groups:
                    
                    clear(group.outData)
                    clear(group.outFig)
                    for case in group.cases:
                        clear(case.output)
        log.info("clear all")
    else:
        paper.start()
        log.info("isAlive = "+str(paper.isAlive()))
        #time.sleep(1)
        #paper.run()
        paper.wait_all_complete()
        
    
    t1 = time.clock()
    
    log.info("Runnint Time: "+str(t1-t0))
    #    if paper.isAlive():
    #        paper.join()
    #        
    #    paper = Paper([demo2])
#        paper.start()
    #paper.wait_all_complete()