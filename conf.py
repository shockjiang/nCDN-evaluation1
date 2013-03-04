import sys
import matplotlib
matplotlib.use("pdf")
import platform
"""the platform of the system"""
HOSTOS = platform.system() 

import matplotlib.pyplot as plt
import md5
import os, os.path
import signal, sys, time
import string
import smtplib


import inspect
from script.updateCounter import getUpdateNum
from script.cmp import cmp
import logging
import threading


IS_MT = True #Multi Threads Run
IS_REFRESH = False


OUT = "output"
DEBUG = False


if HOSTOS.startswith("Darwin"):
    DEBUG = True

if DEBUG:
    MAX_DURATION = 8#15
    MAX_PRODUCER_NUM = 4#7
    CS_LIST =["Zero"]
    OUT += "-debug"
    CONSUMER_CLASS_LIST = ["ConsumerCbr"]
    
else :
    MAX_DURATION = 10
    MAX_PRODUCER_NUM = 7
    CS_LIST = ["Zero", 1,3,5, 10, 0]
    CS_LIST = ["Zero", 1,3,5, 10, 0]
    CONSUMER_CLASS_LIST = ["ConsumerCbr", "ConsumerZipfMandelbrot"]


LOG_LEVEL = logging.DEBUG

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

class Case(Manager, threading.Thread):
    """ run program/simulation case, trace file is printed to self.trace, console msg is printed to self.output
        and self.out is stored the statstical information
        
        self.data
    """
    

    class DataSchema:
        def __init__(self, label, keyword, match="left", desc=None):
            self.label = label
            self.keyword = keyword
            self.match = match #left, right and middle
        
    class DataCounter:
        def __init__(self, schemas):
            self.schemas = schemas
            
            self.dim = 1
            if type(self.schemas) == list:
                self.dim = len(schemas)
                
            self.counts = [0 for i in range(self.dim)]
        
        def count(self, row):
            if row.startswith("#"):
                return
            
            for i in range(self.dim):
                schema = self.schemas[i]
                
                if schema.match == "left":
                    if row.startswith(schema.keyword):
                        self.counts[i] += 1
                elif schema.match == "right":
                    if row.endswith(schema.keyword):
                        self.counts[i] += 1
                elif schema.match == "middle":
                    if row.find(shema.keyword)>=0:
                        self.counts[i] += 1
    UPDATE_FLAG = "- Change Status from" #green-yellow-red.cc UpdateStatus, ndn-fib-entry.cc Row90,
    INTEREST_FLAG = "> Interest for"  #ndn-consumer.cc Row210
    DATA_FLAG = "+ Respodning with ContentObject" #xiaoke.cc SinkIst, a TracedCallback
    DATA_ARRIVE = "< DATA for" #ndn-consumer.cc Row256
    NACK_ARRIVE = "< NACK for" #ndn-consumer.cc Row300
    STATS_FLAGS = [UPDATE_FLAG, INTEREST_FLAG, DATA_FLAG, DATA_ARRIVE, NACK_ARRIVE]
    
    DATA_LABELS = ["Update", "Ist", "DataNew", "DataMet", "NackMet"]
            
            
    FIB_UPDATE = DataSchema(label="Update", keyword=UPDATE_FLAG, desc="FIB entry changing status", match="left")
    IST_NEW = DataSchema(label="Ist", keyword="> Interest for", match="left", desc="Interest Generating")
    DATA_NEW = DataSchema(label="DataNew", keyword="+ Respodning with ContentObject", match="left", desc="producer gernates new content")
    DATA_GOTTEN = DataSchema(label="DataGotten", keyword="< DATA for", match="left", desc="consumer got its data")
    NACK_GOTTEN = DataSchema(label="NackGotten", keyword="< NACK for", match="left", desc="consumer got nack")
    
    SCHEMAS=[FIB_UPDATE, IST_NEW, DATA_NEW, DATA_GOTTEN, NACK_GOTTEN]
    
    def __init__(self, id, **kwargs):
        threading.Thread.__init__(self)
        Manager.__init__(self, id)
        
        self.cmd = "./waf --run \"xiaoke "
        self.trace = os.path.join(OUT, self.__class__.__name__, self.id+".trace") #trace out put
        self.output = os.path.join(OUT, self.__class__.__name__, self.id+".output") #case run console output
        
        #./waf --run "xiaoke --trace=./shock/output2-debug/Dot/DOT-ConsumerCbr-csZero-producer1-nackfalse-duration1.trace 
        #--nack=false 
        #--producerNum=1 
        #--consumerClass=ConsumerCbr 
        #--seed=3 
        #--duration=1">output2-debug/Dot/DOT-ConsumerCbr-csZero-producer1-nackfalse-duration1.dat 2>&1
        self.cmd += " --trace="
        self.cmd += self.trace
        self.cmd += " --nack="
        self.cmd +=  kwargs["nack"] if "nack" in kwargs else "true"
        self.cmd += " --producerNum="
        self.cmd += str(kwargs["producerNum"]) if "producerNum" in kwargs else "1"
        self.cmd += " --consumerClass="
        self.cmd += kwargs["consumerClass"] if "consumerClass" in kwargs else "ConsumerCbr"
        self.cmd += " --seed="
        self.cmd += str(kwargs["seed"]) if "seed" in kwargs else "3"
        self.cmd += " --duration="
        self.cmd += str(kwargs["duration"]) if "duration" in kwargs else "1"
        
        self.cmd +=  "\"";
        self.cmd += ">"+self.output+" 2>&1"  
        
        self.counter =  Case.DataCounter(Case.SCHEMAS)
        self.data = self.counter.counts
        
        
    def run(self):
        """ run the case, after running, the statstical result is held in self.data as list
        """
        self.log.info("> " +self.id+" begins")
        if not self.isRefresh and (os.path.exists(self.output) or os.path.exists(self.out)):
            if os.path.exists(self.out):
                self.read()
            else:
                self.stats()
                self.write()
            self.log.info("= "+self.out+" exists")

        else:    
            self.log.info("+ "+ "CMD: "+self.cmd)
            rst = os.system(self.cmd)
            if rst != 0:
                self.log.error("CMD: "+self.cmd+" return "+str(rst)+" (0 is OK)")
                if (os.path.exists(self.out)):
                    os.remove(self.out)
                if (os.path.exists(self.trace)):
                    os.remove(self.trace)
                if (os.path.exists(self.output)):
                    os.remove(self.output)
                
                return
            self.stats()
            self.write()
        self.log.info("< " + self.id+" ends")    
        self.log.debug("self.data = "+str(self.data))
    
    def stats(self):
        """ stats on the output of the runed case
        """
        f = open(self.output)
        
        for row in f.readlines():
            self.counter.count(row)
        
    def write(self):
        """ write the statistical data to file
        """
        if self.data:
            f = open(self.out, "w")
            f.write("#"+self.cmd+"\n")
            for v in self.data:
                f.write(str(v)+"\t")
            f.close()
        else:
            self.log.warn("! "+self.id+" data is None")
        
    
    def read(self):
        """ read the output and trace file of the case, and get the statistical data
        """
        f = open(self.out)
        for l in f.readlines():
            if l.startswith("#"):
                continue
            record = l.split()
            record = [float(i) for i in record]
        
        self.data = record
        
        self.log.info(self.id+" data="+str(self.data))


