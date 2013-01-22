import matplotlib
matplotlib.use("pdf")
import platform
HOSTOS = platform.system()
import matplotlib.pyplot as plt
import md5
import os, os.path
import signal, sys, time
import string
import smtplib
from scipy import optimize
import numpy as np

import inspect
from script.updateCounter import getUpdateNum
from script.cmp import cmp
import logging
import threading


log = logging.getLogger(__name__)
format='%(levelname)5s:%(funcName)12s:%(lineno)3d: %(message)s'   
#http://docs.python.org/2/library/logging.html#logrecord-attributes
logging.basicConfig(format=format, datefmt='%m/%d/%Y %I:%M:%S %p')
log.setLevel(logging.INFO)
ch = logging.StreamHandler() #console
ch.setLevel(logging.WARN)
log.addHandler(ch)

fh = logging.FileHandler(__name__+".log", mode="w")
fh.setLevel(logging.WARN)
log.addHandler(fh)


SIMULATION_SCRIPT = "./waf --run \"xiaoke"
DATA_LINE_IGNORE_FLAG = "#"

IS_MT = True #Multi Threads Run
IS_REFRESH = False
YS_DIM = 10
OUT = "outputcdn"

NOT_YET = 0
READ_YET = 1
RUN_YET = 2
UP_YET = 3


DEBUG = False


if HOSTOS.startswith("Darwin"):
    DEBUG = True

if DEBUG:
    MAX_DURATION = 8#15
    MAX_PRODUCER_NUM = 4#7
    CS_LIST =["Zero"]
    OUT += "-debug"
    CONSUMER_CLASS_LIST = ["ConsumerCbr"]
    CONSUMER_CLASS_LIST = ["ConsumerCbr", "ConsumerZipfMandelbrot"]
    
else :
    MAX_DURATION = 10
    MAX_PRODUCER_NUM = 7
    CS_LIST = ["Zero", 1,3,5, 10, 0]
    CS_LIST = ["Zero", 1,3,5, 10, 0]
    CONSUMER_CLASS_LIST = ["ConsumerCbr", "ConsumerZipfMandelbrot"]
    
class Manager(threading.Thread):
    def get_current_function_name(self):
