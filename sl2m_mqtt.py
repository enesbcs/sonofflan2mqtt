#############################################################################
############################## MQTT controller ##############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import paho.mqtt.client as mqtt
import time
import json

class Controller():

 def __init__(self,address,port,mtype,pubchannel,subchannel,controlleruser="",controllerpassword=""):
  self.controllerip   = address
  self.controllerport = port
  self.pubchannel = pubchannel
  self.subchannel = subchannel
  self.mtype = mtype
  self.mqttclient = None
  self.lastreconnect = 0
  self.connectinprogress = 0
  self.laststatus = -1
  self.keepalive = 60
  self.controlleruser=controlleruser
  self.controllerpassword=controllerpassword
  self.onmsgcallbackfunc = None

 def controller_init(self,enablecontroller=None,callback=None):
  if enablecontroller != None:
   self.enabled = enablecontroller
  self.connectinprogress = 0
  try:
   ls = self.laststatus
  except:
   self.laststatus = -1
  self.onmsgcallbackfunc = callback
  self.mqttclient = DMQTTClient()
  self.mqttclient.subscribechannel = self.subchannel
  self.mqttclient.controllercb = self.on_message
  self.mqttclient.connectcb = self.on_connect
  self.mqttclient.disconnectcb = self.on_disconnect
  if self.controllerpassword=="*****":
   self.controllerpassword=""
  self.initialized = True
  if self.enabled:
   if self.isconnected()==False:
    print("MQTT: Try to connect")
    self.connect()
  else:
   self.disconnect()
  return True

 def connect(self):
  if self.enabled and self.initialized:
   if self.isconnected():
    print("Already connected force disconnect!")
    self.disconnect()
   self.connectinprogress = 1
   self.lastreconnect = time.time()
   if (self.controlleruser!="" or self.controllerpassword!="") and (self.isconnected() == False):
    self.mqttclient.username_pw_set(self.controlleruser,self.controllerpassword)
    print("Set MQTT password")
   try:
    kp = self.keepalive
   except:
    self.keepalive = 60
   try:
    self.mqttclient.connect(self.controllerip,int(self.controllerport),keepalive=self.keepalive) # connect_async() is faster but maybe not the best for user/pass method
    self.mqttclient.loop_start()
   except Exception as e:
    print("MQTT controller: "+self.controllerip+":"+str(self.controllerport)+" connection failed "+str(e))
  return self.isconnected()

 def disconnect(self):
   try:
    self.mqttclient.loop_stop(True)
   except:
    pass
   try:
    self.mqttclient.disconnect()
   except:
    pass
   stat=self.isconnected()
   if self.enabled!=True:
    print("MQTT Disconnected")
   return stat

 def isconnected(self,ForceCheck=True):
  res = False
  if self.enabled and self.initialized:
   if ForceCheck==False:
    return self.laststatus
   if self.mqttclient is not None:
    gtopic = self.pubchannel
    gval   = "PING"
    mres = 1
    try:
     (mres,mid) = self.mqttclient.publish(gtopic,gval)
    except:
      mres = 1
    if mres==0:
     res = 1 # connected
    else:
     res = 0 # not connected
   if res != self.laststatus:
    if res==0:
     print("MQTT Disconnected")
    else:
     print("MQTT Connected")
    self.laststatus = res
   if res == 1 and self.connectinprogress==1:
    self.connectinprogress=0
  return res

 def on_message2(self, msg):
  success = False
  tstart = self.subchannel[:len(self.subchannel)-1]
  if msg.topic.startswith(tstart) and ("sonoff" in msg.topic) and msg.topic.endswith("/command"):
   msg2 = msg.payload.decode('utf-8')
   try:
    tend = msg.topic[len(self.subchannel)-1:]
    dnames = tend.split("/")
   except:
    dnames = []
   if len(dnames)>2:
    did = dnames[0].split("-")
    if "on" in msg2.lower() or msg2.strip()=="1":
     oval=1
    else:
     oval=0
    self.onmsgcallbackfunc(did[1],oval,dnames[2])

 def on_message(self, msg):
  if self.mtype!="domoticz":
   self.on_message2(msg)
   return True
  msg2 = msg.payload.decode('utf-8')
  list = []
  if ('{' in msg2):
   try:
    list = json.loads(msg2)
   except Exception as e:
    print("JSON decode error:"+str(e)+str(msg2))
    list = []
  if (list) and (len(list)>0):
   try:
    if list['Type'] == "Scene": # not interested in scenes..
     return False
   except:
    pass
   devidx = -1
   nvalue = "0"
   svalue = ""
   decodeerr = False
   tval = [-1,-1,-1,-1]
   try:
    devidx = str(list['idx']).strip()
   except:
    devidx = -1
    decodeerr = True
   try:
    nvalue = str(list['nvalue']).strip()
   except:
    nvalue = "0"
    decodeerr = True
   try:
    svalue = str(list['svalue']).strip()
   except:
    svalue = ""
   if (';' in svalue):
    tval = svalue.split(';')
   tval2 = []
   for x in range(1,4):
    sval = ""
    try:
     sval = str(list['svalue'+str(x)]).strip()
    except:
     sval = ""
    if sval!="":
     tval2.append(sval)
   if len(tval2)==1 and svalue=="":
    svalue=tval2[0]
   else:
    for y in range(len(tval2)):
      matches = re.findall('[0-9]', tval2[y])
      if len(matches) > 0:
       tval[y] = tval2[y]
   forcesval1 = False
   try:
    if list['switchType'] == "Selector":
     forcesval1 = True
   except:
    forcesval1 = False
   if (tval[0] == -1) or (tval[0] == ""):
    if (float(nvalue)==0 and svalue.lower()!="off" and svalue!="") or (forcesval1):
     tval[0] = str(svalue)
    else:
     tval[0] = str(nvalue)
   if decodeerr:
    print("JSON decode error: "+msg2)
   else:
    self.onmsgcallbackfunc(devidx,tval)

 def senddata2(self,devid,outlet,value):
  if self.enabled:
   mStates = ["off","on"]
   if self.isconnected(False):
     stateid = int(float(value))
     gtopic = self.pubchannel
     if self.mtype=="shelly":
      gtopic += "sonoff-"+str(devid)+"/relay/"+str(outlet)
     elif self.mtype=="generic":
      gtopic += "sonoff-"+str(devid)+"/"+str(outlet)
     msg = mStates[stateid]
     mres = 1
     try:
       (mres,mid) = self.mqttclient.publish(gtopic,msg)
     except:
       mres = 1
     if mres!=0:
       self.isconnected()
   else:
    print("MQTT not connected, sending failed.")
    if (time.time()-self.lastreconnect)>30:
     self.connect()

 def senddata(self,idx,value):
  if self.enabled:
   mStates = ["Off","On"]
   domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'
   if self.isconnected(False):
    if int(idx) > 0:
     stateid = int(float(value))
     msg = domomsg.format(str(idx), int(stateid), mStates[stateid])
     mres = 1
     try:
       (mres,mid) = self.mqttclient.publish(self.pubchannel,msg)
     except:
       mres = 1
     if mres!=0:
       self.isconnected()
    else:
     print("MQTT idx error, sending failed.")
   else:
    print("MQTT not connected, sending failed.")
    if (time.time()-self.lastreconnect)>30:
     self.connect()

 def on_connect(self):
  if self.enabled and self.initialized:
   self.isconnected()
  else:
   self.disconnect()

 def on_disconnect(self):
  if self.initialized:
   self.isconnected()

class DMQTTClient(mqtt.Client):
 subscribechannel = ""
 controllercb = None
 disconnectcb = None
 connectcb = None

 def on_connect(self, client, userdata, flags, rc):
  try:
   self.subscribe(self.subscribechannel,0)
   if self.connectcb is not None:
    self.connectcb()
  except Exception as e:
   print("MQTT connection error: "+str(e))
  try:
   rc = int(rc)
  except:
   rc=-1
  if rc !=0:
   estr = str(rc)
   if rc==1:
      estr += " Protocol version error!"
   if rc==3:
      estr += " Server unavailable!"
   if rc==4:
      estr += " User/pass error!"
   if rc==5:
      estr += " Not authorized!"
   print("MQTT connection error: "+estr)

 def on_disconnect(self, client, userdata, rc):
  if self.disconnectcb is not None:
    self.disconnectcb()

 def on_message(self, mqttc, obj, msg):
  if self.controllercb is not None:
   self.controllercb(msg)
