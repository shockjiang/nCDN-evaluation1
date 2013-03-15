from conf import *

import os.path
import time

def getUpdateNum(fp, startFlags=START_FLAGS, ignoreFlags=IGNORE_FLAGS): #filepath
    if (not os.path.exists(fp)):
        time.sleep(3)
    
        
    f = open(fp)

    cnt = [0 for i in range(len(startFlags))]
    
    for line in f.readlines():
        for i in range(len(startFlags)):
            flag = startFlags[i]
            if (line.startswith(flag)):
                cnt[i] += 1

    #print "counter="+str(counter) 
    return cnt;

if __name__=="__main__":
#    cnt = getUpdateNum(fp = UPDATE_FILE)
#    for i in range(len(cnt)):
#        print "i=",i," counter="+str(cnt[i])

    x,y, z = getUpdateNum(fp=UPDATE_FILE)
    print x
    print y
    print z
