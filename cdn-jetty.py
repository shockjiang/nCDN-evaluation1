# -*- coding: utf-8 -*-
import sys
import platform
"""the platform of the system"""
HOSTOS = platform.system() 
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams["font.size"] = 21
matplotlib.rcParams["xtick.labelsize"] = 18
matplotlib.rcParams["lines.linewidth"] = 3.0
matplotlib.rcParams["pdf.fonttype"] = 42
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
#************** Global Settings ****************************************

IS_MT = True #Multi Threads Run

IS_REFRESH = True
IS_REFRESH = False

MAX_THREADN = 24

OUT = "output"

DEBUG = False
if HOSTOS.startswith("Darwin"):
    DEBUG = True
    MAX_THREADN = 2
DEBUG = False

LOG_LEVEL = logging.DEBUG

ALLOWED_CLASS_LI = None #default is None, which means all logger should be allowed, else give a list of allowed logger; but ["Figure"] is OK
#------------------------------

ITEM = "jetty"
PAPER = "cdn-over-ip"
SCRIPT = "cdn-jetty"

#************** Global Settings ****************************************


class ClassFilter(logging.Filter):
    """filter the log information by class name
    """
    def filter(self, record):
        if ALLOWED_CLASS_LI == None:
            return True
        
        if record.name in ALLOWED_CLASS_LI:
            return True
        else:
            return False

log = logging.getLogger() #root logger

format = logging.Formatter('%(levelname)5s:%(name)6s:%(lineno)3d: %(message)s')   
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#http://docs.python.org/2/library/self.logging.html#self.logrecord-attributes
#logging.basicConfig(format=format, datefmt='%m/%d/%Y %I:%M:%S %p')

fh = logging.FileHandler(PAPER+"-"+ITEM+".log", mode="w")
fh.setFormatter(format)

sh = logging.StreamHandler() #console
sh.setFormatter(format)

f = ClassFilter()
sh.addFilter(f)


