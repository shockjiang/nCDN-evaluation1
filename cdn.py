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

MAX_THREADN = 24

OUT = "output"

DEBUG = False
if HOSTOS.startswith("Darwin"):
    DEBUG = True
    MAX_THREADN = 2
DEBUG = False

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
        """ get the Id from attributes held in dic
        
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
        mailh = ["From: "+FROM, "To: shock.jiang@gmail.com", "Subject: Paper ends "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+\
                    "TotalN=" + str(Case.TotalN) +" SuccessN="+str(Case.SuccessN)+ " ExistingN="+str(Case.ExistingN) +" FailN="+str(Case.FailN)]
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
    def __init__(self, Id, cases, headers=["caseId", "unsatisfiedRequestN", "dropedPacketN", "nackedPacketN"]):
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
        index = self.headers.index(key) - 1
        return self.data[caseId][index]
    
    #### to be overloaded    
    def stat(self):
        self.log.info("> Stat: "+self.Id+" begins")
            
        if not self.isRefresh and os.path.exists(self.out):#read data from existing result
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
                    
                    li = [int(cols[i]) for i in range(1, len(cols))]
                    self.data[caseId] = li
                    self.log.debug("column:" + line)
            self.log.info(self.Id+" get data from file")     
              
        else:   #read and stat the case.out
            self.log.info("headers: "+ str(self.headers)) 
            for caseId in self.cases:
                case = self.cases[caseId]
                unsatisfiedRequestN = 0
                dropedPacketN = 0
                nackedPacketN = 0
                
                if (case.result == False):
                    unsatisfiedRequestN = -1
                    dropedPacketN = -1
                    nackedPacket = -1
                else:
                    fin = open(case.out)
                    for line in fin.readlines():
                        line = line.strip()
                        if line == "" or line.startswith("#"):
                            continue
                        if line.startswith("trace") and line.find("timeout") != -1:
                            unsatisfiedRequestN += 1
                        elif line.startswith("trace: Drop Packet"):
                            dropedPacketN += 1
                        elif line.startswith("trace") and line.endswith("nack back"):
                            nackedPacketN += 1
                    fin.close()
                
                self.data[case.Id] = [unsatisfiedRequestN, dropedPacketN, nackedPacketN]
                
                self.log.debug(caseId+": "+str(self.data[case.Id]))

            fout = open(self.out, "w") #write the data to result file
            line = ""
            for header in self.headers:
                line += "\t" + header
            line.strip()
            line = "#headers: " + line+"\n"
            fout.write(line)
            line = "#command: " + case.cmd + "\n"
            fout.write(line)
            for caseId in self.data:
                li = self.data[caseId]
                line = caseId
                for col in li:
                    line += "\t" + str(col)
                line += "\n"
                self.log.debug("write data: "+str(line)) 
                fout.write(line)
            
            fout.close()
            self.log.info(self.Id+" write data to file")
        self.log.info("< Stat: "+self.Id+" ends")
        
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
        self.log.info("< " +self.Id+" ends TotalN/LiveN/SuccessN/ExistingN/FailN=%d/%d/%d/%d/%d" \
                      %(Case.TotalN, Case.LiveN, Case.SuccessN, Case.ExistingN, Case.FailN))
        #self.log.info("< "+str(self.Id)+" ends. Live Case Nun ="+str(Case.LiveN))

            
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
        
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.legend(**self.canvas)
        
        
        plt.grid(True)

        self.log.debug(self.Id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.savefig(self.out2)
        plt.close()
        
        self.log.info(self.Id+" ends")
    
    
    def bar(self):
        self.log.debug(self.Id+" begin to draw ")
        plt.clf()
        
        plt.xticks([i+0.3 for i in range(6)], ("Transmission Time", "Hops", "Data Recieved"))
        self.bars = []
        Width = 1
        i = 0
        for line in self.lines:
#             if hasattr(line, "label") and line.label != None:
#                 plt.plot(line.xs, line.ys, self.style, label=line.label)
#             else:
#                 plt.plot(line.xs, line.ys, self.style)
#        
            xs = [j+Width * i for j in line.xs]
            print "line.xs=",xs
            print "line.ys=", line.ys
            print "xs=",xs       
            bar = plt.bar(left=xs, height=line.ys, width=Width, bottom=0, **line.plt)
            self.bars.append(bar)
            i += 1
        #plt.legend( (p1[0], p2[0]), ('Men', 'Women') )
        
        plt.legend((self.bars[i][0] for i in range(len(self.lines))), (self.lines[i].plt["label"] for i in range(len(self.lines))))
        #for bar in self.bars:
        
        xs = [Width * len(self.lines)/2 + j for j in line.xs]
        print xs
        plt.xticks(xs, line.xs)
                
        plt.grid(True)
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.legend(**self.canvas)
        plt.title(self.canvas.pop("title", " "))
        
#         if self.ymin != None:
#             plt.ylim(ymin=self.ymin)
#         if self.ymax != None:
#             plt.ylim(ymax=self.ymax)
        #location: http://matplotlib.org/api/pyplot_api.html
        plt.legend(**self.canvas)
        self.log.debug(self.Id+" fig save to "+self.out) 
        plt.savefig(self.out)
        plt.savefig(self.out2)
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
        
        self.t0 = time.time()
        global OUT
        OUT = os.path.join(OUT, paper)
        Manager.__init__(self, Id="GOD")
        
#         dir = os.path.split(os.path.realpath(__file__))[0]
#         os.chdir(dir)
        self.cases = {}
        
        Min_Freq = 40
        #Min_Freq = 100
        Max_Freq = 250
        Step = 10
        self.freqs = range(Min_Freq, Max_Freq+Step, Step)
        self.zipfs = [0.99, 0.92, 1.04]
        self.zipfs = [0.99]
        self.duration = 300
        self.producerN = [5, 10, 15, 18, 20, 25, 30]
        self.producerN = [5, 10, 15, 18, 19, 20, 21, 25, 30]
        self.producerN = [5, 10, 15, 18, 21, 25, 30]
        #self.producerN = [10, 12, 15]
        self.seeds = range(3, 9)
        self.seeds = [3]
        self.multicast = ["false", "true"]
        self.consumerClasses = ["CDNConsumer", "CDNIPConsumer"]
        #self.consumerClasses = ["CDNConsumer"]
            
        if DEBUG:
            self.freqs = [100]
            self.consumerClasses = ["CDNIPConsumer", "CDNConsumer"]
            self.seeds = [3]
            self.zipfs = [0.92]
            self.producerN = [10]
            self.duration = 2
        
             
        self.dic = {}
        
        
        self.dic["freqs"] = self.freqs
        self.dic["consumerClasses"] = self.consumerClasses
        self.dic["RngRun"] = self.seeds
        self.dic["producerN"] = self.producerN
        self.dic["multicast"] = self.multicast
        self.dic["zipfs"] = self.zipfs
        self.dic["duration"] = self.duration
        self.dic["item"] = "scalability" 
        
    def setup(self):
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
                                Id = self.parseId(dic)
                                case = Case(Id=Id, param=dic, **dic)
                                cases[Id] = case
        
        self.stat = Stat(Id=self.parseId(self.dic), cases=self.cases)
        #self.stat.isRefresh = True

        #self.log.info("Stat: "+self.stat.Id+" begin")
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
        
        self.stat.stat()
        self.log.info("< "+ self.Id + " setup ends " +\
                      "TotalN="+str(len(cases))+" SuccessN="+str(Case.SuccessN)+ " ExsitingN="+str(Case.ExistingN) +" FailN="+str(Case.FailN))
        

                
        
    def throughput(self, dic):
        lines = []
        for multicast in self.multicast:
            dic["multicast"] = multicast
            for consumerClass in self.consumerClasses: 
                dic["consumerClass"] = consumerClass
                if consumerClass == "CDNIPConsumer" and multicast == "true":
                    continue
                if consumerClass == "CDNConsumer" and multicast == "false":
                    continue
                dots = []
                
                for producerN in self.producerN:
                    dic["producerN"] = producerN
                    
                    y = self.freqs[0]
                    for i in range(len(self.freqs)-1, -1, -1):
                        freq = self.freqs[i]
                        dic["freq"] = freq
                
                        Id = self.parseId(dic)    
                        tt = self.stat.get(Id, "unsatisfiedRequestN") + self.stat.get(Id, "nackedPacketN")
                        if tt < 1500:
                            y = freq
                            break
                            
                    dot = Dot(x=producerN, y=y)
                    
                    dots.append(dot)
                
                if consumerClass == "CDNConsumer":
                   label = "NDN"
                   color = "y"
                else:
                    label = "IP"
                    if multicast == "true":
                        label += " with Multicast"
                    color = "b"
                plt = {}
                plt["color"] = color
                plt["label"] = label
                #plt={"color":"b", "style":"o--", "label":"Impact of Interest Set"}
                line = Line(dots = dots, plt=plt)
                lines.append(line)
        canvas = {}
        canvas["xlabel"] = "Producer #"
        canvas["ylabel"] = "Throughput: Frequency of Interest"
        canvas["loc"] = "upper left"
        fig = Figure(Id="scalability", lines = lines, canvas=canvas)
        #fig.line()
        fig.bar()
#         dic["freq"] = 100
#         dic["RngRun"] = 3
#         dic["producerN"] = 10
#         dic["zipfs"] = 0.92
#         dic["duration"] = 50
#         dic["multicast"] = "true"
#         dic["consumerClass"] = "CDNConsumer"
#         for producerN in self.producerN:
#             dic["producerN"] = producerN
#             Id = self.parseId(dic)
#             y = self.stat.get(Id, "unsatisfiedRequestN")
#             print y


#         for freq in self.freqs:
#             dic = {}
#             dic["freq"] = freq
#             for consumer in self.consumerClasses:
#                 dic["consumerClass"] = consumer
#                 for seed in self.seeds:
#                     dic["RngRun"] = seed
#                     for producerN in self.producerN:
#                         dic["producerN"] = producerN
#                         for multicast in self.multicast:
#                             dic["multicast"] = multicast
#                             for zipfs in self.zipfs:
#                                 dic["zipfs"] = zipfs
#                                 
#                                 dic["duration"] = self.duration
#     
#                                 Id = self.parseId(dic)
#                                 case = Case(Id=Id, param=dic, **dic)
#                                 cases[Id] = case
    
    def create(self, func=throughput):
#         scalability: x-producerN, y-unsatisfiedRequest
#         QoS
#         bandwidth
#         latency
#         loss
        freqs = [100]
        consumerClass = self.consumerClasses
        seeds = [3]
        producerN = [10]
        multicast = self.multicast
        zipfs = [0.92]
        duration = self.duration
        
        #scalabiltiy
        dic = {}
        dic["freq"] = 100
        dic["RngRun"] = 3
        dic["producerN"] = 10
        dic["zipfs"] = 0.92
        dic["duration"] = self.duration
        
        for seed in self.seeds:
            dic["RngRun"] = seed
            for zipfs in self.zipfs:
                dic["zipfs"] = zipfs
                
                func(self, dic)
        
def stop():
    print "-------------- Kill Python ------------"
    os.system("pkill Python")




if __name__=="__main__":
    #cmd = "./waf --run 'shock-test  --ratetrf=shock/output/Case/ist-set.rate'>output/Case/ist-set.output 2>&1"
    #print os.system(cmd)
    #global DEBUG
    
    signal.signal(signal.SIGINT,stop)
    signal.signal(signal.SIGTERM, stop)
    
        
    for i in range(1, len(sys.argv)):
        av = sys.argv[i]
        if av == "--debug":
            DEBUG = True
        elif av == "--nodebug":
            DEBUG = False
            
    god = God(paper="cdn-over-ip")
    
    try:    
        god.setup()
    except IOError as e:
        self.log.error("I/O error({0}): {1}".format(e.errno, e.strerror))
    else:
        god.create()
    finally:
        if (not DEBUG) and (not HOSTOS.startswith("Darwin")):
            god.notify(way="email")

