
import md5
import os, os.path

SIMULATION_SCRIPT = "./waf --run \"xiaoke"
DATA_LINE_IGNORE_FLAG = "#"
OUT = "./output/"

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
ch = logging.StreamHandler() #console
ch.setLevel(logging.WARN)
log.addHandler(ch)

fh = logging.FileHandler(__name__+".log", mode="w")
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


class TestCase:
    def __init__(self, duration=1, seed=3, producerNum=2, consumerClass="ConsumerCbr", csSize="0", cmd=SIMULATION_SCRIPT):
        self.duration = duration
        self.seed = seed
        self.producerNum = producerNum
        self.consumerClass = consumerClass
        self.csSize = csSize
        
        
        
        
        self.id = self.getID()
        self.cmd = cmd+" --duration="+str(self.duration)+ " --seed="+str(self.seed) +" --producerNum="+str(self.producerNum)
        if consumerClass != None and consumerClass != "ConsumerCbr":
            self.cmd += " --consumerClass="+consumerClass
        if not (self.csSize == "Zero" or self.csSize == "ZERO"):    
            self.cmd += " --csSize="+self.csSize
            
        self.cmd +=  "\"";
        
        
        self.output = os.path.join(OUT, "case/")
        if not os.path.exists(self.output):
            os.makedirs(self.output)
        self.output = os.path.join(self.output, self.id+".log")
        
        log.info("output="+self.output)
        self.cmd += ">"+self.output
        
        self.cmd += " 2>&1"
        self.consumerClass = consumerClass
        
        self.y = -1
        log.info("cmd4="+self.cmd);
        
    def getID(self):
        name = "duration"+str(self.duration)
        
        if self.seed !=3:
            name += "-seed"+str(self.seed)
            
        if self.consumerClass!=None and self.consumerClass!="ConsumerCbr":
            name += "-"+str(self.consumerClass)
             
        if not (self.csSize == "Zero" or self.csSize == "ZERO"):
            name += '-csSize'+self.csSize
        log.info("csSize="+self.csSize)
        
        name += "-producers"+str(self.producerNum)
        
        log.debug("name="+name)
        return name
        #print self.cmd


class CaseGroup:
    def __init__(self, duration=1, seed=3, producerNum=2, cmd=SIMULATION_SCRIPT, duration_li=None, producerNum_li=None, 
                 consumerClass="ConsumerCbr", csSize="Zero",
                 xlabel="X", ylabel="Y", ymin=0.0, ymax=1.0,
                 style=None, label=None, title=None, outFig="output/fig.pdf"
                 ):
        assert not (duration_li != None and producerNum_li !=None)
        
        self.cases = []
        tc = TestCase(duration, seed, producerNum, consumerClass, csSize=csSize, cmd=cmd)
        self.cases.append(tc)
        
        self.duration = duration
        self.seed = seed
        self.producerNum = producerNum
        self.duration_li = duration_li
        self.producerNum_li = producerNum_li
        self.consumerClass = consumerClass
        self.csSize = csSize
        
        
        self.grid = True
        self.gridWhich = "major"
        self.xs = []
        self.yss = [[], [], []]
        self.ys = self.yss[0]
        self.y2s = self.yss[1]
        self.y3s = self.yss[2]
        
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.max = 0
        self.ymin = ymin
        self.ymax = ymax
        self.style = style or "ro"
        
        if (duration_li != None):
            self.xs.append(duration)
            self.xs += duration_li
            for drt in duration_li:
                tc = TestCase(drt, seed, producerNum, consumerClass, csSize = self.csSize, cmd=cmd)
                self.cases.append(tc)

        if (producerNum_li != None):
            self.xs.append(producerNum)
            self.xs += producerNum_li
            for num in producerNum_li:
                tc = TestCase(duration, seed, num,consumerClass, csSize=self.csSize, cmd=cmd)
                self.cases.append(tc)
        #
        self.id = self.getID()
        
        self.label = label
        self.title = title or self.id
                
        self.outData =  os.path.join(OUT, "data/")
        if not os.path.exists(self.outData):
            os.makedirs(self.outData)
        self.outData = os.path.join(self.outData, self.id+".dat")

        self.outFig = os.path.join(OUT, "fig/")
        if not os.path.exists(self.outFig):
            os.makedirs(self.outFig)

        self.outFig = os.path.join(self.outFig, self.id+".pdf")
        
        assert len(self.xs) == len(self.cases)#, "xs dimension" +str(len(self.xs))+" != ys dimension" + str(len(self.cases))
    
    def getCMDs(self):
        cmds = []
        for case in self.cases:
            cmds.append(case.cmd)
        log.info("cmds: "+str(cmds))
        return cmds
    
        
    def getID(self, shortmodel=False):
        if (self.duration_li != None):
             name = "duration"+str(self.xs)
             if shortmodel:
                 name += "\n"
        else:
            name = "duration"+str(self.duration)
            
        if (self.producerNum_li != None):
            name += "-producer"+str(self.xs)
            if shortmodel:
                name += "\n"
        else:
             name += "-producer"+str(self.producerNum)
                
        if (self.seed != 3):
            name += "-seed"+str(self.seed)
            if shortmodel:
                 name += "\n"
        if (self.consumerClass != None and self.consumerClass != "ConsumerCbr"):
            name += "-"+self.consumerClass
            if shortmodel:
                 name += "\n"
        if not (self.csSize == "Zero" or self.csSize == "ZERO"):
            name += '-csSize'+self.csSize
        
        log.debug("name="+name)
        return name
        


