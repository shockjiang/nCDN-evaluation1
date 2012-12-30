import sys
import threading
import time
#print sys._getframe().f_code.co_filename
#print sys._getframe().f_code.co_name
#print sys._getframe().f_lineno
#
#print __file__
#print __name__

#
#class TestCase(threading.Thread):
#    def __init__(self, id):
#        threading.Thread.__init__(self)
#        self.id = id
#        #self.start()
#        
#        
#    def run(self):
#        print "thread "+str(self.id)+" begin"
#        time.sleep(3)
#        print "threading "+str(self.id) + "wait"
#        time.sleep(3)
#        print "thread "+str(self.id)+" end"
#        
#class CaseGroup:
#    def __init__(self, cases):
#        self.cases = cases
#    
#    def run(self):
#        for case in self.cases:
#            case.start()
#            
#    def wait_all_complete(self):
#        print "begin to wait"
#        for case in self.cases:
#            if case.isAlive():
#                case.join()
#        
#        print "all end"
#
#class TestCaseMgr(threading.Thread):
#    def __init__(self):
#        threading.Thread.__init__(self)
#        
#if __name__=="__main__":
#    tcs = []
#    for i in range(5):
#        case = TestCase(i)
#        tcs.append(case)
#    group = CaseGroup(tcs)
#    group.run()
#    
#    group.wait_all_complete()
#    

from conf import *
from script.updateCounter import getUpdateNum
import matplotlib.pyplot as plt
import os, os.path

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler() #console
ch.setLevel(logging.DEBUG)
log.addHandler(ch)
#
#fh = logging.FileHandler(__file__+".log", mode="w")
#fh.setLevel(logging.INFO)
#log.addHandler(fh)
import threading
class CaseMgr(threading.Thread):
    def __init__(self, case):
        threading.Thread.__init__(self)
        self.case = case
        
    def run(self):
        testcase = self.case
        log.info("case "+testcase.getID()+" begin to run")
        if os.path.exists(testcase.output):
            log.info("ready: "+testcase.output)
        else:
            log.info("run cmd: "+testcase.cmd)
            log.info("cmd="+testcase.cmd)
            os.system(testcase.cmd)
            
        self.case.y = self.processData()
        log.info(" case.y="+str(self.case.y))
        
    def processData(self):
        case = self.case
        return getUpdateNum(case.output)
        log.info("case "+case.getID()+" finished")
    

class GroupMgr(threading.Thread):
    def __init__(self, group):
        threading.Thread.__init__(self)
        self.group = group
        self.caseMgrs = [CaseMgr(case) for case in group.cases]
    
    
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
        for line in f.readlines():
            if line.startswith(DATA_LINE_IGNORE_FLAG):
                continue
            line = line.strip()
            [x, y] = line.split()
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
        log.debug("group "+self.group.getID()+" run")
        if (os.path.exists(group.outData)):
            log.info( "alread "+str(group.outData))
            for cmd in group.getCMDs():
                log.info( ">> "+cmd)
                
            xs, ys, max = self.readData()
            assert group.xs == xs, "x is not the same data in file. xs="+str(group.xs)+", file.xs="+str(xs)
            group.ys = ys
            group.max = max    
            log.info("read ys from file: "+str(ys))
        else:
            for caseMgr in self.caseMgrs:
                caseMgr.start()
                
                
    def wait_all_complete(self):
        if self.isAlive():
            self.join()
            
        for caseMgr in self.caseMgrs:
            if caseMgr.isAlive():
                caseMgr.join()
        
        log.info("group "+self.group.getID()+" finished")        
        # not ok if already have file        
        for case in self.group.cases:
            self.group.ys.append(case.y)
            log.info("add ys="+str(case.y))
        if (not os.path.exists(self.group.outData)):
            self.writeData()
        
        
        

class MergerMgr(threading.Thread):
    def __init__(self, merger):
        threading.Thread.__init__(self)
        self.merger = merger
        self.groupMgrs = [GroupMgr(group) for group in merger.groups]
        
        
    def run(self):
        merger = self.merger
        log.info(" merger "+merger.getName()+" mgr begins to run")
        if (os.path.exists(merger.outFig)):
            log.info( "already " + str(merger.outFig))
            #return
        
        plt.clf()
        plt.figure(figsize=(5,9))
        for groupMgr in self.groupMgrs:
            groupMgr.start()
            groupMgr.wait_all_complete()
            
            group = groupMgr.group
            plt.plot(group.xs, group.ys, "o-", label=group.label)
        plt.grid(group.grid, group.gridWhich)
        plt.xlabel(group.xlabel);
        plt.ylabel(group.ylabel);
        
        plt.title(merger.title)
        plt.legend()
    
        log.info("fig save to "+merger.outFig)
        
        plt.savefig(merger.outFig)
        

    def wait_all_complete(self):
        for groupMgr in self.groupMgrs:
            if groupMgr.isAlive():
                groupMgr.join()
        log.info("merge "+self.merger.getName()+" finished")
    

class Paper(threading.Thread):
    def __init__(self, demos):
        threading.Thread.__init__(self)
        self.demos = demos
        self.mergerMgrs = [MergerMgr(demo) for demo in demos]
        
    def run(self):
        log.debug("demos mgr begin to run")
        for mgr in self.mergerMgrs:
            mgr.start()
            #mgr.wait_all_complete()
            
    def wait_all_complete(self):
        for mgr in self.mergerMgrs:
            if mgr.isAlive():
                mgr.join()
        
        log.info("all demo finished")
        
if __name__ == "__main__":
    mgr = Paper([demo2])
    mgr.start()
    mgr.wait_all_complete()