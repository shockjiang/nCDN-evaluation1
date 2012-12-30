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

fh = logging.FileHandler(__file__+".log", mode="w")
fh.setLevel(logging.INFO)
log.addHandler(fh)

def runCase(testcase):
    if os.path.exists(testcase.output):
        log.info("ready: "+testcase.output)
    else:
        log.info("run cmd: "+testcase.cmd)
        os.system(testcase.cmd)

def processData(case):
    return getUpdateNum(case.output)

def drawFigure(group):

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
    

def readData(infile):
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


def writeData(group):
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
    
def runGroup(group):
    if (os.path.exists(group.outData)):
        print "alread "+str(group.outData)
        for cmd in group.getCMDs():
            print ">> "+cmd
            
        xs, ys, max = readData(group.outData)
        assert group.xs == xs, "x is not the same data in file. xs="+str(group.xs)+", file.xs="+str(xs)
        group.ys = ys
        group.max = max    
    else:
        for case in group.cases:
            runCase(case)
            
            y = processData(case)
            if (y>group.max):
                group.max = y
            group.ys.append(y)
        writeData(group)
        
    #drawFigure(group)


def mergeFigures(merger):
    if (os.path.exists(merger.outFig)):
        print "already " + str(merger.outFig)
        #return
    
    plt.clf()
    
    for group in merger.groups:
        runGroup(group)
        plt.plot(group.xs, group.ys, group.style, label=group.label)
    plt.grid(group.grid, group.gridWhich)
    plt.xlabel(group.xlabel);
    plt.ylabel(group.ylabel);
    
    plt.title(merger.title)
    plt.legend()

    log.info("fig save to "+merger.outFig)
    
    plt.savefig(merger.outFig)    
        
    pass


def run():
    mergeFigures(demo1)
    #mergeFigures(demo2)
        
if __name__ == "__main__":
    run()