#! /usr/bin/python2.7
import sys
import platform
"""the platform of the system"""
HOSTOS = platform.system() 



import matplotlib
matplotlib.use('Agg')
#matplotlib.use("pdf")
import matplotlib.pyplot as plt


import md5
import os, os.path
import signal, sys, time
import string
import smtplib


import inspect
#from script.updateCounter import getUpdateNum
from script.cmp import cmp
import logging
import threading


IS_MT = True #Multi Threads Run
IS_REFRESH = True
IS_REFRESH = False
OUT = "output"
DEBUG = False


if HOSTOS.startswith("Darwin"):
    DEBUG = True

DEBUG = False

if DEBUG:
    MAX_DURATION = 2#15
    MAX_PRODUCER_NUM = 3#7
    CS_LIST =["Zero"]
    OUT += "-debug"
    #CONSUMER_CLASS_LIST = ["ConsumerZipfMandelbrot"]
    CONSUMER_CLASS_LIST = ["ConsumerCbr", "ConsumerZipfMandelbrot"]
    IS_REFRESH = True
    
else :
    MAX_DURATION = 10
    MAX_PRODUCER_NUM = 3
    CS_LIST = ["Zero"]
    CONSUMER_CLASS_LIST = ["ConsumerCbr", "CDNIPApp"]

LOG_LEVEL = logging.DEBUG


AliveCaseCounter = 0

class ClassFilter(logging.Filter):
    """filter the log information by class name
    """
    ALLOWED_CLASS_LI = None #default is None, which means all logger should be allowed, else give a list of allowed logger
    #ALLOWED_CLASS_LI = ["Figure"]
    
    
    def filter(self, record):
        if ClassFilter.ALLOWED_CLASS_LI == None:
            return True
        
        if record.name in ClassFilter.ALLOWED_CLASS_LI:
            return True
        else:
            return False

log = logging.getLogger() #root logger

format = logging.Formatter('%(levelname)5s:%(name)6s:%(lineno)3d: %(message)s')   
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#http://docs.python.org/2/library/self.logging.html#self.logrecord-attributes
#logging.basicConfig(format=format, datefmt='%m/%d/%Y %I:%M:%S %p')

fh = logging.FileHandler("conf.log", mode="w")
fh.setFormatter(format)

sh = logging.StreamHandler() #console
sh.setFormatter(format)

f = ClassFilter()
sh.addFilter(f)
#sh.addFilter(logging.Filter("Figure"))


log.addHandler(sh)
log.addHandler(fh)

    
class Manager:
    """ Super Class of all the manager class, name as an example, Case, Dot, Line, Figure and Paper"""
    def __init__(self, id, **kwargs):
        self.id = id
        self.daemon = True
        self.isMT = IS_MT
        self.isRefresh = IS_REFRESH
        self.t0 = time.time()
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        #self.log.basicConfig(format=format, datefmt='%I:%M:%S %p')
        #print "log name="+self.log.name
        self.log.setLevel(LOG_LEVEL)
        
#        if self.log.name in LOG_ALLOW:
#            self.log.addFilter(logging.Filter("Case"))
#        
        self.out = os.path.join(OUT, self.__class__.__name__)
        if not os.path.exists(self.out):
            os.makedirs(self.out)
        outType = ".dat"
        if "outType" in kwargs:
            outType = kwargs["outType"]
        self.out = os.path.join(self.out, self.id+outType)
    
    def parseId(self, dic):
        """ get the id from attributes held in dic
        
        """
        id = ""
        keys = dic.keys()
        keys.sort()
        for k in keys:
            v = dic[k]
            id += "-"+str(k)+str(v)
        return id
    def notify(self, way="email", **msg):
        self.t1 = time.time()
        data = self.id+" ends on "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+ \
            " after running for "+str(self.t1 - self.t0)+" seconds"
        data = msg.get("data", data)
        
        self.log.info(data)
        print data
        if way == "print":
            return
        
        from smtplib import SMTP
        TO = msg.get("to", ["shock.jiang@gmail.com"])
        FROM = "06jxk@163.com"
        SMTP_HOST = "smtp.163.com"
        user= "06jxk"
        passwords="jiangxiaoke"
        mailb = ["paper ends", data]
        mailh = ["From: "+FROM, "To: shock.jiang@gmail.com", "Subject: Paper ends "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))]
        mailmsg = "\r\n\r\n".join(["\r\n".join(mailh), "\r\n".join(mailb)])
    
        send = SMTP(SMTP_HOST)
        send.login(user, passwords)
        rst = send.sendmail(FROM, TO, mailmsg)
        
        if rst != {}:
            self.log.warn("send mail error: "+str(rst))
        else:
            self.log.info("sending mail finished")
        send.close()
    
    
