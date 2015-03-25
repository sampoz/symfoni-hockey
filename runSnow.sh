 #!/bin/bash

# Used to make sure that snow_serial.py runs

if ps -ef | grep -v grep | grep snow_serial ; then
        exit 0
else
	sudo python /home/pi/symfoni-hockey/snow_serial.py >> /home/pi/symfoni-hockey/snow.log & 
        exit 0
fi
