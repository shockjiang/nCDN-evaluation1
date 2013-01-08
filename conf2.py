import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import md5
import os, os.path
import signal, sys, time
import string
import smtplib

TO = ["shock.jiang@gmail.com"]
FROM = "justok06@foxmail.com"
SMTP_HOST = "smtp.qq.com"

import inspect
from script.updateCounter import getUpdateNum
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
YS_DIM = 3
OUT = "./output3/"

NOT_YET = 0
READ_YET = 1
RUN_YET = 2
UP_YET = 3


DEBUG = False
if DEBUG:
    MAX_DURATION = 3#15
    MAX_PRODUCER_NUM = 3#7
    OUT = "./output3-debug/"
else :
    MAX_DURATION = 10
    MAX_PRODUCER_NUM = 7


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
    atts = ["duration", "seed", "producerNum", "consumerClass", "cs"]
    script=SIMULATION_SCRIPT
    def __init__(self, duration, seed, producerNum, consumerClass, cs, id=None):
        data = {}
        data["duration"] = duration
        data["seed"] = seed
        data["producerNum"] = producerNum
        data["consumerClass"] = consumerClass
        data["cs"] = cs
        
        self.init(data, Dot.atts, id)
        
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
        if len(cnt) != YS_DIM:
            log.warn("len(cnt) != YS_DIM. cnt="+str(cnt))
            return
        for i in range(len(cnt)):
            self.ys.append(cnt[i])
        
        
class Line(Manager):
    def __init__(self, dots, data, id=None):#
        self.dots = dots
        Manager.__init__(self, children=dots, data=data, id=id)
        #self.isRefresh = True
        
        self.xs = []
        self.yss = [[] for i in range(YS_DIM)]
        self.ys = self.yss[0]
        self.y2s = self.yss[1]
        self.y3s = self.yss[2]
        
    def getId(self, separater="-"):
        id = self.__class__.__name__
        cmds = self.getCMDs()
        id += separater + self.getAtt("label") + separater+ self.digest(str(cmds))
        return id
    
    
    def read(self):
        log.info(self.id+" read data")
        f = open(self.out)
        for rd in f.readlines():
            if rd.startswith(DATA_LINE_IGNORE_FLAG):
                continue
            rd = rd.strip()
            xys = rd.split()
            
            assert len(xys) == len(self.yss) + 1, "reading data error"
            x = xys[0]
            self.xs.append(x)
            for i in range(1, len(xys)):
                value = xys[i]
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
            
        f.write(DATA_LINE_IGNORE_FLAG+"\t"+str(self.getAtt("xlabel"))+"\t"+str(self.getAtt("ylabel"))+"\n")
        
        for i in range(len(self.xs)):
            x = self.xs[i]
            line = str(x)
            for j in range(len(self.yss)):
                value = self.yss[j][i]
                line += "\t" + str(value)
            line += "\n"
            f.write(line)
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
                self.ys.append(dot.ys[0])
                self.y2s.append(dot.ys[1])
                self.y3s.append(dot.ys[2])
                log.debug(self.getId()+" add ys="+str(dot.ys[0])+" xs="+str(self.xs)+" yss="+str(self.yss))
    
        
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
            if len(line.xs) != len(line.ys):
                log.error("plot xs.size!=ys.size. xs="+str(line.xs)+", ys="+str(line.ys)+" group.id="+line.getID())
                continue
            log.info(line.id+" xs="+str(line.xs)+" ys="+str(line.ys)+ " label="+line.getAtt("label"))
            plt.plot(line.xs, line.ys, label=line.getAtt("label"))


            
        plt.grid(self.getAtt("grid"))
        plt.xlabel(self.getAtt("xlabel") or "X");
        plt.ylabel(self.getAtt("ylabel") or "Y");
        
        plt.title(self.getAtt("title"))
        plt.legend()
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
        if DEBUG:
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
            
        