class Stat(Manager):
    def __init__(self, id):
        Manager.__init__(self, id=id)
        pass
    
    def add(self, fp):
        if not os.path.exists(fp):
            self.log.error("fp="+fp+" does not exist")
            return
        fp = open(fp)
        rows = fp.readlines()
        if len(rows) == 0:
            self.log.error("fp="+fp+" is blank")
            return
        row = rows[0]
        colN = len(row.split())
        
        if not hasattr(self, "data"):
            #self.data = [0 for i in range(colN)]
            pass
    
        for row in rows:
            row = row.strip()
            if row=="" or row.startswith("Time") or row.startswith("#"):
                continue
            
            parts = row.split()
            ##time    node    I-Ist    O-Ist    D-Ist    I-Data    O-Data    D-Data
    
            #0.2        0        4        1        0        21        21        0
            assert len(parts) == colN, "len(parts)="+str(len(parts))+" ("+str(colN)+" is OK). row="+str(row)
            
            
            
            
    def statApp(self, fp):#*.trace
        if not os.path.exists(fp):
            self.log.error("fp="+fp+" does not exist")
            return
        fp = open(fp)
        rows = fp.readlines()
        if len(rows) == 0:
            self.log.error("fp="+fp+" is blank")
            return
        row = rows[0]
        colN = len(row.split())
        
        varname = "app"
        rowN = 0
        if not hasattr(self, varname):
            var = [0 for i in range(2)]
            exec("self."+varname+"=var")
            #self.log.info("self."+varname+"="+str(var))
            pass
        #Time    Node    AppId    SeqNo    Type    DelayS    DelayUS    RetxCount    HopCount
        #0.04724    34    1    0    LastDelay    0.04724    47240    1    11           
        
        consumers = [2, 10, 12, 22, 34, 38, 44, 50]
        
        for row in rows:      
            row = row.strip()
            if row=="" or row.startswith("Time") or row.startswith("#"):
                continue
            
            
            parts = row.split()
            #assert len(parts)==colN, "len("+parts+")!="+str(colN)
            assert len(parts) == colN, self.id+": len(parts)="+str(len(parts))+" ("+str(colN)+" is OK). row="+str(row)
            node = int(parts[1])
            if not node in consumers:
                continue
            
            delay = float(parts[6])
            hop = int(parts[8])
            
            Type = parts[4]
            if Type == "FullDelay":
                continue
            
    
            var[0] += delay
            var[1] += hop
            rowN += 1
        
        exec("self."+varname+"N=rowN")
        #self.log.info("self."+varname+"N=varN")
    def statRate(self, fp): #rate
        self.log.debug("statRate begin "+fp)
        if not os.path.exists(fp):
            self.log.error("fp="+fp+" does not exist")
            return
        fp = open(fp)
        rows = fp.readlines()
        if len(rows) == 0:
            self.log.error("fp="+fp+" is blank")
            return
        row = rows[0]
        colN = len(row.split())
        
        varname = "rate"
        rowN = 0
        if not hasattr(self, varname):
            var = [0 for i in range(colN)]
            exec("self."+varname+"=var")
            pass
#time    node    I-Ist    O-Ist    D-Ist    I-Data    O-Data    D-Data
#1        0        432        0        216        0        0        0     
            
        data = self.rate
                    
        for row in rows:
            row = row.strip()
            if row=="" or row.startswith("Time") or row.startswith("#"):
                continue
            
            parts = row.split()
            ##time    node    I-Ist    O-Ist    D-Ist    I-Data    O-Data    D-Data
    
            #0.2        0        4        1        0        21        21        0
            assert len(parts) == colN, "len(parts)="+str(len(parts))+" ("+str(colN)+" is OK). row="+str(row)
            
            #print str(parts)
            time = float(parts[0])
            node = int(parts[1])
            iist = int(parts[2])
            oist = int(parts[3])
            dist = int(parts[4])
            idata = int(parts[5])
            odata = int(parts[6])
            ddata = int(parts[7])
            
            consumers = [2, 10, 12, 22, 34, 38, 44, 50]
            if node in consumers:
                data[0] += idata
                data[1] += iist
                data[2] += oist
                data[3] += dist
                data[4] += idata
                data[5] += odata
                data[6] += ddata
                #self.log.debug("node="+str(node))
                rowN += 1

                if ddata > 0:  
                    self.log.debug("consumer: "+str(parts))
                continue
            providers = [8, 9]
            if node in providers:
                continue
            #data[0] += float(time)
            
        
        exec("self."+varname+"N=rowN")