class Dot(Manager):
    """ Information of Dot on the Line
        
        self.x, self.y
    """
    
    def __init__(self, id, case, x, yindex, **kwargs):
        Manager.__init__(self, id)
        try:
            if type(yindex) == int:
                self.y = case.data[yindex] 
            elif type(yindex) == str:
                tmps = yindex.split(".")  #4.1
                assert len(tmps) == 2, "tmps="+str(tmps)
                t1 = int(tmps[0])
                t2 = int(tmps[1])
                if case.data[t2] == 0:
                    self.y = 0
                    log.warn(self.id+" gives an warnning. self.y=0")
                else:
                    self.y = case.data[t1]/float(case.data[t2])
                
            self.log.debug(self.id+" y="+str(self.y))
            self.x = x
        except IndexError:
            self.log.error(self.id+" Index out of range. yindex="+str(yindex))
            
        #self.y = case.data[yindex]
        
        
class Line(Manager):
    """ informaion of Line on the figure
    
        self.xs, self.ys
    """
    def __init__(self, id, dots, **kwargs):
        Manager.__init__(self, id)
        self.dots = dots
        self.label = kwargs["label"] if "label" in kwargs else "Line"
        self.xs = []
        self.ys = []
        for dot in dots:
            self.xs.append(dot.x)
            self.ys.append(dot.y)
        self.log.info(self.id+" xs="+str(self.xs))
        self.log.info(self.id+" ys="+str(self.ys))
        
    
        
