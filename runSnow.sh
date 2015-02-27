 #!/bin/bash

# Used to make sure that snow_serial.py runs

if ps -ef | grep -v grep | grep snow_serial ; then
        exit 0
else
        sleep 10
	python /home/pi/snow_hockey/snow_serial.py >> /home/pi/snow_hockey/snow.log & 
        exit 0
fi