class Merger:
    def __init__(self, title, groups):
        self.groups = groups
        self.title = title# + self.getName("\n")
        self.id = self.getID()
        self.outFig = os.path.join(OUT, "fig/")
        if not os.path.exists(self.outFig):
            os.makedirs(self.outFig)
        self.outFig = os.path.join(self.outFig, title+"-"+self.id+".pdf")
        
    def getID(self):
        name = self.getName()
        m = md5.new()
        m.update(name)
        return m.hexdigest()
    
    def getName(self, spliter="-"):
        name = ""
        for group in self.groups:
            name += spliter+ group.getID()
        
        return name
        

debug = True

if debug:
    MAX_DURATION = 3#15
    MAX_PRODUCER_NUM = 4#7
    OUT = "./output2/"
else :
    MAX_DURATION = 10
    MAX_PRODUCER_NUM = 7
    
csSize0 = "ZERO"
def getDemo1():
    groups = []
    for num in range(2, MAX_PRODUCER_NUM, 1):
        group = CaseGroup(duration_li=range(2, MAX_DURATION), producerNum=num, csSize=csSize0,
              xlabel="Simulation Time (Seconds)", ylabel="# update", style="o-", 
              label="Producer#="+str(num), title="Duration: [2,"+str(MAX_DURATION)+"]\nProducer Num="+str(num))
        groups.append(group)
    demo1 = Merger("Sequence csSize="+str(csSize), groups)
    return demo1

def getDemo2():
    groups = []
    for num in range(2, MAX_PRODUCER_NUM, 1):
        group = CaseGroup(duration_li=range(2, MAX_DURATION), producerNum=num, 
                          consumerClass="ConsumerZipfMandelbrot", csSize=csSize0,
              xlabel="Simulation Time (Seconds)", ylabel="# update", style="o-", 
              label="Producer#="+str(num), title="Duration: [2,"+str(MAX_DURATION)+"]\nProducer Num="+str(num))
        groups.append(group)
    demo1 = Merger("Zipf-Mandelbrot csSize="+str(csSize0), groups)
    return demo1

csSize = "10"
def getDemo3():
    groups = []
    for num in range(2, MAX_PRODUCER_NUM, 1):
        group = CaseGroup(duration_li=range(2, MAX_DURATION), producerNum=num, csSize=csSize,
              xlabel="Simulation Time (Seconds)", ylabel="# update", style="o-", 
              label="Producer#="+str(num), title="Duration: [2,"+str(MAX_DURATION)+"]\nProducer Num="+str(num))
        groups.append(group)
    demo1 = Merger("Sequence csSize="+str(csSize), groups)
    return demo1

def getDemo4():
    groups = []
    for num in range(2, MAX_PRODUCER_NUM, 1):
        group = CaseGroup(duration_li=range(2, MAX_DURATION), producerNum=num, 
                          consumerClass="ConsumerZipfMandelbrot", csSize=csSize,
              xlabel="Simulation Time (Seconds)", ylabel="# update", style="o-", 
              label="Producer#="+str(num), title="Duration: [2,"+str(MAX_DURATION)+"]\nProducer Num="+str(num))
        groups.append(group)
    demo1 = Merger("Zipf-Mandelbrot csSize="+str(csSize), groups)
    return demo1



fig1 = getDemo1()
fig2 = getDemo2()
fig3 = getDemo3()
fig4 = getDemo4()
#groups = [pCase]
#groups = [dCase]