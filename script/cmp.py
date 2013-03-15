import os, os.path
ROOT_PATH = os.path.split(os.path.realpath(__file__))[0]

TRACE_FILE = os.path.join(ROOT_PATH, "../output/app-delays-trace.txt")
DATA_LINE_IGNORE_FLAG = "#"


def cmp(fp= TRACE_FILE):
    f = open(fp)
   
    lastsum = 0.0
    fullsum = 0.0
    diffcnt = 0
    retxsum = 0
    hopsum = 0
    
    seqmax = -1
    
    last = None;
    full = None;
    prev = None
    
    dic = {}
    lines = f.readlines();
    for j in range(len(lines)):
        line = lines[j]
        line = line.strip()
        
        if line=="" or line.startswith("DATA_LINE_IGNORE_FLAG") or line.startswith("Time"):
            continue
        parts = line.split()
        assert len(parts) == 9, "line="+str(j)+" len(parts)="+str(len(parts))+" 8 is OK"
        
        nod = parts[1]
        seq = int(parts[3])
        typ = parts[4]
        val = parts[6]
        retx = int(parts[7])
        hop = int(parts[8])
        
        
        
        if typ == "FullDelay":
            full = parts
            assert last != None
            if last[0] != full[0] or last[1] != full[1] or last[2] != full[2]:
                print "line:"+str(j)+" error "+ line
                #continue
            
            if last[5] != full[5]:
                #print line
                diffcnt += 1

            fullsum += float(val)
            retxsum += retx
            hopsum += hop
            
            
        elif typ == "LastDelay":
            last = parts
            lastsum += float(val)
            
            if seq > seqmax:
                seqmax = seq
            key = parts[0]+"-"+parts[1]+"-"+parts[2]
#            if dic.has_key(key):
#                dic[key] += 1
#            else:
#                dic[key] = 1

        else:
            assert fale, "type="+typ
            
        if prev!= None and prev[3] == parts[3]:
           print "type error line:"+str(j)+" error "+ line
        
        prev = parts
    
    #print "fullsum="+str(fullsum)+", lastsum="+str(lastsum)+" records:"+str(len(lines))+" diffcnt="+str(diffcnt)
    rd = float(len(lines)/2)
    avglast = lastsum/rd
    avgfull = fullsum/rd
    avghop = hopsum/rd
    avgretx = retxsum/rd
    #print "fullsum avg="+str(fullsum/rd)+", lastsum avg="+str(lastsum/rd)+", hop avg="+str(hopsum/float(rd))+", retx avg="+str(retxsum/float(rd))
    
    #print "seqMax="+str(seqmax)
    for k, v in dic.iteritems():
        if v > 1:
            print "key="+str(k)+" value="+v

    return [rd, avglast, avgfull, avghop, avgretx]

def recordcmp(fp1, fp2):
    
    dic1 = fill(fp1)
    dic2 = fill(fp2)
    same = {}
    
    
    for key in dic1.keys():
        if dic2.has_key(key):
            
            if (dic1[key] != dic2[key]):
                print "key="+str(key)+" dic1[key]="+str(dic1[key])+" dic2[key]="+str(dic2[key])
            else:
                same[key] = dic1[key]
                del dic1[key]
                del dic2[key]
        else:
            #print "key"+str(key) +" not in dic2"
            pass
    
    #printall(same)
    print "dic1"
    #printall(dic1)
    print "dic2"
    #printall( dic2)
    print "len(same)="+str(len(same))+" len(dic1)="+str(len(dic1))+" len(dic2)="+str(len(dic2))

def fill(fp):
    f = open(fp)
    lines = f.readlines()
    dic = {}
    for i in range(len(lines)):
        line = lines[i] 
        parts = line.split()
        key = parts[0]+"-"+parts[1]+"-"+parts[2]
        if parts[2] !="252":
            pass
            #continue
        
        if dic.has_key(key):
            dic[key] += 1
            #print "error"
        else:
            dic[key] = 1
    #dic.iteritems()
    return dic

def printall(dic):
    #dic = sorted(dic.items(), key=lambda x: x[1])
    for key, val in dic.iteritems():
        if val > 1:
            print "key="+str(key)+" value="+str(dic[key])
        
        
if __name__ == "__main__":
    print "testing"
    #cmp(fp=TRACE_FILE)
    
    print "Nack enable"
    fp1 = os.path.join(ROOT_PATH, "../output/Nack-enable.txt")
    cmp(fp=fp1)
    
    print "Nack disable"
    fp2 = os.path.join(ROOT_PATH, "../output/Nack-disable.txt")
    cmp(fp=fp2)
    
    recordcmp(fp1, fp2)