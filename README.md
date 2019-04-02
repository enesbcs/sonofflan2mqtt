# SonoffLAN2MQTT

Sonoff LAN mode devices to MQTT bridge. 

It's a proof of concept project, discovering all Sonoff devices in the same LAN, that entered to LAN mode, and collecting and forwarding commands sent to it/arriving from them to an MQTT broker for further processing. Primarily targeted to Domoticz MQTT.
Based on [my Wireshark adventures](https://bitekmindenhol.blog.hu/2018/08/31/sonoff_lan_uzemmod) and [Andrew Beveridge's pysonofflan program ](https://github.com/beveradb/pysonofflan) which is very nice, but as i see it has a blocking nature. This bridge can handle multiple Sonoff devices at the same time with websockets and multithreading. (multithreading in Domoticz python plugin system is not supported as i know, this is the reason why i am unable to make a simple python plugin from it)

**This will only work for Sonoff devices running a recent version of the stock (Itead / eWeLink) firmware, which have been blocked from accessing the internet (to put them in LAN Mode).**

Please refer to the official tutorial on how to enter LAN mode on Sonoff devices:

https://help.ewelink.cc/hc/en-us/articles/360007134171-LAN-Mode-Tutorial#h3

Supported devices:

https://help.ewelink.cc/hc/en-us/articles/360007134171-LAN-Mode-Tutorial#h2


# Installation
```
    git clone https://github.com/enesbcs/sonofflan2mqtt.git
    cd sonofflan2mqtt
    sudo apt install python3-pip
    sudo pip3 install websocket-client paho-mqtt
    ./sonofflan2mqtt.py
```
It's tested on Ubuntu but will also run on other Debian/Raspbian and similar Linux OS.

Make sure, that every device lost it's internet connection and nobody connected to them, as only 1 client can be connect to a LAN device at the same time!

# Setup
Open sonofflan2mqtt.json file with your favourite text editor and set "mqtt_address" with your Mqtt broker's IP address, then the necessary port, user and password settings. If you set "mqtt_type" to domoticz than the subscribe and publish topic's will be filled automatically by the program, it can be leaved empty.
The "device_idx_list" has to be filled manually. At the first run you will se several lines that lists the found Sonoff devices (if you succesfully setted them up to enter into LAN mode) and it's Device ID's. This has to be entered into the JSON settings file, with the Domoticz device IDX's that you created for controlling them. 

For example: on a Sonoff S20 ID 10003b90001 "outlet0" is the first and only relay, so if you created a device IDX 45 in Domoticz, you have to write "outlet0":45, at the right line filling with the right sonoff device id. 
Then restart the sonofflan2mqtt application and now you are able to control this socket changing the state of the IDX 45 device.

If it works you have to make the sonofflan2mqtt.py script to auto start at system boot time.
