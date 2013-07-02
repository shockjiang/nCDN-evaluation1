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
from script.cmp import cmp
import logging
import threading
import shlex, subprocess
import signal 

IS_MT = True #Multi Threads Run

IS_REFRESH = True
IS_REFRESH = False

OUT = "output"

DEBUG = False
if HOSTOS.startswith("Darwin"):
    DEBUG = True

LOG_LEVEL = logging.DEBUG


#--------------Global Settings----------------

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
    def __init__(self, Id, **kwargs):
        self.Id = Id
        self.daemon = True
        self.isMT = IS_MT
        self.isRefresh = IS_REFRESH
        self.t0 = time.time()
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(LOG_LEVEL)
        
        
        self.out = os.path.join(OUT, self.__class__.__name__)
        if not os.path.exists(self.out):
            os.makedirs(self.out)
        outType = ".txt"
        if "outType" in kwargs:
            outType = kwargs["outType"]
        if not outType.startswith("."):
            outType = "." + outType
        self.out = os.path.join(self.out, self.Id+outType)
    
    
    
    def parseId(self, dic):
        """ get the Id from attributes held in dic
        
        """
        Id = ""
        keys = dic.keys()
        keys.sort()
        for k in keys:
            v = dic[k]
            if k == "consumerClass":
                pass
            else:
                Id += "-" + str(k)
            if isinstance(v, list):
                Id += str(v[0])+"-"+str(v[-1])
            else:
                Id += str(v)
        if Id.startswith("-"):
            Id = Id[1:]
        return Id
    
    def notify(self, way="email", **msg):
        self.t1 = time.time()
        data = self.Id+" ends on "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+ \
            " after running for "+str(self.t1 - self.t0)+" seconds"
        data = msg.get("data", data)
        
        self.log.info(data)
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
    def __init__(self, Id, cases):
        Manager.__init__(self, Id)
        self.cases = cases
        self.headers = ["caseId", "unsatisfiedRequestN", "dropedPacketN"]
        self.data = {}  #data keyed by case.Id        
        
        
    #### to be overloaded    
    def stat(self):
        if not self.isRefresh and os.path.exists(self.out):
            self.log.info(self.out+" is there")
            fin = open(self.out)
            for line in fin.readlines():
                line = line.strip()
                if line.startswith("#"):
                    cols = line[1:].split()
                    if self.headers != cols:
                        self.log.warn("stat file headers are different: self.headers="+str(self.headers)+" InFileHeaders="+str(cols))
                    
                elif line != "":
                    cols = line.split()
                    caseId = cols[0]
                    
                    li = [int(cols[i]) for i in range(1, len(cols))]
                    self.data[caseId] = li
                    self.log.debug("column:" + line)
            self.log.info(self.Id+" get data from file")     
              
        else:
            for caseId in self.cases:
                case = self.cases[caseId]
                unsatisfiedRequestN = 0
                dropedPacketN = 0
                fin = open(case.out)
                for line in fin.readlines():
                    line = line.strip()
                    if line == "" or line.startswith("#"):
                        continue
                    if line.startswith("trace") and line.find("timeout") != -1:
                        unsatisfiedRequest += 1
                    elif line.startswith("race: Drop Packet"):
                        dropedPacketN += 1
                fin.close()
                self.data[case.Id] = [unsatisfiedRequestN, dropedPacketN]
                self.log.debug(caseId+": "+str(self.data[case.Id]))

            fout = open(self.out, "w")
            line = ""
            for header in self.headers:
                line += "\t" + header
            line.strip()
            line = "#" + line+"\n"
            fout.write(line)
            for caseId in self.data:
                li = self.data[caseId]
                line = caseId
                for col in li:
                    line += "\t" + str(col)
                line += "\n"
                self.log.debug(self.Id+" write data: "+str(line)) 
                fout.write(line)
            
            fout.close()
            self.log.info(self.Id+" write data to file")

class Case(Manager, threading.Thread):
    """ run program/simulation case, trace file is printed to self.trace, console msg is printed to self.output
        and self.out is stored the statstical information
        
        self.data
    """    
    LiveN = 0
    SuccessN = 0
    FailN = 0
    def __init__(self, Id, param={}, **kwargs):
        threading.Thread.__init__(self)
        Manager.__init__(self, Id)
        
        self.cmd = "./waf --run \'cdn"
        self.param = param
        
        for key, val in param.items():
            self.cmd += " --"+key+"="+str(val) 

        self.cmd +=  "\'";
        self.cmd += ">"+self.out+" 2>&1"  
   
    def start(self):
        Case.LiveN += 1
        threading.Thread.start(self)

    def run(self):
        """ run the case, after running, the statstical result is held in self.data as list
        """
        #Case.LiveN += 1
        self.log.info("> " +self.Id+" begins")
        if (not self.isRefresh) and os.path.exists(self.out):
            Case.SuccessN += 1
            pass
        else:    
            self.log.info("+ "+ "CMD: "+self.cmd)
            args = shlex.split(self.cmd)
                
            p = os.system(self.cmd)
            Case.SuccessN += 1
            if p != 0:
                self.log.error(self.cmd+" return error" )
                if os.path.exists(self.out):
                    os.remove(self.out)
                Case.FailN += 1
            