log.addHandler(sh)
log.addHandler(fh)

    
class Manager:
    """ Super Class of all the manager class, name as an example, Case, Dot, Line, Figure and Paper"""
    def __init__(self, Id, **kwargs): #kwargs["outType"]
        self.Id = Id
        #self.daemon = True
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
        """ construct the Id from attributes held in dic, attributes, such us id, trace are ignored
        
        """
        Id = ""
        keys = dic.keys()
        keys.sort()
        for k in keys:
            v = dic[k]
            if k.startswith("consumerClass"):
                if isinstance(v, list):
                    if len(v) >1:
                        Id += "-"+str(v[0])+"-"+str(v[-1])
                    else:
                        Id += "-" + str(v[0])
                else:
                    Id += "-"+str(v)
            elif k.startswith("id") or k.startswith("trace"):
                continue
            else:
                Id += "-" + str(k)            
                if isinstance(v, list):
                    if len(v) >1:
                        Id += str(v[0])+"-"+str(v[-1])
                    else:
                        Id += str(v[0])
                else:
                    Id += str(v)
                    
        if Id.startswith("-"):
            Id = Id[1:]
        Id = Id.replace(".", "")
        return Id
    
    def notify(self, way="email", **msg): #way="email"|"print"
        '''notify users about running result, currently there are two ways: email, print
        '''
        self.t1 = time.time()
        data = PAPER+": " +ITEM +" ends "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+ " TotalN=" + str(Case.TotalN) +" SuccessN="+str(Case.SuccessN)+ " ExistingN="+str(Case.ExistingN) +" FailN="+str(Case.FailN)
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
        mailh = ["From: "+FROM, "To: shock.jiang@gmail.com", "Subject: " +data]
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
    def __init__(self, Id, cases, headers): #headers = ["rowN", "latency", "hop"]
        Manager.__init__(self, Id)
        self.cases = cases
        self.headers = headers
        self.data = {}  #data keyed by case.Id        
    
    def get(self, caseId, key):
        if not caseId in self.data:
            self.log.warn(caseId+" is not in the caseId set")
            return -2
        if not key in self.headers:
            self.log.warn(key + "is not in the headers")
            return -2
        
        index = self.headers.index(key)
        
        if isinstance(self.data[caseId][0], list): #self.data[caseId]= [['time', 'value'],[1,'a'],[2,'b']]
            li = []                                  #                [[1,100], [2, 150], [3, 101]]  ["latency", "count"] 
            for liv in self.data[caseId]:
                li.append(liv[index])
            return li
        return self.data[caseId][index]  #self.data[caseId] = ['freq', 'value']
    
    
    def read(self):
        self.log.info(self.out+" is there")
        fin = open(self.out)
        for line in fin.readlines():
            line = line.strip()
            if line.startswith("#headers:"):
                cols = line[len("#headers:"):].strip().split()
                if self.headers != cols:
                    self.log.warn("stat file headers are different: self.headers="+str(self.headers)+" InFileHeaders="+str(cols))
            elif line.startswith("#command:"):
                pass    
            elif line != "":
                cols = line.split()
                caseId = cols[0]
                
                li = [float(cols[i]) for i in range(1, len(cols))]
                if caseId in self.data:
                    if isinstance(self.data[caseId][0], list):
                        self.data[caseId].append(li)
                    else:
                        self.data[caseId] = [self.data[caseId]]
                else:
                    self.data[caseId] = li
                self.log.debug("column:" + line)
        self.log.info(self.Id+" get data from file")     
       
    def write(self):
        fout = open(self.out, "w") #write the data to result file
        line = ""
        for header in self.headers:
            line += "\t" + header
        line.strip()
        line = "#headers: " + line+"\n"
        fout.write(line)
        #line = "#command: " + case.cmd + "\n"
        #fout.write(line)
        for caseId in self.data:
            li = self.data[caseId]
            if isinstance(li[0], list):
                for il in li:
                    line = caseId
                    for col in il:
                        line += "\t" + str(col)
                    line += "\n"
                    self.log.debug("write data: "+str(line)) 
                    fout.write(line)    
            else:
                line = caseId
                for col in li:
                    line += "\t" + str(col)
                line += "\n"
                self.log.debug("write data: "+str(line)) 
                fout.write(line)
        fout.flush()
        fout.close()
        self.log.info(self.Id+" write data to file")
        self.log.debug("output file is "+self.out)
        
    def stat(self):
        self.log.info("> Stat: "+self.Id+" begins")
        if not self.isRefresh and os.path.exists(self.out):#read data from existing result
            self.read()
        else:   #read and stat the case.out
            self.obtain() #get data from raw output
            self.write()
        self.log.info("< Stat: "+self.Id+" ends")
    
    #------------- to be overloade ----------------------
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
                
                for line in fin.readlines():
                    line = line.strip()
                    if line == "" or line.startswith("#") or line.startswith("Time"):
                        continue
                    cols = line.split()
                    kind = cols[4]
                    if kind == "LastDelay":
                        continue
                    
                    latency = round(float(cols[6])/10000)
                    
                    if latency in distN:
                        distN[latency] += 1
                    else:
                        distN[latency] = 1
                    
                fin.close()
                #self.data[case.Id] = [rowN, latency/rowN, hop/rowN]
                self.data[case.Id] = []
                keys = distN.keys()
                keys.sort()
                sum = 0
                for key in keys:
                    sum += distN[key]
                    self.data[case.Id].append([key, sum])
                for li in self.data[case.Id]:
                    li[1] = li[1]/float(sum)
                    
                self.log.debug(caseId+": "+str(self.data[case.Id]))
    #------------- to be overloade ----------------------            
                
