# -*- coding: utf-8 -*-Ã
import serial
import suds
import RPi.GPIO as GPIO
import time
import os
import glob
import socket
import subprocess
import threading

isCalibrated=False
instanceURL='https://symfonik15.service-now.com'
user='soap.hockey'
soapPassword='10L2M6fSN4JnHcH5ccq1'
def main():
        try:
                print 'Starting program:'
		print subprocess.check_output("date") # log time
		# find usable serial ports
		ports = scan()
		print "Found ports:"
		for name in scan(): print name
		if len(ports) < 2:
			raise IOError("Missing usb com ports, found "+str(len(ports)) +" ports, was expecting 2") 
                ser = serial.Serial(ports[0], timeout=1)
                ser1 = serial.Serial(ports[1], timeout=1)
                
		#setup soap 
		global instanceURL
		global user
		global soapPassword
		url = instanceURL + '/u_symfoni_hockey_goal.do?WSDL'
                urlUpdateIp = instanceURL + '/u_symfoni_hockey_raspberry_pi_status.do?WSDL'
		client = suds.client.Client(url, username=user, password=soapPassword)
		home_goal_thread = goal_thread(client=client, u_goal_post=0)
		away_goal_thread = goal_thread(client=client, u_goal_post=1)
		updateIpClient= suds.client.Client(urlUpdateIp, username=user, password=soapPassword)
		print"Got wsdls and set up clients"                

		#Led pin setup
		#Set GPIO numbering scheme to be BOARD (pin numbers, not names)
		GPIO.setmode(GPIO.BOARD) 
		#led1
		GPIO.setup(18, GPIO.OUT)
                GPIO.output(18, False)
		#led2
		GPIO.setup(7, GPIO.OUT) #minus of led2
		GPIO.output(7, False)
		GPIO.setup(15, GPIO.OUT) #plus of led2
                GPIO.output(15, False)

		#update ip and send logs
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('google.com', 0))
		ipString = socket.gethostbyname(s.getsockname()[0])
		print ipString
		#get logs
		log =  subprocess.check_output(["tail", "-n 20", "/home/pi/symfoni-hockey/snow.log"])
		client_update_thread = sender_thread(client=updateIpClient, u_ip=ipString, u_log_entry=log)
		client_update_thread.start()
		#test ping
		ping_thread = ping_thread("www.google.com")
		ping_thread.run()

		#calibrate goal ports
		global isCalibrated
		while (isCalibrated == False):
			print "Waiting for calibration"
			GPIO.output(18, False)			
			GPIO.output(15, True)
			time.sleep(1)
			if ser.inWaiting()>0:
                                print "Calibrated port for Away(1) Team"
                                time.sleep(7)
                                ser.flushInput()
                                ser1.flushInput()
				ser1.close()
				ser.close()
				ser = serial.Serial(ports[0], timeout=1)
		                ser1 = serial.Serial(ports[1], timeout=1)
				isCalibrated=True
				break
                        if ser1.inWaiting()>0:
				print "Calibrated port for Home(0) Team"
                                time.sleep(7)
                                ser.flushInput()
				ser1.flushInput()
                                ser1.close()
                                ser.close()
                                ser1 = serial.Serial(ports[0], timeout=1)
                                ser = serial.Serial(ports[1], timeout=1)
				isCalibrated=True
				break
			GPIO.output(18, True)
                        GPIO.output(15, False)
			time.sleep(1)

		GPIO.output(18, True)
                GPIO.output(15, True)


		#main loop
		i=0
                while (True):
			i+=1
			GPIO.output(18, False)
                        if ser.inWaiting()>0:
				home_goal_thread.run()
                                print "Home goal"
				time.sleep(7)
				ser.flushInput()
                        if ser1.inWaiting()>0:
				away_goal_thread.run()
                                print "Away goal"
				time.sleep(7)
				ser1.flushInput()
                        GPIO.output(18, True)
			time.sleep(0.1)
			if i%1000==0:
				testPing()
			if i>4000:
				i=0
		GPIO.output(15, False)
                GPIO.output(18, False)
                ser.close()
                ser1.close()
	except IOError, ioe: #handle serial port errors
		print "Caught IOError, " +str(ioe) +"\n Waiting 10s, then retrying" #change led color here
		time.sleep(10);
		main() 
        except Exception, e:
                print e

def scan():
   # scan for available ports. return a list of device names.
   return glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

def testPing():
	print "testing ping"
	try:
		# Refactor ping
		testsite = "www.google.com"		
		response = os.system("ping -c 1 " + testsite)

		#and then check the response...
		if response == 0:
  			print testsite, 'is up!'
		else:
  			print testsite, 'is down!'
		
	except IOError, e:
		GPIO.output(15, False)
		raise IOError('Network not working, could not ping ' + testsite +  ', error was '+ str(e))
	GPIO.output(15, True)

class sender_thread(threading.Thread):
        def __init__(self, **kwargs):
            threading.Thread.__init__(self)
	    self.client = kwargs["client"]
	    self.u_ip = kwargs["u_ip"]
	    self.u_log_entry = kwargs["u_log_entry"]
        def run(self):
            self.client.service.insert(u_ip=self.u_ip, u_log_entry=self.u_log_entry)
	    print "Send ip to SNC instance from thread"

class goal_thread(threading.Thread):
        def __init__(self, **kwargs):
            threading.Thread.__init__(self)
            self.client = kwargs["client"]
            self.u_goal_post = kwargs["u_goal_post"]
        def run(self):
            self.client.service.insert(u_goal_post=self.u_goal_post)
            print "Send goal to post " + str(self.u_goal_post) + " from thread"

class ping_thread(threading.Thread):
        def __init__(self, **kwargs):
            threading.Thread.__init__(self)
            self.url = kwargs["url"]
        def run(self):
		        print "testing ping"
		        try:
		                response = os.system("ping -c 1 -q " + self.url) # q for quiet
		                #and then check the response...
		                if response == 0:
		                        print testsite, 'is up!'
		                else:
		                        print testsite, 'is down!'

		        except IOError, e:
		                GPIO.output(15, False)
		                raise IOError('Network not working, could not ping ' + testsite +  ', error was '$
		        GPIO.output(15, True)
	    print "Pinged " + url 

try:
	main()
except KeyboardInterrupt:
                GPIO.output(15, False)
                GPIO.output(18, False)
                print "User terminated program"
                exit()
	    