#        def get_cur_info():  
#        print sys._getframe().f_code.co_filename #__file__
#        print sys._getframe().f_code.co_name
#        print sys._getframe().f_lineno  
        return inspect.stack()[1][3]
    
    def __init__(self, children, data={}, atts=[], id=None):
        threading.Thread.__init__(self)
        
        self.daemon = True
        self.isMT = IS_MT
        self.isRefresh = IS_REFRESH
        
        self.yet = NOT_YET
        
        
        self.children = children
        self.data = data
        self.atts = atts # subset of keys of data, which is used to make the Id
        
        self.id = id or self.getId()
        self.setName(self.id)
        self.out = os.path.join(OUT, self.__class__.__name__)
        if not os.path.exists(self.out):
            os.makedirs(self.out)
        outType = self.getAtt("outType") or ".dat"
        self.out = os.path.join(self.out, self.id+outType)
    
    
    def getAtt(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None
        
    def getId(self, separater="-"):
        id = self.__class__.__name__
        for key in self.atts:
            value = self.getAtt(key)
            id += separater + key +str(value)
        
        return id
        
    def run(self):
        log.info("> " +self.id+" begins")
        if (not self.isRefresh) and self.out != None and os.path.exists(self.out) :
            log.info("= "+self.id+" exists")
            self.read()
            self.yet = READ_YET
            return
        
        if self.children == None:
            self.yet = RUN_YET
            return
        
        for child in self.children:
            child.start()
            if not self.isMT:
                child.join()
        if not self.isMT:
            self.yet = RUN_YET
            
    
    def signal_handler(signum, frame):
        log.info("get keyboard interrupt") 
        sys.exit();


    def waitChildren(self):
        
        #signal.signal(signal.SIGINT,  self.signal_handler); 
        #signal.signal(signal.SIGTERM, self.signal_handler);
        
        
        if self.children == None:
            log.info("< " +self.id+" ends")
            while self.yet == NOT_YET:
                time.sleep(1)
                
            return
        
        while self.yet == NOT_YET:
            for child in self.children:
                if child.isAlive():
                    child.join()
            if self.isMT:
                self.yet = RUN_YET
        
        for child in self.children:
            assert child.yet != NOT_YET, child.getId()+" is not yet("+str(child.yet)+"), but parent thread ends("+str(self.yet)+")"
            
        log.info("< " +self.id+" ends")

            
    def after(self):
        log.info("after all complete run: nothing")
    
    def read(self):
        log.info("read")
    
    def write(self):
        log.info("write")
    
    def digest(self, str):
        m = md5.new()
        m.update(str)
        return m.hexdigest()
    
class Dot(Manager):
    atts = ["duration", "seed", "producerNum", "consumerClass", "cs", "nack"]
    script=SIMULATION_SCRIPT
    
    def __init__(self, data, id=None):
        Manager.__init__(self, children=None, data = data, atts = Dot.atts, id=id)
        self.trace = os.path.join(OUT, self.__class__.__name__, self.id+".trace")
        self.data["trace"] = os.path.join("./shock", self.trace)
        self.x = self.getAtt("duration")
        
        
        self.ys = []
    #       
        self.cmd = Dot.script
        for k, v in data.iteritems():
            self.cmd += " --"+str(k)+"="+str(data[k])

        self.cmd +=  "\"";
        self.cmd += ">"+self.out+" 2>&1"    
    
#    def __init__(self, duration, seed, producerNum, consumerClass, cs, id=None):
#        data = {}
#        data["duration"] = duration
#        data["seed"] = seed
#        data["producerNum"] = producerNum
#        data["consumerClass"] = consumerClass
#        data["cs"] = cs
#        
#        self.init(data, Dot.atts, id)
#    

            
    def init(self, data, atts, id):    
        #get self.id and self.out by calling getId()
        Manager.__init__(self, children=None, data = data, atts = atts, id=id)
        
        self.x = self.getAtt("duration")
        
        
        self.ys = []
#        self.y = self.ys[0]
#        self.y2 = self.ys[1]
#        self.y3 = self.ys[2]
        
        
        self.cmd = Dot.script
        self.cmd += " --duration="+str(self.getAtt("duration"))+ " --seed="+str(self.getAtt("seed")) +" --producerNum="+str(self.getAtt("producerNum"))
      
        self.cmd += " --consumerClass="+self.getAtt("consumerClass")
        cs = self.getAtt("cs")

        self.cmd += " --csSize="+str(self.getAtt("cs"))
        
        self.cmd +=  "\"";
        self.cmd += ">"+self.out+" 2>&1"
        

        
    def run(self):
        log.info("> " +self.id+" begins")
        if (not self.isRefresh) and self.out != None and os.path.exists(self.out) :
            self.yet = READ_YET
            log.info("= "+self.out+" exists")

        else:    
            log.info("+ "+ "CMD: "+self.cmd)
            rst = os.system(self.cmd)
            if rst != 0:
                log.error("CMD: "+self.cmd+" return "+str(rst)+" (0 is OK)")
                os.remove(self.out)
                return
    
        self.read()
        if self.yet == NOT_YET:
            self.yet = RUN_YET
        log.debug("self.ys = "+str(self.ys))
        
#    def waitChildren(self):    
#        Manager.waitChildren(self)
        
        
    def read(self):
        cnt = getUpdateNum(self.out)
            #return
        for i in range(len(cnt)):
            self.ys.append(cnt[i])
        
        cnt = cmp(self.trace)
        self.ys += cnt
        
        log.info(self.id+" ys="+str(self.ys))
        
        if len(self.ys) != YS_DIM:
            log.warn("len(self.ys) != YS_DIM. cnt="+str(self.ys))

        
class Line(Manager):
    def __init__(self, dots, data, id=None):#
        self.dots = dots
        Manager.__init__(self, children=dots, data=data, id=id)
        #self.isRefresh = True
        
        self.xs = []
        self.yss = [[] for i in range(YS_DIM)]
#        self.y1s = self.yss[0]
#        self.y2s = self.yss[1]
#        self.y3s = self.yss[2]
        self.updates = self.yss[0]  #update number
        self.ists = self.yss[1]  #Interst packets
        self.datas = self.yss[2] #Data generating packets
        self.meets = self.yss[3] #Data arrives 
        #self.ys = [self.datas[i]/self.ists[i] for i in range(len(self.datas[i]))]
        
    def getId(self, separater="-"):
        id = self.__class__.__name__
        cmds = self.getCMDs()
        id += separater + self.getAtt("label") + separater+ self.digest(str(cmds))
        return id
    
    
    def read(self):
        log.info(self.id+" read data")
        f = open(self.out)
        for rd in f.readlines():
            rd = rd.strip()
            if rd.startswith(DATA_LINE_IGNORE_FLAG):
                continue
            
            xys = rd.split()
            
            assert len(xys) == len(self.yss) + 1, "reading data error"
            x = float(xys[0])
            self.xs.append(x)
            for i in range(1, len(xys)):
                value = float(xys[i])
                self.yss[i-1].append(value)  
        f.close()
        
        for i in range(len(self.dots)):
            dot = self.dots[i]
            dot.x = self.xs[i]
            log.debug("xs="+str(self.xs)+", yss="+str(self.yss))
            dot.ys = self.yss[0][i]
            dot.yet = UP_YET
        log.info(self.id+" read yss="+str(self.yss))    
            
    def write(self):
        assert len(self.xs)==len(self.yss[0]),  "len(xs)!=len(yss[0]) xs="+str(self.xs)+", yss[0]="+str(self.yss[0])
        f = open(self.out, "w")
        f.write(DATA_LINE_IGNORE_FLAG+"\t"+self.id+"\n");
        
        for cmd in self.getCMDs():
            f.write(DATA_LINE_IGNORE_FLAG + "\t" + cmd+"\n")
            
        #f.write(DATA_LINE_IGNORE_FLAG+"\tduration"+"\tChanging#"+"\tIST#"+"\tDataNew#"+"\tDataArrive#\tNack#\n")
        titles = ["#duration", "update#", "Interest#", "DataNew#", "DataMet#", "Nack#"]
        #  return [rd, avglast, avgfull, avghop, avgretx]
        titles +=["record#", "ALastDelay", "AFullDelay", "AvgHop", "AvgRetx#"]
        for i in range(len(titles)):
            title = titles[i]
            f.write("%12.10s(%d)"%(title, i-1))
        f.write("\n")
        
        for i in range(len(self.xs)):
            x = self.xs[i]
            f.write("%15.10s"%(x))
            #line = str(x)
            for j in range(len(self.yss)):
                #print "i=",i,", j=",j
                value = str(self.yss[j][i])
                f.write("%15.10s"%(value))
                #line += "\t" + str(value)
            #line += "\n"
            f.write("\n")
        f.flush()
        f.close()
    
        
    def getCMDs(self):
        cmds = []
        for dot in self.dots:
            cmds.append(dot.cmd)
        #log.info("cmds: "+str(cmds))
        return cmds
    
        
    def run(self):
        Manager.run(self)
        Manager.waitChildren(self)
        self.after()
        if self.getAtt("tofit"):
            self.fit()
        self.write()
        
        
        
    def after(self):
        if (not self.isRefresh) and os.path.exists(self.out):
            for i in range(len(self.dots)):
                dot = self.dots[i]
                dot.x = self.xs[i]
                log.debug("xs="+str(self.xs)+", yss="+str(self.yss))
                dot.ys = self.yss[0][i]
        else:
            for dot in self.dots:
                self.xs.append(dot.x)
#                self.updates.append(dot.ys[0])
#                self.ists.append(dot.ys[1])
#                self.datas.append(dot.ys[2])
#                self.meets.append(dot.ys[3])
                for i in range(len(dot.ys)):
                    v = dot.ys[i]
                    self.yss[i].append(v)
                log.debug(self.getId()+" add ys="+str(self.updates)+" xs="+str(self.xs)+" yss="+str(self.yss))
        
        #self.ys = [self.datas[i]/self.ists[i] for i in range(len(self.datas))]
        Yindex = self.getAtt("Yindex") or 0
        if type(Yindex) == int:
            self.ys = self.yss[int(Yindex)] 
        elif type(Yindex) == str:
            tmps = Yindex.split(".")
            assert len(tmps) == 2, "tmps="+str(tmps)
            t1 = int(tmps[0])
            t2 = int(tmps[1])
            self.ys = [self.yss[t1][i]/float(self.yss[t2][i]) for i in range(len(self.xs))]
            
            
    def fitx2(self, x, a, b, c):        
        return a * x **2 + b * x + c
    
    def fitx(self, x, a, b):
        return a * x + b
    
    
    def fit(self, func=None, guess=None, func_argcount=None):
        func = func or self.fitx
        if guess == None:
            guess = [1 for i in range(func_argcount or func.func_code.co_argcount - 2)]
        params, params_covariance = optimize.curve_fit(func, np.array(self.xs), np.array(self.ys), guess)
        self.ysfit = [func(self.xs[i], *params) for i in range(len(self.xs))]
        self.paramsfit = params
        self.variancefit = params_covariance
        log.info(self.id+" fit with "+func.func_code.co_name+" ends. params="+str(params)+" variance="+str(params_covariance))
        return params, params_covariance
        
def testDot():
    dot = Dot(duration=1, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs=3)
    dot.run()

#testDot()

def testLine():
    dot1 = Dot(duration=1, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs=10)
    dot2 = Dot(duration=2, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs=10)
    ld = {}
    ld["label"] = "differentSC"
    line = Line([dot1, dot2], ld)
    line.start()

#testLine()

lock=threading.RLock()        
class Figure(Manager):
    def __init__(self, lines, data={}, id=None):
        self.lines = lines
        data["outType"] = ".pdf"
        data["linestyle"] = "o-"
        Manager.__init__(self, lines, data, id=id)
        self.isRefresh = True
    
    def run(self):
        Manager.run(self)
        Manager.waitChildren(self)
        self.write()

    def write(self):
        lock.acquire()
        log.debug("begin to draw ")
        plt.clf()
        log.debug("1")
        #plt.figure(figsize=(5,9))
        log.debug("2")
        for line in self.lines:
            if len(line.xs) != len(line.updates):
                log.error("plot xs.size!=ys.size. xs="+str(line.xs)+", yss="+str(line.yss)+" group.id="+line.id)
                continue
            log.info(line.id+" xs="+str(line.xs)+" ys="+str(line.ys)+ " label="+line.getAtt("label"))
            plt.plot(line.xs, line.ys, self.getAtt("linestyle"), label=line.getAtt("label"))
            if line.getAtt("tofit"):
                plt.plot(line.xs, line.ysfit, self.getAtt("linestyle"), label=line.getAtt("label")+"-fit")

            
        plt.grid(self.getAtt("grid"))
        plt.xlabel(self.getAtt("xlabel") or "X");
        plt.ylabel(self.getAtt("ylabel") or "Y");
        
        plt.title(self.getAtt("title"))
        
        #location: http://matplotlib.org/api/pyplot_api.html
        plt.legend(loc="upper left")
        log.debug("fig save to "+self.out) 
        plt.savefig(self.out)
        #plt.close()
        
        log.info(self.id+" finishes")
        log.debug("end to draw")
        lock.release()
    
    def after(self):
        pass
    
    def getId(self, separater="-"):
        id = self.__class__.__name__
        
        id += separater + self.getAtt("title")
        t = ""
        for line in self.lines:
            id += separater + line.getAtt("label")
            t += separater+ line.id
        id += separater + self.digest(t)
        return id
    

def testFigure():
    dot1 = Dot(duration=1, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs=10)
    dot2 = Dot(duration=2, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs=10)
    ld = {}
    ld["label"] = "cs=10"
    line1 = Line([dot1, dot2], ld)
    line1.isRefresh = True
    
    dot3 = Dot(duration=1, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs="1")
    dot4 = Dot(duration=2, seed=3, producerNum=2, consumerClass="ConsumerCbr", cs="1")
    ld = {}
    ld["label"] = "cs=0"
    line2 = Line([dot3, dot4], ld)
    line2.isRefresh = True
    
    ld = {"title":"CS"}
    figure = Figure([line1, line2], ld)
    figure.start()
    
#testFigure()

class Paper(Manager):
    
    def __init__(self, figures, data):
        self.figures = figures
        Manager.__init__(self, figures, data)
        self.isRefresh = True
        #self.Daemon = False
        self.t0 = time.time()
        
    def run(self): 
        Manager.run(self)
        Manager.waitChildren(self)
        self.after()
        
    def getId(self, separater="-"):
        id = self.__class__.__name__
        id += separater+self.getAtt("title")
        str = ""
        for fig in self.figures:
            str += separater + fig.id
        id += separater + self.digest(str)
        return id

    def after(self):
        self.t1 = time.time()
        data = self.id+" ends on "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+" after running for "+str(self.t1 - self.t0)+" seconds"
        log.info(data)
        if HOSTOS.startswith("Darwin"):
            return
        from smtplib import SMTP
        TO = ["shock.jiang@gmail.com"]
        FROM = "06jxk@163.com"
        SMTP_HOST = "smtp.163.com"
        user= "06jxk"
        passwords="jiangxiaoke"
        data = self.id+" ends on "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))+" after running for "+str(self.t1 - self.t0)+" seconds"
        mailb = ["paper ends", data]
        mailh = ["From: "+FROM, "To: shock.jiang@gmail.com", "Subject: Paper ends "+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.t1)))]
        mailmsg = "\r\n\r\n".join(["\r\n".join(mailh), "\r\n".join(mailb)])
    
        send = SMTP(SMTP_HOST)
        send.login(user, passwords)
        rst = send.sendmail(FROM, TO, mailmsg)
        
        if rst != {}:
            log.warn("send mail error: "+str(rst))
        else:
            log.info("sending mail finished")
        send.close()
            
        