class Case(Manager, threading.Thread):
    """ run program/simulation case, trace file is printed to self.trace, console msg is printed to self.output
        and self.out is stored the statstical information
        
        self.data
    """
    TotalN = 0
    LiveN = 0  #LiveN < MAX_THREADN
    SuccessN = 0
    ExistingN = 0
    FailN = 0  #TotalN = SuccessN + ExistingN + FailN
    
    def __init__(self, Id, param={}, **kwargs):
        threading.Thread.__init__(self)
        Manager.__init__(self, Id)
        
        self.setDaemon(False)
        self.result = None
        self.trace = os.path.join(OUT, self.__class__.__name__, "latency-"+self.Id+".txt")
        
        self.cmd = "./waf --run \'" +SCRIPT
        self.param = param
        
        for key, val in param.items():
            self.cmd += " --"+key+"="+str(val) 
        self.cmd += " --id="+str(self.Id)
        self.cmd +=  "\'";
        self.cmd += ">"+self.out+" 2>&1"  
   
    def start(self):
        Case.LiveN += 1
        threading.Thread.start(self)

    def run(self):
        """ run the case, after running, the statstical result is held in self.data as list
        """
        #Case.LiveN += 1
        self.log.info("> " +self.Id+" begins TotalN/LiveN/SuccessN/ExistingN/FailN=%d/%d/%d/%d/%d" \
                      %(Case.TotalN, Case.LiveN, Case.SuccessN, Case.ExistingN, Case.FailN))
        if (not self.isRefresh) and os.path.exists(self.out):
            Case.ExistingN += 1
            self.result = True
            pass
        else:    
            self.log.info("+ "+ "CMD: "+self.cmd)
            args = shlex.split(self.cmd)
                
            p = os.system(self.cmd)
            if p == 0:
                Case.SuccessN += 1
                self.result = True
                self.log.info("- "+ "CMD: "+self.cmd)
            else:
                self.log.error(self.cmd+" return error" )
                if os.path.exists(self.out):
                    os.remove(self.out)
                Case.FailN += 1
                self.result = False
                self.log.warn("! "+ "CMD: "+self.cmd)
                
        Case.LiveN -= 1
        self.log.info("< " +self.Id+" ends TotalN/LiveN/SuccessN/ExistingN/FailN=%d/%d/%d/%d/%d" \
                      %(Case.TotalN, Case.LiveN, Case.SuccessN, Case.ExistingN, Case.FailN))


            
class Dot():        
    def __init__(self, x, y):
        self.x = x
        self.y = y  
        
class Line(Manager):
    def __init__(self, dots=None, xs=None, ys=None, plt={}, **kwargs):
        #for dot in dots:
        if dots != None:
            dotN = len(dots)
            self.xs = [dots[i].x for i in range(dotN)]
            self.ys = [dots[i].y for i in range(dotN)]
        else:
            dotN = len(xs)
            self.xs = xs
            self.ys = ys
            
        self.plt = plt
        
class Figure(Manager):
    """ information of Figure
        such as title, xlabel, ylabel, etc
    """
    def __init__(self, Id, lines, canvas={}, **kwargs):
        Manager.__init__(self, Id, outType=".png")
        self.detail = os.path.join(OUT, self.__class__.__name__, self.Id+".dat")
        self.lines = lines
        self.canvas = canvas   
        self.kwargs = kwargs
        self.out2 = os.path.join(OUT, self.__class__.__name__, self.Id+".pdf")
        
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

        plt.grid(True)        
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.xlim(xmax=self.canvas.pop("xmax", None))
        plt.legend(**self.canvas)
        
        
        if HOSTOS.startswith("Darwin"):
            plt.savefig(self.out)
            plt.savefig(self.out2)
            self.log.debug(self.Id+" fig save to "+self.out)
        plt.close()
        
        self.log.info(self.Id+" ends")
    
    
    def bar(self):
        self.log.debug(self.Id+" begin to draw ")
        plt.clf()
        
        plt.xticks([i+0.3 for i in range(6)], ("Transmission Time", "Hops", "Data Recieved"))
        self.bars = []
        Width = self.canvas.pop("width", 0.2)
        i = 0
        for line in self.lines:
            xs = [j+Width * i for j in line.xs]
            print "line.xs=",xs
            print "line.ys=", line.ys
            #print "xs=",xs       
            bar = plt.bar(left=xs, height=line.ys, width=Width, bottom=0, **line.plt)
            self.bars.append(bar)
            i += 1
        #plt.legend( (p1[0], p2[0]), ('Men', 'Women') )
        
        plt.legend((self.bars[i][0] for i in range(len(self.lines))), (self.lines[i].plt["label"] for i in range(len(self.lines))))
        #for bar in self.bars:
        
        xs = [Width * len(self.lines)/2 + j for j in line.xs]
        #print xs
        plt.xticks(xs, line.xs)
                
        plt.grid(True)
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.legend(**self.canvas)
        plt.title(self.canvas.pop("title", " "))
        
        plt.legend(**self.canvas)
        if HOSTOS.startswith("Darwin"):
            plt.savefig(self.out)
            plt.savefig(self.out2)
            self.log.debug(self.Id+" fig save to "+self.out)
        plt.close()
        
        self.log.info(self.Id+" finishes")

