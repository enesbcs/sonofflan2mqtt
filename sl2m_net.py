#############################################################################
############################# Network library ###############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import threading
from contextlib import closing
import socket
import re
import os
import itertools

def get_ip():
   if os.name == "posix":
    f = os.popen('ifconfig')
    for iface in [' '.join(i) for i in iter(lambda: list(itertools.takewhile(lambda l: not l.isspace(),f)), [])]:
        #print('  -> ',iface)
        if re.findall('^(eth|wlan|enp|ens|enx|wlp|wls|wlx)[0-9]',iface) and re.findall('RUNNING',iface):
            if os.getenv('LANG')[0:2]=='de':
                ip = re.findall('(?<=inet\sAdresse:)[0-9\.]+',iface)
            else: # default 'en'
                ip = re.findall('(?<=inet\saddr:)[0-9\.]+',iface)
            if ip:
                return ip[0]
            else:
                ip = re.findall('(?<=inet\s)[0-9\.]+',iface) # support Arch linux
                if ip:
                 return ip[0]
   elif os.name == "nt":
    f = getoutput("ipconfig")
    ipconfig = f.split('\n')
    for line in ipconfig:
        if 'IPv4' in line:
            ip = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',line)
            if ip:
                return ip[0]
   return False

class Discover:
  def __init__(self,oip=None):
            if oip is None or oip == "":
             self.ownip = get_ip()
            else:
             self.ownip = oip
            self.hostaddr = self.ownip.split('.')[:-1]
            self.devices = []

  def discover(self):
        self.devices = []
        threads = []
        hostaddr = ""
        try:
            for host_num in range(1,255):
             hostaddr = '.'.join(self.hostaddr) + '.' + str(host_num)
             t = threading.Thread(target=self.check_port,args=(hostaddr,))
             threads.append(t)
             t.start()
            for th in threads:
             th.join()

        except Exception as ex:
            print("Caught Exception: ",str(ex))

        return self.devices

  def check_port(self, host):
    port = 8081
    opened = False
    try:
     with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        if sock.connect_ex((host, port)) == 0:
            #print("Port ",port," is open")
            self.devices.append(host)
            opened = True
    except Exception as e:
     print(e)
    return opened

 