class Case(Manager, threading.Thread):
    """ run program/simulation case, trace file is printed to self.trace, console msg is printed to self.output
        and self.out is stored the statstical information
        
        self.data
    """    
    LiveN = 0
    def __init__(self, id, param={}, **kwargs):
        threading.Thread.__init__(self)
        Manager.__init__(self, id)
        
        self.cmd = "./waf --run \'name-set"
        self.stat = Stat(id=id)
        self.param = param
        

        self.trace = os.path.join(OUT, self.__class__.__name__, self.id+".app") #trace out put
        self.output = os.path.join(OUT, self.__class__.__name__, self.id+".output") #case run console output
        self.output = "/dev/null"
        self.ratetrf = os.path.join(OUT, self.__class__.__name__, self.id+".rate")
        
        
        for key, val in param.items():
            self.cmd += " --"+key+"="+str(val) 
        #./waf --run "xiaoke --trace=./shock/output2-debug/Dot/DOT-ConsumerCbr-csZero-producer1-nackfalse-duration1.trace 
        #--nack=false 
        #--producerNum=1 
        #--consumerClass=ConsumerCbr 
        #--seed=3 
        #--duration=1">output2-debug/Dot/DOT-ConsumerCbr-csZero-producer1-nackfalse-duration1.dat 2>&1
        self.cmd += " --trace="
        self.cmd += os.path.join("shock", self.trace)
# #         self.cmd += " --csSize="
# #         self.cmd += str(kwargs["csSize"]) if "csSize" in kwargs else "Zero"
# #         self.cmd += " --nack="
# #         self.cmd +=  kwargs["nack"] if "nack" in kwargs else "true"
# #         self.cmd += " --producerNum="
# #         self.cmd += str(kwargs["producerNum"]) if "producerNum" in kwargs else "1"
#         self.cmd += " --consumerClass="
#         self.cmd += kwargs["consumerClass"] if "consumerClass" in kwargs else "ConsumerCbr"
#         self.cmd += " --freq="
#         self.cmd += str(kwargs["freq"]) if "freq" in kwargs else "1"
#         self.cmd += " --seed="
#         self.cmd += str(kwargs["seed"]) if "seed" in kwargs else "3"
#         self.cmd += " --duration="
#         self.cmd += str(kwargs["duration"]) if "duration" in kwargs else "1"
    
        self.cmd += " --ratetrf="
        self.cmd += os.path.join("shock", self.ratetrf)
            
        self.cmd +=  "\'";
        self.cmd += ">"+self.output+" 2>&1"  
   
    def start(self):
        Case.LiveN += 1
        threading.Thread.start(self)
        
    def run(self):
        """ run the case, after running, the statstical result is held in self.data as list
        """
        #Case.LiveN += 1
        self.log.info("> " +self.id+" begins")
        if not self.isRefresh and os.path.exists(self.ratetrf):
            pass
        else:    
            self.log.info("+ "+ "CMD: "+self.cmd)
            #print os.popen("./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'").readlines()
            
            #rst = os.system(self.cmd)
            rst = os.system(self.cmd)
            if rst != 0:
                self.log.error("CMD: "+self.cmd+" return "+str(rst)+" (0 is OK). Output: "+self.output)
                if (os.path.exists(self.out)):
                    os.remove(self.out)
                if (os.path.exists(self.trace)):
                    os.remove(self.trace)
                if (os.path.exists(self.output)):
                    os.remove(self.output)
                
                #return
        self.stats()
        Case.LiveN -= 1
        self.log.info("< "+str(self.id)+" ends. Live Case Nun ="+str(Case.LiveN))
        
        
    def stats(self):
        """ stats on the output of the runed case
        """
        self.stat.statRate(self.ratetrf)
        self.stat.statApp(self.trace)
            
class Dot():        
    def __init__(self, x, y):
        self.x = x
        self.y = y  
        
class Line(Manager):
    def __init__(self, dots, plt={}, **kwargs):
        #for dot in dots:
        dotN = len(dots)
        self.xs = [dots[i].x for i in range(dotN)]
        self.ys = [dots[i].y for i in range(dotN)]
        self.plt = plt
        
        
class Figure(Manager):
    """ information of Figure
        such as title, xlabel, ylabel, etc
    """
    def __init__(self, id, lines, canvas={}, **kwargs):
        Manager.__init__(self, id, outType=".pdf")
        self.detail = os.path.join(OUT, self.__class__.__name__, self.id+".dat")
        self.lines = lines
        self.canvas = canvas