class God(Manager):
    """ God to control all the processes of the program, when to run cases, how to assign data and draw figs
    
    """
 
    IsError = False
    def run(self):
        cases = self.cases

        self.log.info("> "+ self.Id + " run begins")
        Case.TotalN = len(cases)
        if not self.isRefresh and (not self.stat.isRefresh) and os.path.exists(self.stat.out):
            Case.ExistingN = Case.TotalN
            pass
        else:
            keys = cases.keys()
            if len(keys)<= MAX_THREADN:
                for Id, case in cases.items():
                    case.start()
                    
                for Id, case in cases.items():
                    if case.isAlive():
                        case.join()
            else:
                aliveThds = []
                for j in range(MAX_THREADN):
                    key = keys[j]
                    case = cases[key]
                    aliveThds.append(case)
                    case.start()
                    
                next = MAX_THREADN
                
                while next < len(keys):
                    endN = 0
                    endThds = []
                    for case in aliveThds: 
                        if case.isAlive() == False:
                            endN += 1
                            endThds.append(case)
                            if case.result == False:
                                God.IsError = True
                                break
                    if God.IsError:
                        break
                            
                    for case in endThds:
                        aliveThds.remove(case)
                            
                    for i in range(endN):
                        if next >= len(keys):
                            break
                        key = keys[next]
                        case = cases[key]
                        aliveThds.append(case)
                        case.start()
                        
                        next += 1
                        
                for case in aliveThds:
                    if case.isAlive():
                        case.join()
                    else:
                        if case.result == False:
                            God.IsError = True
                            break
    
        self.log.info("< "+ self.Id + " run ends with IsError="+str(God.IsError) +\
                      " TotalN="+str(len(cases))+" SuccessN="+str(Case.SuccessN)+ " ExsitingN="+str(Case.ExistingN) +" FailN="+str(Case.FailN))
   
       
    def __init__(self, paper):
        """ God will run all the cases needed
        
        """
        
        self.t0 = time.time()
        global OUT
        OUT = os.path.join(OUT, paper)
        Manager.__init__(self, Id="GOD")
        
