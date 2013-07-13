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

MAX_THREADN = 100

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
    def __init__(self, Id, cases, headers=["caseId", "time", "droppedPacketN", "changeProducerN", "satisfiedRequestN", "unsatisfiedRequestN"]):
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
        
        if isinstance(self.data[caseId][0], list): #self.data[caseId]= [['time', 'value'],[1,'a'],[2,'b']]
            li = []
            for liv in self.data[caseId]:
                li.append(liv[index])
            return li
        return self.data[caseId][index]  #self.data[caseId] = ['freq', 'value']
    
    #### to be overloaded    
    def stat(self):
        self.log.info("> Stat: "+self.Id+" begins")
        
        for Id, case in self.cases.items():
            fp = os.path.join(OUT, "Case", "request-"+Id+".txt")
            f = open(fp)
            self.data[Id] = []
            self.log.debug("stat add Id: "+Id)
            for line in f.readlines():
                if line.startswith("#"):
                    continue
                parts = line.split()
                parts[0] = int(parts[0])/1000.0
                self.data[Id].append( parts )

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
        
        self.setDaemon(True)
        self.result = None
        
        self.cmd = "./waf --run \'cdn-nodedown"
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
            ys = [int(y)/100.0 for y in line.ys]
            can = plt.plot(line.xs, ys, line.plt.pop("style", "o-"), **line.plt)
            cans.append(can)
        
        plt.xlabel(self.canvas.pop("xlabel", " "))
        plt.ylabel(self.canvas.pop("ylabel", " "))    
        plt.legend(**self.canvas)
        
        plt.plot([5], [0], 'o')
        plt.annotate('Key Node is Down', xy=(5,0), xytext=(2, 15),
                     arrowprops=dict(facecolor='black', shrink=0.05))
        
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
        Max_Freq = 200
        Step = 10
        self.freqs = range(Min_Freq, Max_Freq+Step, Step)
        self.freqs = [80]
        self.zipfs = [0.99, 0.92, 1.04]
        self.zipfs = [0.99]
        self.duration = 10
        self.producerN = [5, 10, 15, 18, 20, 25, 30]
        self.producerN = [30]
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
        
        
    def setup(self):
        self.log.info("> "+ self.Id + " setup begins")
        cases = self.cases

        
        for consumerClass in self.consumerClasses:
            for multicast in self.multicast:
                if consumerClass == "CDNConsumer" and multicast == "false":
                    continue
                if consumerClass == "CDNIPConsumer" and multicast == "true":
                    continue
                dic = {}
                dic["freq"] = 70
                dic["RngRun"] = 3
                dic["producerN"] = 30
                dic["zipfs"] = 0.92
                dic["duration"] = 16
                dic["item"] = "nodedown"
                dic["consumerClass"] = self.consumerClasses
                dic["multicast"] = self.multicast
                trace = self.parseId(dic)
                dic["trace"] = trace
                
                dic["consumerClass"] = consumerClass
                dic["multicast"] = multicast 
                Id = self.parseId(dic)
                dic["id"] = Id
                case = Case(Id=Id, param=dic)
                cases[Id] = case
        
        self.stat = Stat(Id=self.parseId(self.dic), cases=self.cases)
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
        
        
        
    
        self.log.info("< "+ self.Id + " setup ends " +\
                      "TotalN="+str(len(cases))+" SuccessN="+str(Case.SuccessN)+ " ExsitingN="+str(Case.ExistingN) +" FailN="+str(Case.FailN))
    
    def reliability(self):
        pass
    
    
    def create(self, func):
#         scalability: x-producerN, y-unsatisfiedRequest
#         QoS
#         bandwidth
#         latency
#         loss
        self.stat.stat()
        lines = []
        for Id, case in self.cases.items():
            times = self.stat.get(Id, "time")
            unsatisfiedRequestNs = self.stat.get(Id, "unsatisfiedRequestN")
            self.log.debug("times="+str(times)+" Ns="+str(unsatisfiedRequestNs))
            assert len(times) == len(unsatisfiedRequestNs), "length is not equal"
            dots = []
            for i in range(len(times)):
                dot = Dot(x=times[i], y=unsatisfiedRequestNs[i])
                dots.append(dot)
            
            plt = {}
            
            if case.param["consumerClass"] == "CDNConsumer":
                label = "NDN"
                color = "y"
            elif  case.param["consumerClass"] == "CDNIPConsumer":
                label = "IP"
                if case.param["multicast"] == "true":
                    label += " with Multicast"
                color = "b"
            self.log.debug("consumerClass="+case.param["consumerClass"]+" multicast="+case.param["multicast"])
            plt["label"] = label
            plt["color"] = color
            line = Line(dots = dots, plt=plt)
            lines.append(line)
        
        canvas = {}
        canvas["loc"] = "upper left"
        canvas["xlabel"] = "Time (Second)"
        canvas["ylabel"] = "Unsatisfied Request # (x100)"
        fig = Figure(Id="reliabiltiy-node", lines=lines, canvas=canvas)
        fig.line()

#         freqs = [100]
#         consumerClass = self.consumerClasses
#         seeds = [3]
#         producerN = [10]
#         multicast = self.multicast
#         zipfs = [0.92]
#         duration = [50]
#         
#         #scalabiltiy
#         dic = {}
#         dic["freq"] = 100
#         dic["RngRun"] = 3
#         dic["producerN"] = 10
#         dic["zipfs"] = 0.92
#         dic["duration"] = self.duration
#         
#         for seed in self.seeds:
#             dic["RngRun"] = seed
#             for zipfs in self.zipfs:
#                 dic["zipfs"] = zipfs
#                 
#                 func(self, dic)
#         
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
        god.create(None)
        pass
    finally:
        if (not DEBUG) and (not HOSTOS.startswith("Darwin")):
            god.notify(way="email")

