#!/usr/bin/python

# Rob Convery
#
# Listens to the serial port (with XRF Connected), publishes the temp values
# and updates the corresponding rrd file
 
import mosquitto
import os
import time
import serial
import datetime
import rrdtool
import re
from time import sleep

broker = "127.0.0.1"
tcpport = 1883

baud = 9600
port = '/dev/ttyAMA0'
ser = serial.Serial(port, baud, timeout=0)
rrddir = '/home/convery/rrd-data/'

def on_message(mosq, obj, msg):
	print("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)
	if re.search("WeatherStation/OutsideTemp", msg.topic):
		print "Command Sent:"
	elif re.search("Water", msg.topic):
		print "Command Sent:"
	else:
		print "No Match for "+msg.topic

mypid = os.getpid()
client_uniq = "pubclient_"+str(mypid)
mqttc = mosquitto.Mosquitto(client_uniq)

def on_connect(mosq, obj, rc):
    if rc == 0:
        print("Connected successfully.")

#define the callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

#connect to broker
mqttc.connect(broker, tcpport, 60)

#subscribe to topic test
mqttc.subscribe("WeatherStation", 2)

#remain connected and publish
while mqttc.loop() == 0:
	llapMsg = ser.read(12)
	if len(llapMsg) == 12:
		now = datetime.datetime.now()
		mqttc.publish("TempSensors", llapMsg)
		if re.search("^a\w\w\w\w", llapMsg):
			if re.search("TMPA", llapMsg):
				rrdfile = llapMsg[1:7] 
				value = llapMsg[7:12]
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| Updating RRD - File: ' + rrdfile + '.rrd with temperature value: ' + value
				rrdtool.update(rrddir + 'XRFTemp/' + rrdfile + '.rrd','N:' + str(value));
				if re.search("TATMPA", llapMsg):
					print now.strftime("%Y-%m-%d %H:%M:%S ") + 'Publish on /TempSensors/Nursery'
					mqttc.publish("/TempSensors/Nursery", value)
				elif re.search("TBTMPA", llapMsg):
                                        print now.strftime("%Y-%m-%d %H:%M:%S ") + 'Publish on /TempSensors/LivingRoom'
                                        mqttc.publish("/TempSensors/LivingRoom", value)
				elif re.search("TCTMPA", llapMsg):
                                        print now.strftime("%Y-%m-%d %H:%M:%S ") + 'Publish on /TempSensors/MasterBedroom'
                                        mqttc.publish("/TempSensors/MasterBedroom", value)
				elif re.search("TDTMPA", llapMsg):
                                        print now.strftime("%Y-%m-%d %H:%M:%S ") + 'Publish on /TempSensors/Porch'
                                        mqttc.publish("/TempSensors/Porch", value)
			elif re.search("BATTLOW", llapMsg):
				sensor = llapMsg[1:3]
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| Warning Sensor ' + sensor + ' has low battery'
			elif re.search("WAKE", llapMsg):
				sensor = llapMsg[1:3]
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| Sensor ' + sensor + ' waking'
			elif re.search("BATT", llapMsg):
				rrdfile = llapMsg[1:7]
				value = llapMsg[7:11]
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| Updating RRD - File: ' + rrdfile + '.rrd with battery voltage: ' + value
				rrdtool.update(rrddir + 'XRFBattery/' + rrdfile + '.rrd','N:' + str(value));
			elif re.search("SLEEPING", llapMsg):
				sensor = llapMsg[1:3]
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| Sensor ' + sensor + ' sleeping'
			else:
				print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| a..... No match'
		else:
			print now.strftime("%Y-%m-%d %H:%M:%S ") + 'String = |' + llapMsg + '| No match'
	sleep(0.5)
ser.close()