#         dir = os.path.split(os.path.realpath(__file__))[0]
#         os.chdir(dir)
#         dir = os.path.split(os.path.realpath(__file__))[0]
#         os.chdir(dir)

        #------------- to be overloade ----------------------            
        self.cases = {}
        
        Min_Freq = 40
        #Min_Freq = 100
        Max_Freq = 200
        Step = 10
        self.freqs = range(Min_Freq, Max_Freq+Step, Step)
        #self.freqs = [100, 110]
        self.zipfs = [0.99, 0.92, 1.04]
        self.zipfs = [0.99]
        self.duration = 30
        self.producerN = [5, 10, 15, 18, 20, 25, 30]
        self.producerN = [5, 10, 15, 18, 19, 20, 25, 30]
        self.producerN = [15]
        self.seeds = range(3, 9)
        self.seeds = [3]
        self.multicast = ["false", "true"]
        self.consumerClasses = ["CDNConsumer", "CDNIPConsumer"]
        #self.consumerClasses = ["CDNConsumer"]
            
        if DEBUG:
            self.freqs = [100]
            self.consumerClasses = ["CDNIPConsumer", "CDNConsumer"]
            self.seeds = [3]
            self.zipfs = [0.99]
            self.producerN = [15]
            self.duration = 2
        
             
        self.dic = {}
        self.dic["freqs"] = self.freqs
        self.dic["consumerClasses"] = self.consumerClasses
        self.dic["RngRun"] = self.seeds
        self.dic["producerN"] = self.producerN
        self.dic["multicast"] = self.multicast
        self.dic["zipfs"] = self.zipfs
        self.dic["item"] = ITEM
        self.dic["duration"] = self.duration
        
        headers = ["latency", "count"]
        self.stat = Stat(Id=self.parseId(self.dic), cases=self.cases, headers=headers)
        
    
    def setup(self):
        cases = self.cases
        self.log.info("> "+ self.Id + " setup begins")
        cases = self.cases
        for freq in self.freqs:
            dic = {}
            dic["freq"] = freq
            for consumer in self.consumerClasses:
                dic["consumerClass"] = consumer
                for seed in self.seeds:
                    dic["RngRun"] = seed
                    for producerN in self.producerN:
                        dic["producerN"] = producerN
                        for multicast in self.multicast:
                            dic["multicast"] = multicast
                            if consumer == "CDNConsumer" and multicast == "false":
                                continue
                            if consumer == "CDNIPConsumer" and multicast == "true":
                                continue
                            for zipfs in self.zipfs:
                                dic["zipfs"] = zipfs
                                
                                dic["duration"] = self.duration
                                dic["item"] = ITEM
                                Id = self.parseId(dic)
                                case = Case(Id=Id, param=dic, **dic)
                                cases[Id] = case
            self.log.info("> "+ self.Id + " setup ends")
    
    def create(self, func):
        self.stat.stat()
        
        dic = {}        
        dic["RngRun"] = 3
        dic["producerN"] = 15
        dic["zipfs"] = 0.99
        dic["duration"] = self.duration
        dic["item"] = ITEM
        func(dic)
        
    def world(self, dic={}):
        lines = []
        lines2 = []
         
        for multicast in self.multicast:
            dic["multicast"] = multicast
            for consumerClass in self.consumerClasses: 
                dic["consumerClass"] = consumerClass
                print consumerClass, multicast
                if consumerClass == "CDNIPConsumer" and multicast == "true":
                    continue
                if consumerClass == "CDNConsumer" and multicast == "false":
                    continue
                
                dots = []
                dots2 = []
                for producerN in self.producerN:
                    dic["producerN"] = producerN
                
                    for freq in [150]:#self.freqs:
                        dic["freq"] = freq  
                        Id = self.parseId(dic)
                        
                        if consumerClass == "CDNConsumer":
                           label = "nCDN"
                           color = "y"
                        else:
                            label = "Traditional CDN"
                            color = "b"
                        #label += ": Frequency="+str(freq)
                        plt = {}
                        plt["color"] = color
                        plt["label"] = label
                        xs = [x/10.0 for x in self.stat.get(Id, "latency")]
                        line = Line(xs=xs, ys=self.stat.get(Id, "count"), plt=plt)
                        lines.append(line)
        canvas = {}
        canvas["xlabel"] = "Latency (x$10^2$ MS)"
        canvas["ylabel"] = "CDF of Requests #"
        canvas["loc"] = "lower right"
        canvas["xmax"] = 10
        fig = Figure(Id=ITEM, lines = lines, canvas=canvas)
        fig.line()
        #fig.bar()
#         
#         canvas["xlabel"] = "Frequency of Request (x10)"
#         canvas["ylabel"] = "Latency (US)"
#         canvas["loc"] = "upper left"
#         fig = Figure(Id=ITEM, lines = lines2, canvas=canvas)
#         #fig.line()
#         fig.bar()

    

if __name__=="__main__":
    #cmd = "./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'>output/Case/ist-set.output 2>&1"
    #print os.system(cmd)
    #global DEBUG    
    for i in range(1, len(sys.argv)):
        av = sys.argv[i]
        if av == "--debug":
            DEBUG = True
        elif av == "--nodebug":
            DEBUG = False
            
    god = God(paper=PAPER)
    god.setup()
    try:
        god.run()
    except IOError as e:
        self.log.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        
    else:
        god.create(god.world)
        if God.IsError:
            os.remove(god.stat.out)
    finally:
        if (not DEBUG) and (not HOSTOS.startswith("Darwin")):
            god.notify(way="email")
        else:
            god.notify(way="print")

