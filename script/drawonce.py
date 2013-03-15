from conf import *

import matplotlib.pyplot as plt

import os.path
import time

class group:
    def __init__(self, xs, yss):
        self.xs = xs
        self.yss = yss
        self.ys = yss[0]
        self.title = "Figure"
        self.xlabel = "X"
        self.ylabel = "#"
        self.outFig = "out.pdf"
        self.style = "o-"
        self.label = "update"
        self.grid = True

    def drawFigure(self):
        
        if (os.path.exists(group.outFig)):
            return

        plt.clf()
        
        plt.xlabel(group.xlabel);
        plt.ylabel(group.ylabel);
        plt.plot(group.xs, [group.yss[2][i]/float(group.ys[i]) for i in range(len(group.ys))],
                 group.style, label=group.label)
        
        plt.grid(group.grid)
        if (group.title != None):
            plt.title(group.title)
        plt.legend()

        #plt.ylim(group.ymin, group.ymax)
        plt.show()
        
        #plt.savefig(group.outFig)


def readData(fp):
    #assert len(xs)==len(ys), "len(xs)!=len(ys) xs="+str(xs)+", ys="+str(ys)
    f = open(fp)
    
    xs = []
    yss = [[],[],[]]
    for rd in f.readlines():
        if rd.startswith(DATA_LINE_IGNORE_FLAG):
            continue
        rd = rd.strip()
        xys = rd.split()
        
        x = int(xys[0])
        xs.append(x)
        for i in range(1, len(xys)):
            value = int(xys[i])
            yss[i-1].append(value)
    f.close()
    return xs, yss



if __name__=="__main__":
#    cnt = getUpdateNum(fp = UPDATE_FILE)
#    for i in range(len(cnt)):
#        print "i=",i," counter="+str(cnt[i])
    top = "../output/data/"
    fs = os.listdir(top)
    for f in fs:
        if os.path.isfile(f) and f.endswith(".dat"):
            pass
    
    fp1 = "../output/data/duration[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]-producer2.dat"
    fp3 = "../output/data/duration[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]-producer3.dat"
    fp4 = "../output/data/duration[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]-producer4.dat"
    fp5 = "../output/data/duration[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]-producer5.dat"
    fp2 = "../output/data/duration[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]-producer2-ConsumerZipfMandelbrot.dat"

    for fp in [fp5]:
        xs, yss = readData(fp)
        group = group(xs, yss)
        group.drawFigure()
