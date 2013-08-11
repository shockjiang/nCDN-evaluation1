# -*- coding: utf-8 -*-
#!python
#from pyConf import Manager, Case, Dot, Line, Figure, God
import PyConf
from PyConf import Case, Line, Dot
import sys
import platform
"""the platform of the system"""
HOSTOS = platform.system() 
import matplotlib
#matplotlib.use('Agg')
matplotlib.rcParams["font.size"] = 21
matplotlib.rcParams["xtick.labelsize"] = 18
matplotlib.rcParams["lines.linewidth"] = 3.0
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
import os, os.path

#------------------------------
PyConf.ITEM = "latency-test"
PyConf.SCRIPT = "cdn-latency"
PyConf.IS_REFRESH = True

    
#************** Global Settings ****************************************

class Stat(PyConf.Stat):

    def obtain(self):
        ''' get data from raw output data
        '''
        self.log.info("headers: "+ str(self.headers)) 
        for caseId in self.cases:
            case = self.cases[caseId]
            distN = {}
            if (case.result == False):
                distN["-2"] = -2
            else:
                fin = open(case.trace)
                
                sum = 0
                cnt = 0
                for line in fin.readlines():
                    line = line.strip()
                    if line == "" or line.startswith("#") or line.startswith("Time"):
                        continue
                    cols = line.split()
                    kind = cols[4]
                    if kind == "FullDelay":
                        continue
                    
                    latency = round(float(cols[6])/10000)
                    
                    sum += latency
                    cnt += 1
                    
                fin.close()
                #self.data[case.Id] = [rowN, latency/rowN, hop/rowN]
                
                self.data[case.Id] = [sum/cnt if cnt>0 else 1, cnt]
                
                self.log.debug(caseId+": "+str(self.data[case.Id]))

    
class Figure(PyConf.Figure):
    def extend(self, plt):
        self.log.debug("extend")


class God(PyConf.God):
    def __init__(self, paper):
        PyConf.God.__init__(self, paper=paper)
        headers = ["latency", "count"]
        self.stat = Stat(Id=self.parseId(self.dic), cases=self.cases, headers=headers)
        
        
        #headers = ["time", "droppedPacketN", "changeProducerN", "satisfiedRequestN", "unsatisfiedRequestN"]
        #self.stat2 = TraceStat(Id=self.parseId(self.dic), cases=self.cases, headers=headers)

    def setup(self, dic):    
        for freq in self.freq:
            for consumer in self.consumerClass:
                for producerN in self.producerN:
                    for multicast in self.multicast:
                        if consumer == "CDNConsumer" and multicast == "false":
                            continue
                        if consumer == "CDNIPConsumer" and multicast == "true":
                            continue
                        
                        dic["freq"] = freq
                        dic["consumerClass"] = consumer
                        dic["multicast"] = multicast
                        dic["producerN"] = producerN
                        
                        Id = self.parseId(dic)
                        case = Case(Id=Id, param=dic, **dic)
                        self.cases[Id] = case
                    
    
    def world(self, dic):
        self.stat.stat()
        
        lines = []
         
        for multicast in self.multicast:
            dic["multicast"] = multicast
            for consumerClass in self.consumerClass: 
                dic["consumerClass"] = consumerClass
                if consumerClass == "CDNIPConsumer" and multicast == "true":
                    continue
                if consumerClass == "CDNConsumer" and multicast == "false":
                    continue
                dots = []
                
                for producerN in self.producerN:
                    dic["producerN"] = producerN
                
                    for freq in self.freq:#self.freqs:
                        dic["freq"] = freq  
                        Id = self.parseId(dic)
                        
                        if consumerClass == "CDNConsumer":
                           label = "NDN"
                           color = "y"
                        else:
                            label = "IP"
                            color = "b"
                        
                        dot = Dot(x=freq, y=self.stat.get(Id, "latency"))
                        dots.append(dot)
                        #label += ": Frequency="+str(freq)
                    plt = {}
                    plt["color"] = color
                    plt["label"] = label
                    
                    line = Line(dots=dots, plt=plt)
                    lines.append(line)
        canvas = {}
        canvas["ylabel"] = "Average Latency (x$10^2$ MS)"
        canvas["xlabel"] = "Frequency"
        canvas["loc"] = "lower right"
        
        fig = Figure(Id=PyConf.ITEM, lines = lines, canvas=canvas)
        fig.bar()
        
        ####
        pass

if __name__=="__main__":
    #cmd = "./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'>output/Case/ist-set.output 2>&1"
    #print os.system(cmd)
    #global DEBUG    
    for i in range(1, len(sys.argv)):
        av = sys.argv[i]
        if av == "--debug":
            PyConf.DEBUG = True
            PyConf.ITEM = "latency-test"
            PyConf.SCRIPT = "test"
            #PyConf.IS_REFRESH = True

            PyConf.OUT = PyConf.OUT+"-debug"
        elif av == "--nodebug":
            PyConf.DEBUG = False
            
    god = God(paper=PyConf.PAPER)
    god.create(god.setup)
    
    try:
        god.run()
    except IOError as e:
        self.log.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        
    else:
        god.create(god.world)
        
        if God.IsError:
            os.remove(god.stat.out)
    finally:
        if (not PyConf.DEBUG) and (not PyConf.HOSTOS.startswith("Darwin")):
            god.notify(way="email")
        else:
            god.notify(way="print")

