from conf import *

import os.path
import time

def getUpdateNum(fp, startFlag=UPDATE_FLAG, ignoreFlags=UPDATE_IGNORE_FLAGS): #filepath
    if (not os.path.exists(fp)):
        time.sleep(3)
        
    f = open(fp)

    counter = 0
    for line in f.readlines():
        if line.startswith(DATA_LINE_IGNORE_FLAG):
            continue
        if line.startswith(startFlag):
            for flag in ignoreFlags:
                if line.find(flag) != -1:
                    continue;
            counter +=1

    #print "counter="+str(counter) 
    return counter;

if __name__=="__main__":
    getUpdateNum(UPDATE_FILE, UPDATE_FLAG)

