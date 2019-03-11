#!/usr/bin/env python3
#############################################################################
####################### Sonoff LAN devices to MQTT bridge ###################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import sonofflan
import sl2m_net
import sl2m_mqtt
import time
import sys, signal, os
import json

sonoffs = []
PERIODIC_CHECK_INTERVAL = 0
MQTT_TOPIC_PUB = ""
MQTT_TOPIC_SUB = ""

def signal_handler(signal, frame):
 global sonoffs
 try:
  for s in range(len(sonoffs)):
   if sonoffs[s] is not None:
    sonoffs[s].disconnect()
 except:
  pass
 sys.exit(0)

def is_device_connected(ipaddr):
 global sonoffs
 darr = []
 dconn = False
 for s in range(len(sonoffs)):
  if sonoffs[s] is not None:
   if sonoffs[s].connected==False:
    darr.append(s)
   elif sonoffs[s].host == ipaddr:
    dconn = True
    break
 if len(darr)>0:
  for d in reversed(range(len(darr))):
   sid = darr[d]
   print("Remove disconnected device: ",sonoffs[sid].host)
   del sonoffs[sid]
 return False

def device_search():
 global sonoffs, ssettings

 sdevs = sl2m_net.Discover()
 sonoff_ips = sdevs.discover()
 for i in range(len(sonoff_ips)):
  if is_device_connected(sonoff_ips[i])==False:
   s = sonofflan.SonoffLAN(sonoff_ips[i])
   try:
    s.connect()
    time.sleep(0.5)
    if s.connected:
     sonoffs.append(s)
     print("Connected to "+sonoff_ips[i])
     s.add_event_handler(sonoff_callback)
     if ssettings["mqtt_type"]=="domoticz":
      for i in range(len(ssettings["device_idx_list"])):
       if ssettings["device_idx_list"][i]["sonoff_device_id"]==s.getid():
        s.idx[0] = ssettings["device_idx_list"][i]["idx"]["outlet0"]
        s.idx[1] = ssettings["device_idx_list"][i]["idx"]["outlet1"]
        s.idx[2] = ssettings["device_idx_list"][i]["idx"]["outlet2"]
        s.idx[3] = ssettings["device_idx_list"][i]["idx"]["outlet3"]
        break
    else:
     s.on_close()
   except:
    pass

def mqtt_callback(did,val,outlet=0):
 global ssettings, sonoffs
# print("From MQTT:",did,val,outlet)
 if ssettings["mqtt_type"]=="domoticz":
  for s in range(len(sonoffs)):
   for i in range(len(sonoffs[s].idx)):
    if int(sonoffs[s].idx[i])==int(did):
     sonoffs[s].setstate(int(val[0]),i,True)
#     print(sonoffs[s].deviceid,did,int(val[0]))
     break
 else:
  for s in range(len(sonoffs)):
   if str(sonoffs[s].deviceid)==str(did):
    sonoffs[s].setstate(int(val),int(outlet))
#    print("MQTT",sonoffs[s].deviceid,did,int(val))
    break

def sonoff_callback(host,devid,outlet,state):
 global mqttcontroller, ssettings, sonoffs
 for s in range(len(sonoffs)):
   if sonoffs[s].getid()==devid:
    if ssettings["mqtt_type"]=="domoticz":
      mqttcontroller.senddata(sonoffs[s].idx[outlet],state)
    else:
      mqttcontroller.senddata2(sonoffs[s].deviceid,outlet,state)
#      print("sd2",sonoffs[s].deviceid,devid,int(state))
    break

# print(host,devid,outlet,state)

signal.signal(signal.SIGINT, signal_handler)
try:
 with open("sonofflan2mqtt.json") as f:
  ssettings = json.load(f)
  PERIODIC_CHECK_INTERVAL = ssettings["periodic_check_interval"]
except Exception as e:
 print("sonofflan2mqtt.json can not be read! ",str(e))
 ssettings = []

device_search()
ctime = time.time()
print("Sonoff LAN enabled devices found: ",len(sonoffs))

try:
 MQTT_TOPIC_PUB = ssettings["mqtt_topic_pub"].strip()
 MQTT_TOPIC_SUB = ssettings["mqtt_topic_sub"].strip()
 if ssettings["mqtt_type"]=="domoticz":
  if ssettings["mqtt_topic_pub"].strip()=="":
   MQTT_TOPIC_PUB = "domoticz/in"
  if ssettings["mqtt_topic_sub"].strip()=="":
   MQTT_TOPIC_SUB = "domoticz/out"
 if ssettings["mqtt_type"]=="shelly":
   MQTT_TOPIC_PUB = "shellies/"
   MQTT_TOPIC_SUB = "shellies/#"
 if ssettings["mqtt_address"]:
  mqttcontroller = sl2m_mqtt.Controller(ssettings["mqtt_address"],ssettings["mqtt_port"], ssettings["mqtt_type"],MQTT_TOPIC_PUB,MQTT_TOPIC_SUB,ssettings["mqtt_user"],ssettings["mqtt_password"])
  mqttcontroller.controller_init(True,mqtt_callback)
  for s in range(len(sonoffs)):
   for o in range(sonoffs[s].outletnum):
    sonoff_callback(sonoffs[s].host,sonoffs[s].deviceid,o,sonoffs[s].getstate(o))
except Exception as e:
 print("MQTT setup failed",str(e))
 mqttcontroller = None
 sys.exit(0)

while True:
 if PERIODIC_CHECK_INTERVAL>0 and time.time()-ctime>PERIODIC_CHECK_INTERVAL:
  device_search()
  ctime = time.time()
  print("Periodic checker found",len(sonoffs),"device")
 if PERIODIC_CHECK_INTERVAL==0 and time.time()-ctime>30:
  for s in range(len(sonoffs)):
   if sonoffs[s] is not None:
    if sonoffs[s].connected==False:
     print("Trying to reconnect",sonoffs[s].host)
     sonoffs[s].reconnect()
  ctime = time.time()
 time.sleep(1)