class Figure(Manager):
    """ information of Figure
        such as title, xlabel, ylabel, etc
    """
    def __init__(self, id, lines, **kwargs):
        Manager.__init__(self, id, outType=".pdf")
        self.detail = os.path.join(OUT, self.__class__.__name__, self.id+".dat")
        
        self.lines = lines
        self.style = kwargs["style"] if "style" in kwargs else "o-"
        
        self.title = kwargs["title"] if "title" in kwargs else "Title"
        self.xlabel = kwargs["xlabel"] if "xlabel" in kwargs else "X"
        self.ylabel = kwargs["ylabel"] if "ylabel" in kwargs else "#"
        
    def draw(self):
        self.log.debug(self.id+" begin to draw ")
        plt.clf()
        for line in self.lines:
            plt.plot(line.xs, line.ys, self.style, label=line.label)
            
        plt.grid(True)
        plt.xlabel(self.xlabel);
        plt.ylabel(self.ylabel);
        plt.title(self.title)
        #location: http://matplotlib.org/api/pyplot_api.html
        plt.legend(loc="upper left")
        self.log.debug(self.id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.close()
        
        self.write()
        self.log.info(self.id+" finishes")
        
    def write(self):
        f = open(self.detail, "w")
        if self.lines == None or len(self.lines) == 0:
            return
        f.write("#Duration\t")
        
        for line in self.lines:
            f.write("%15.10s" %(line.label))
        f.write("\n")
        xs = self.lines[0].xs
        for i in range(len(xs)):
            x = xs[i]
            
            f.write("%9.8s" %(x))
            
            for line in self.lines:
                y = line.ys[i]
                f.write("%15.10s" %(y))
            
            f.write("\n")


class Paper(Manager):
    """ information of paper, which includes multiple figure
    
        to do: run latex command to generate paper directly
    """
    def __init__(self, id, figs, **kwargs):
        Manager.__init__(self, id)
        self.figs = figs



class God(Manager):
    """ God to control all the processes of the program, when to run cases, how to assign data and draw figs
    
    """
    
    def __init__(self):
        """ God will run all the cases needed
        
        """
        Manager.__init__(self, id="GOD")
        self.t0 = time.time()
        self.paperid = None
        self.t1 = None
        
        dic = {}
        cases = {}
        for nack in ["true", "false"]:
            dic["nack"] = nack
            for duration in [1, 2, 3]:
                dic["duration"] = duration
                id = "Case" + self.parseId(dic)
                
                case = Case(id=id, **dic)
                case.start()
                cases[id] = case
        
        for k, case in cases.items():
            if case.isAlive():
                case.join()
                
            #self.log.info(case.id+" ends")

        self.log.info("Cases Run end!")
        self.cases = cases
    
    
    def say(self):
        """ God creates the universe, "God says ..."
        
        """
        figs = []
        
        for yindex in [1, 4, "4.1"]:
            dic = {}
            figid ="Fig-"
            
            if type(yindex) == int:
                figid += Case.DATA_LABELS[yindex]
            elif type(yindex) == str:
                tmps = yindex.split(".")
                assert len(tmps) == 2, "tmps="+str(tmps)
                t1 = int(tmps[0])
                t2 = int(tmps[1])
                figid += Case.DATA_LABELS[t1] + "=" + Case.DATA_LABELS[t2]
                
            lines = []
            
            for nack in ["true", "false"]:
                dic["nack"] = nack
                lineid = "Line"+self.parseId(dic)
                
                dots = []
                MAX_DURATION = 3
                for duration in range(1, MAX_DURATION+1):
                    dic["duration"] = duration
                    atts = self.parseId(dic)
                    id = "Case" + atts
                    case = self.cases[id]
                    
                    dot = Dot(id="Dot"+atts, case=case, x=duration, yindex=yindex)
                    dots.append(dot)
                if nack == "true":
                    linelabel = "NDN"
                else:
                    linelabel = "IP"
                line = Line(id=lineid, dots=dots, label=linelabel)
                lines.append(line)
            fig = Figure(id=figid, lines=lines)
            fig.draw()   
            figs.append(fig)
        
        paperid = "paper-cdn"
        paper = Paper(id=paperid, figs=figs)
        self.paperid = paperid
        
        self.log.info("Paper Run end!")

    def rest(self):
        """ God notifies people it create everything and has a rest
        
        """
        self.t1 = time.time()
        data = self.paperid+" ends on "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+ \
            " after running for "+str(self.t1 - self.t0)+" seconds"
        self.log.info(data)
        if HOSTOS.startswith("Darwin"):
            #pass
            return
        from smtplib import SMTP
        TO = ["shock.jiang@gmail.com"]
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
    
    
if __name__=="__main__":
    god = God()
    god.say()
    god.rest()

 
