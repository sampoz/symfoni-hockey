#! /bin/bash 

# Not tested, so don't trust this script
cd /home/pi/
git clone github:sampoz/symfoni-hockey.git
sudo cp rc.local_example /etc/rc.local
crontab crontab # install crontab
