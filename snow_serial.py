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

isCalibrated = False
instanceURL = 'https://symfonik15.service-now.com'
user = 'soap.hockey'
soapPassword = '10L2M6fSN4JnHcH5ccq1'
goal_interval = 5
def main():
        try:
            print 'Starting program:'
            print subprocess.check_output("date") # log time
            #Find usable serial ports
            ports = scan()
            print "Found ports:"
            for name in scan(): print name
            if len(ports) < 2:
                raise IOError("Missing usb com ports, found "+str(len(ports)) +" ports, was expecting 2") 
            ser = serial.Serial(ports[0], timeout=1)
            ser1 = serial.Serial(ports[1], timeout=1)
                    
            #Setup soap 
            global instanceURL
            global user
            global soapPassword
            url = instanceURL + '/u_symfoni_hockey_goal.do?WSDL'
            urlUpdateIp = instanceURL + '/u_symfoni_hockey_raspberry_pi_status.do?WSDL'
            client = suds.client.Client(url, username=user, password=soapPassword)
            #Setup threads
            home_goal_thread = goal_thread(client=client, u_goal_post=0)
            away_goal_thread = goal_thread(client=client, u_goal_post=1)
            updateIpClient= suds.client.Client(urlUpdateIp, username=user, password=soapPassword)
            home_goal_thread.start()
            away_goal_thread.start()
            print"Got wsdls and set up clients"                

            #Led pin setup
            #Set GPIO numbering scheme to be BOARD (pin numbers, not names)
            GPIO.setmode(GPIO.BOARD) 
            #Setup leds
            GPIO.setup(7, GPIO.OUT) #Home Goal led
            GPIO.setup(8, GPIO.OUT) #Away Goal led
            GPIO.setup(12, GPIO.OUT)#Script Running led
            GPIO.setup(23, GPIO.OUT)#Internet OK led
            #Turn all leds off 
            GPIO.output(7, False) 
            GPIO.output(8, False)
            GPIO.output(12, False)
            GPIO.output(23, False)
            #Turn script status led on 
            GPIO.output(12, True)
            #update ip and send logs
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('google.com', 0))
            ipString = socket.gethostbyname(s.getsockname()[0])
            print ipString
            #Client status update threads
            client_start_thread = sender_thread(client=updateIpClient, u_ip=ipString, u_startup="true")
            client_start_thread.run()
            client_update_thread = sender_thread(client=updateIpClient, u_ip=ipString, u_startup="")
            #test ping
            ping_update_thread = ping_thread(url="www.google.com")
            ping_update_thread.start()
            ping_update_thread.run()
            #calibrate goal ports
            global isCalibrated
            while (isCalibrated == False):
                print "Waiting for calibration"
                GPIO.output(7, False)          
                GPIO.output(8, True)
                time.sleep(1)
                if ser.inWaiting()>0:
                    print "Calibrated port for Away(1) Team"
                    time.sleep(goal_interval)
                    ser.flushInput()
                    ser1.flushInput()
                    ser1.close()
                    ser.close()
                    ser = serial.Serial(ports[0], timeout=1)
                    ser1 = serial.Serial(ports[1], timeout=1)
                    isCalibrated=True
                    GPIO.output(8, True)
                    GPIO.output(7, False)
                    time.sleep(0.5)
                    break
                if ser1.inWaiting()>0:
                    print "Calibrated port for Home(0) Team"
                    time.sleep(goal_interval)
                    ser.flushInput()
                    ser1.flushInput()
                    ser1.close()
                    ser.close()
                    ser1 = serial.Serial(ports[0], timeout=1)
                    ser = serial.Serial(ports[1], timeout=1)
                    isCalibrated=True
                    GPIO.output(7, True)
                    GPIO.output(8, False)
                    time.sleep(0.5)
                    break
                GPIO.output(7, True)
                GPIO.output(8, False)
                time.sleep(1)
            GPIO.output(7, False)
            GPIO.output(8, False)

            #main loop
            i=0
            while (True):
                i+=1
                if ser.inWaiting()>0:
                    print "Home goal"
                    wiggle_led(8, 15, False) # wiggle away led, leave it off
                    home_goal_thread.run()
                    time.sleep(4)
                    ser.flushInput()
                if ser1.inWaiting()>0:
                    print "Away goal"
                    wiggle_led(7, 15, False) # wiggle home led, leave it off
                    away_goal_thread.run()
                    time.sleep(4)
                    ser1.flushInput()
                time.sleep(0.01)
                if i%1000==0:
                    ping_update_thread.run()
                if i>4000:
                    client_update_thread.run()
                    i=0
            ser.close()
            ser1.close()
        except IOError, ioe: #handle serial port errors
            print "Caught IOError, " +str(ioe) +"\n Waiting 10s, then retrying" #change led color here
            time.sleep(10);
            main() 
        except Exception, e:
            free_leds()
            print e

def wiggle_led(port_number, amount, end_state):
    for n in range(0, amount):
        GPIO.output(port_number, True)
        time.sleep(0.1)
        GPIO.output(port_number, False)
        time.sleep(0.1)
    GPIO.output(port_number, end_state)

def free_leds():
    #Turn all leds off
    GPIO.output(7, False)
    GPIO.output(8, False)
    GPIO.output(12, False)
    GPIO.output(23, False)
    print "Program terminated with error " +str(e)
    exit()
    

def scan():
   # scan for available ports. return a list of device names.
   return glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

class sender_thread(threading.Thread):
        def __init__(self, **kwargs):
            threading.Thread.__init__(self)
            self.client = kwargs["client"]
            self.u_ip = kwargs["u_ip"]
            if "u_startup" in kwargs:
                self.u_startup = kwargs["u_startup"]
            else:
                self.u_startup = "false"
        def run(self):
            log =  subprocess.check_output(["tail", "-n 100", "/home/pi/symfoni-hockey/snow.log"])
            print self.client.service.insert(u_ip=self.u_ip, u_log_entry=log, u_startup=self.u_startup)
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
                    response = os.system("ping -c 1 -q -W 5 " + self.url) # q for quiet
                    #and then check the response...
                    if response == 0:
                        print self.url, 'is up!'
                        GPIO.output(23, True)
                    else:
                        print self.url, 'is down!'
                        GPIO.output(23, False)

            except IOError, e:
                    GPIO.output(23, False)
                    raise IOError('Network not working, could not ping ' + self.url +  ', error was ' + str(e))
            print "Pinged " + self.url 

try:
    main()
except KeyboardInterrupt:
                #Turn all leds off
                free_leds()
                print "User terminated program"
                exit()
except e:
                free_leds()
                print "Program exited with error " + str(e)
                exit()
        

