#############################################################################
######################## Sonoff LAN devices library #########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#

import websocket # sudo pip3 install websocket-client
import threading
import time
import random
from typing import Dict
import json

switch_states = ['off','on']

class SonoffLAN:
 def __init__(self,host,port=8081,event_handler=None):
  self.host = host
  self.port = port
  self.ws = None
  self.wst = None
  self.event_handler = event_handler
  self.connected = False
  self.deviceid = None
  self.outlets = [-1,-1,-1,-1]
  self.outletnum = 0
  self.idx = [0,0,0,0]

 def connect(self):
  websocket_address = 'ws://%s:%s/' % (self.host, self.port)
#  websocket.enableTrace(True) # DEBUG ONLY
  protocol_str = "Sec-WebSocket-Protocol: chat"
  self.ws = websocket.WebSocketApp(websocket_address, on_open= self.send_online_message, on_message = self.on_message, on_close = self.on_close, on_error=self.on_error, header = [protocol_str])
  self.wst = threading.Thread(target=self.ws.run_forever)
  self.wst.daemon = True
  self.connected = True
  self.wst.start()

 def add_event_handler(self,event_handler):
  self.event_handler = event_handler

 def getid(self):
  return self.deviceid

 def getstate(self,outletnum=0):
  if outletnum < self.outletnum:
   return self.outlets[outletnum]
  else:
   return -1

 def setstate(self,state,outletnum=0,Outbound=False):
  global switch_states
  if self.ws.sock.connected:
    params = ""
    if self.outletnum==1 and state in [0,1]:
     params = {'switch':switch_states[state]}
    elif self.outletnum>1:
     params = {'switches':[]}
     for o in range(self.outletnum):
      if outletnum==o:
        params['switches'].append({'switch':switch_states[state],'outlet':o})
      else:
        astate = self.outlets[o]
        if astate in [0,1]:
         params['switches'].append({'switch':switch_states[astate],'outlet':o})
    json_data = json.dumps(self.get_update_payload(self.deviceid, params))
#    print(json_data) # DEBUG only
    self.ws.send(json_data)
    self.statechanged(outletnum,state,Outbound)
  else:
    self.connected = False
    return False

 def statechanged(self,num,state,Outbound=False):
  if self.outlets[num] != state:
   self.outlets[num] = state
   if Outbound==False:
    ehok = False
    if self.event_handler is not None:
     try:
      self.event_handler(self.host,self.deviceid,num,state)
      ehok = True
     except:
      ehok = False
    if ehok==False:
     print("Event handler undefined for device! IP:",self.host,"Sonoff device ID:",self.deviceid,"Outlet:",num,"State:",switch_states[state])

 def send_online_message(self):
   if self.ws is not None and self.ws.sock.connected:
    json_data = json.dumps(self.get_user_online_payload())
    self.ws.send(json_data)
   else:
    self.connected = False
    print(self.host," not connected")

 def on_message(self,message):
  try:
   if str(message)!="" and "{" in message:
    response = json.loads(message)
   else:
    response = ""
  except:
   response = ""
  if self.deviceid is None:
   if ('error' in response and response['error'] == 0) and 'deviceid' in response:
    self.deviceid = response['deviceid']
    print("Device ID received! IP:",self.host,"Sonoff device ID:")
    self.outletnum = 1
  if ('action' in response and response['action'] == 'update'):
   if 'switches' in response['params']:
    for o in range(len(response['params']['switches'])):
     num = response['params']['switches'][o]['outlet']
     if 'off' in response['params']['switches'][num]['switch']:
      state = 0
     else:
      state = 1
     self.statechanged(num,state)
     if num>(self.outletnum-1):
      self.outletnum = num+1
   elif 'switch' in response['params']: # only one outlet
     if 'off' in response['params']['switch']:
      state = 0
     else:
      state = 1
     self.statechanged(0,state)
#  print("MSG: ",response) # DEBUG

 def on_error(self,error):
  if self.host is not None and self.deviceid is not None:
#   print(self.host,self.deviceid,str(error))
   self.disconnect()
  self.connected = False

 def on_close(self):
  if self.connected:
   valid = True
  else:
   valid = False
  self.disconnect()
  if self.deviceid is not None and valid:
   print(self.host,self.deviceid," disconnected")

 def disconnect(self,Force=False):
  self.connected = False
  try:
   if self.ws is not None:
    self.ws.keep_running = False
    self.ws.close()
  except:
   pass

 def reconnect(self):
   self.disconnect()
   time.sleep(0.1)
   self.connect()

 def get_user_online_payload(self) -> Dict:
  return {
            'action': "userOnline",
            'userAgent': 'app',
            'version': 6,
            'nonce': ''.join([str(random.randint(0, 9)) for _ in range(15)]),
            'apkVesrion': "1.8",
            'os': 'Android',
            'at': 'at',  # No bearer token needed in LAN mode
            'apikey': 'apikey',  # No apikey needed in LAN mode
            'ts': str(int(time.time())),
            'model': 'D410_w7',
            'romVersion': '7.1.2',
            'sequence': str(time.time()).replace('.', '')
  }

 def get_update_payload(self, deviceid: str, params: dict) -> Dict:
  return {
            'action': 'update',
            'userAgent': 'app',
            'params': params,
            'apikey': 'apikey',  # No apikey needed in LAN mode
            'deviceid': deviceid,
            'sequence': str(time.time()).replace('.', ''),
            'controlType': 4,
            'ts': 0
  }


 