#         self.lines = lines
#         self.style = kwargs["style"] if "style" in kwargs else "o-"
#         
#         self.title = kwargs["title"] if "title" in kwargs else None
#         self.xlabel = kwargs["xlabel"] if "xlabel" in kwargs else None
#         
#         self.ylabel = kwargs["ylabel"] if "ylabel" in kwargs else "Number of Packets"
#         self.ymin = kwargs["ymin"] if "ymin" in kwargs else None
#         self.ymax = kwargs["ymax"] if "ymax" in kwargs else None
#         self.legendloc = kwargs["legendloc"] if "legendloc" in kwargs else "upper right"
#         
        self.kwargs = kwargs
        
    def line(self):
        self.log.debug(self.id+" begin to draw ")
        plt.clf()
        
        cans = []
        for line in self.lines:
            self.log.info("line.xs="+str(line.xs))
            self.log.info("line.ys="+str(line.ys))
            self.log.info("plt atts="+str(line.plt))
            can = plt.plot(line.xs, line.ys, line.plt.pop("style", "o-"), **line.plt)
            cans.append(can)
        
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.legend(**self.canvas)
        
        
        plt.grid(True)

        self.log.debug(self.id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.close()
        
        self.log.info(self.id+" ends")
    
    
    def bar(self):
        self.log.debug(self.id+" begin to draw ")
        plt.clf()
        
        plt.xticks([i+0.3 for i in range(6)], ("Transmission Time", "Hops", "Data Recieved"))
        self.bars = []
        for line in self.lines:
#             if hasattr(line, "label") and line.label != None:
#                 plt.plot(line.xs, line.ys, self.style, label=line.label)
#             else:
#                 plt.plot(line.xs, line.ys, self.style)
#    
            print "line.xs=",line.xs
            print "line.ys=", line.ys       
            bar = plt.bar(left=line.xs, height=line.ys, width=0.3, bottom=0, **line.plt)
            self.bars.append(bar)
            
        #plt.legend( (p1[0], p2[0]), ('Men', 'Women') )
        
        plt.legend((self.bars[i][0] for i in range(len(self.lines))), (self.lines[i].plt["label"] for i in range(len(self.lines))))
        #for bar in self.bars:

                
        plt.grid(True)
        if self.xlabel != None:
            plt.xlabel(self.xlabel);
        if self.ylabel != None:
            plt.ylabel(self.ylabel);
        if self.title != None:
            plt.title(self.title)
            
        if self.ymin != None:
            plt.ylim(ymin=self.ymin)
        if self.ymax != None:
            plt.ylim(ymax=self.ymax)
        #location: http://matplotlib.org/api/pyplot_api.html
        plt.legend(loc=self.legendloc)
        self.log.debug(self.id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.close()
        
        self.log.info(self.id+" finishes")
    

# class Paper(Manager):
#     """ information of paper, which includes multiple figure
#     
#         to do: run latex command to generate paper directly
#     """
#     def __init__(self, id, figs, **kwargs):
#         Manager.__init__(self, id)
#         self.figs = figs
#         OUT = os.path.join(OUT, id)



class God(Manager):
    """ God to control all the processes of the program, when to run cases, how to assign data and draw figs
    
    """
    
    def __init__(self, paper):
        """ God will run all the cases needed
        
        """
        Manager.__init__(self, id="GOD")
        self.t0 = time.time()
        global OUT
        OUT = os.path.join(OUT, paper)
        
#         dir = os.path.split(os.path.realpath(__file__))[0]
#         os.chdir(dir)
        self.cases = {}
        
        self.freqs = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1, 1.2, 1.5, 2, 3, 5, 7, 8, 10, 12, 15, 18, 20,22,25,28, 30, 32, 35, 38]
        self.freqs = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.8]
        self.freqs += [1, 1.2, 1.5, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.5, 2.8, 3, 3.2,  3.4, 3.5, 3.6, 3.7, 3.8, 4, 4.5, 5,6, 7, 8]
        
        #self.freqs += [10, 15, 20, 30]
        #self.freqs = [1, 1.2, 1.5, 2, 3, 5, 7, 8, 10, 12, 15, 18, 20]
        #self.freqs = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1]
        self.freqs = [self.freqs[i]* 10 for i in range(len(self.freqs))]
        self.consumers = ["ConsumerCbr", "ConsumerSet"]
        
        
    def setup(self):
        cases = self.cases
        for freq in self.freqs:
            dic = {}
            dic["freq"] = freq
            for consumer in self.consumers:
                dic["consumerClass"] = consumer
                
                id = self.parseId(dic)
                case = Case(id=id, param=dic, **dic)
                cases[id] = case
                
        
        for id, case in cases.items():
            case.start()
            
        for id, case in cases.items():
            if case.isAlive():
                case.join()
            
            #case.stats()
        
        
        
    def sayApp(self):
        figs = {}
        lines = []
        lines2 = []
        lines3 = []
        #lines4 = []
        for consumer in self.consumers:
            param = {}
            param["consumerClass"] = consumer
            dots = []
            dots2 = []
            dots3 = []
            #dots4 = []
            for freq in self.freqs:
                param["freq"] = freq    
                id = self.parseId(param)
                case = self.cases[id]
                plt = {}
                if consumer == "ConsumerCbr":
                    plt["color"] = "y"
                    plt["label"] = "Normal Interest"
                    offset = 0
                else:
                    plt["color"] = "r"
                    plt["label"] = "Interest Set"
                    offset = 0.3
                dot = Dot(x=freq, y=case.stat.app[0]/float(case.stat.appN))
                dots.append(dot)
                
                dot2 = Dot(x=freq, y=case.stat.app[1]/float(case.stat.appN))
                dots2.append(dot2)
                
                dot3 = Dot(x=freq, y=case.stat.appN)
                dots3.append(dot3)
                
                #dot4 = Dot(x=freq, y=case)
            line = Line(dots, plt=plt)
            lines.append(line)
            
            line2 = Line(dots2, plt=plt)
            lines2.append(line2)

            line3 = Line(dots3, plt=plt)
            lines3.append(line3)

        
        
        canvas = {}
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        
        canvas["ylabel"] = "Transmission Delay (ms)"
        canvas["loc"] = "lower right"      
        fig = Figure(id="tx-deplay=freqs", lines=lines, canvas=canvas)
        fig.line()
        
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        canvas["ylabel"] = "Average Transmission Hops"
        fig2 = Figure(id="hop=freqs", lines=lines2, canvas=canvas)
        fig2.line()
        
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        dots = []
        for i in range(len(self.freqs)):
            dot = Dot(x=self.freqs[i], y=32*8*self.freqs[i])
            dots.append(dot)
        line = Line(dots, plt)
        #lines3.append(line)
        fig3 = Figure(id="data-received", lines=lines3, canvas=canvas)
        fig3.line()
        
        
    def sayRate(self):
        figs = {}
        lines = []
        lines2 = []
        lines3 = []
        for consumer in self.consumers:
            param = {}
            param["consumerClass"] = consumer
            dots = []
            dots2 = []
            dots3 = []
            plt = {}
            if consumer == "ConsumerCbr":
                plt["color"] = "y"
                plt["label"] = "Normal Interest"
            else:
                plt["color"] = "r"
                plt["label"] = "Interest Set"
                
                
            for freq in self.freqs:
                param["freq"] = freq    
                id = self.parseId(param)
                case = self.cases[id]
                
                
                dot = Dot(x=freq, y=case.stat.rate[2])
                dots.append(dot)
                
                dot = Dot(x=freq, y=case.stat.rate[5])
                dots2.append(dot)
                
                dot = Dot(x=freq, y=case.stat.rate[0])
                dots3.append(dot)
            line = Line(dots, plt=plt)
            lines.append(line)
            if consumer == "ConsumerSet":
                ds = []
                for dot in dots:
                    d = Dot (dot.x, 32*dot.y)
                    ds.append(d)
                line = Line(dots=ds, plt={"color":"b", "style":"o--", "label":"Impact of Interest Set"})
                lines.append(line)
            
            line = Line(dots2, plt=plt)
            lines2.append(line)
                
            line = Line(dots3, plt=plt)
            lines3.append(line)
        canvas = {}
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        #canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        
        canvas["loc"] = "upper left"
        
        fig = Figure(id="Ist-fwN=freq", lines=lines, canvas=canvas)
        fig.line()
        canvas["loc"] = "lower right"
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        fig = Figure(id="Data-fwN=freq", lines=lines2, canvas=canvas)
        fig.line()
        canvas["xlabel"] = "Interest Set Freqency or Equally Interest Freqency(/32)"
        fig = Figure(id="Consumer-in-Data=freq", lines=lines3, canvas=canvas)
        fig.line()
        
if __name__=="__main__":
    #cmd = "./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'>output/Case/ist-set.output 2>&1"
    #print os.system(cmd)
    god = God(paper="name-set")
    god.setup()
    god.sayApp()
    god.sayRate()
    #god.notify(way="email")
            
            
