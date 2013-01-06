import sys
import threading
import time


class Se:
    
    pass

def write():
    self = Se()
    self.id = "0"
    self.t0 = time.time()
    self.t1 = time.time()
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
        pass
        #log.info("sending mail finished")
write()