#             
#             try:
#                 p = subprocess.check_output(args, shell=True)
#                 with open(self.out, 'w') as f:
#                     f.write(p)
#                     f.close()
#                 Case.SuccessN += 1
#             #if p != 0:
#             except subprocess.CalledProcessError as ex:
#                 self.log.error(self.cmd+":" +ex)
#                 if os.path.exists(self.out):
#                     os.remove(self.out)
#                 Case.FailN += 1
                    
        Case.LiveN -= 1
        self.log.info("< "+str(self.Id)+" ends. Live Case Nun ="+str(Case.LiveN))

            
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
    def __init__(self, Id, lines, canvas={}, **kwargs):
        Manager.__init__(self, Id, outType=".pdf")
        self.detail = os.path.join(OUT, self.__class__.__name__, self.Id+".dat")
        self.lines = lines
        self.canvas = canvas   
        self.kwargs = kwargs
        
    def line(self):
        self.log.debug(self.Id+" begin to draw ")
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
        
        
        plt.grId(True)

        self.log.debug(self.Id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.close()
        
        self.log.info(self.Id+" ends")
    
    
    def bar(self):
        self.log.debug(self.Id+" begin to draw ")
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
            bar = plt.bar(left=line.xs, height=line.ys, wIdth=0.3, bottom=0, **line.plt)
            self.bars.append(bar)
            
        #plt.legend( (p1[0], p2[0]), ('Men', 'Women') )
        
        plt.legend((self.bars[i][0] for i in range(len(self.lines))), (self.lines[i].plt["label"] for i in range(len(self.lines))))
        #for bar in self.bars:

                
        plt.grId(True)
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
        self.log.debug(self.Id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.close()
        
        self.log.info(self.Id+" finishes")
    

# class Paper(Manager):
#     """ information of paper, which includes multiple figure
#     
#         to do: run latex command to generate paper directly
#     """
#     def __init__(self, Id, figs, **kwargs):
#         Manager.__init__(self, Id)
#         self.figs = figs
#         OUT = os.path.join(OUT, Id)



class God(Manager):
    """ God to control all the processes of the program, when to run cases, how to assign data and draw figs
    
    """
    
    def __init__(self, paper):
        """ God will run all the cases needed
        
        """
        Manager.__init__(self, Id="GOD")
        self.t0 = time.time()
        global OUT
        OUT = os.path.join(OUT, paper)
        
#         dir = os.path.split(os.path.realpath(__file__))[0]
#         os.chdir(dir)
        self.cases = {}
        self.freqs = [120, 130]
        Min_Freq = 200
        Max_Freq = 500
        self.freqs = range(Min_Freq, Max_Freq, 100)
        self.consumers = ["CDNConsumer"]
     
        
    def setup(self):
        dic = {}
        dic["freqs"] = self.freqs
        dic["consumers"] = self.consumers
        
      
        cases = self.cases
        for freq in self.freqs:
            dic = {}
            dic["freq"] = freq
            for consumer in self.consumers:
                dic["consumerClass"] = consumer
                
                Id = self.parseId(dic)
                case = Case(Id=Id, param=dic, **dic)
                cases[Id] = case
                
        self.stat = Stat(Id=self.parseId(dic), cases=self.cases)
        
        if not self.isRefresh and (not self.stat.isRefresh) and os.path.exists(self.stat.out):
            pass
        else:
            for Id, case in cases.items():
                case.start()
                
            for Id, case in cases.items():
                if case.isAlive():
                    case.join()
        
        self.stat.stat()
        
    def create(self):
        pass
        
def stop():
    os.system("pkill Python")
    
if __name__=="__main__":
    #cmd = "./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'>output/Case/ist-set.output 2>&1"
    #print os.system(cmd)
    god = God(paper="cdn-over-ip")
    god.setup()
    god.create()
    if not DEBUG:
        god.notify(way="email")
    signal.signal(signal.SIGINT,stop)         