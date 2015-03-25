#! /bin/bash 

# Not tested, so don't trust this script
cd /home/pi/
git clone github:sampoz/symfoni-hockey.git
cd symfoni-hockey
sudo cp rc.local_example /etc/rc.local
crontab crontab # install crontab
sudo apt-get install python-pip
sudo pip install -r requirements.txt
sudo apt-get install python-serial
