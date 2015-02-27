import serial
import suds
import RPi.GPIO as GPIO
import time
import os
import glob
import socket
import ping

isCalibrated=False


def main():
        try:
                print 'Starting program:'

		# find usable serial ports
		ports = scan()
		print "Found ports:"
		for name in scan(): print name
		if len(ports) < 2:
			raise IOError("Missing usb com ports, found "+str(len(ports)) +" ports, was expecting 2") 
                ser = serial.Serial(ports[0], timeout=1)
                ser1 = serial.Serial(ports[1], timeout=1)
                
		#setup soap 
		url = 'https://topten.service-now.com/u_hockey_goals.do?WSDL'
                urlUpdateIp = 'https://symfonidemofl.service-now.com/u_hockey_raspberry_ip.do?WSDL'
		client = suds.client.Client(url, username='Hockey_admin', password='0!739Ac75N6*b81z')
		updateIpClient= suds.client.Client(urlUpdateIp, username='Hockey_admin', password='0!739Ac75N6*b81z')
                
		#Led pin setup
		#led1
		GPIO.setup(18, GPIO.OUT)
                GPIO.output(18, False)
		#led2
		GPIO.setup(7, GPIO.OUT) #minus of led2
		GPIO.output(7, False)
		GPIO.setup(15, GPIO.OUT) #plus of led2
                GPIO.output(15, False)

		#update ip
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('google.com', 0))
		ipString = socket.gethostbyname(s.getsockname()[0])
		print ipString
		updateIpClient.service.insert(u_ip = ipString)
		
		#test ping
		testPing()
		i=0

		#calibrate goal ports
		global isCalibrated
		while (isCalibrated == False):
			print "Waiting for calibration"
			GPIO.output(18, False)			
			GPIO.output(15, True)
			time.sleep(1)
			if ser.inWaiting()>0:
                                print "Calibrated port for Away Team"
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
				print "Calibrated port for Away Team"
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
                while (True):
			i+=1
			GPIO.output(18, False)
                        if ser.inWaiting()>0:
                                client.service.insert(u_goal = 'Suomi')
                                print "ja joukkue oli Suomi!"
				time.sleep(7)
				ser.flushInput()
                        if ser1.inWaiting()>0:
                                print "ja joukkue oli Ruotsi"
                                client.service.insert(u_goal = 'Ruotsi')
				time.sleep(7)
				ser1.flushInput()
                        GPIO.output(18, True)
			time.sleep(0.1)
			if i%100==0:
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
		delay = ping.Ping('www.google.com', timeout=2000).do()
	except IOError, e:
		GPIO.output(15, False)
		raise IOError("Network not working, could not ping google, error was "+ str(e))
	print "Google works, delay was "+ str(delay)
	GPIO.output(15, True)

try:
	main()
except KeyboardInterrupt:
                GPIO.output(15, False)
                GPIO.output(18, False)
                print "User terminated program"
                exit()


