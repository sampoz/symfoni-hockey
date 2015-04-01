# Symfoni hockey hardware
* Remember to add to Crontab and to /etc/rc.local, see rc.local_example
* Remember to configure keys for git 

# Hardware
* Raspberry pi 2
* Raspbian Release date:2015-02-16

# Pin Layout
* Board Pin 7: Home goal +
* Board Pin 9: Home goal - (ground)

* Board Pin 8: Away goal +
* Board Pin 6: Away goal - (ground)

* Board Pin 12: Script running led +
* Board Pin 14: Script running led . (ground)

* Board Pin 23: Internet OK led +
* Board Pin 25: Internet OK led - (ground)


# Installation instructions
* dd Raspbian image to sd-card
* Configure environment ( expand, keyboard-layout, hostname)
* scp .ssh to pi
* pull from github
* install python-pip, sudo apt-get install python-pip
* run sudo pip install -r requirements.txt 
* install crontab with "crontab crontab"
 

# TODO
* Install rc
* Install update hook

# SNC Instance side 
* create soap user
* grant roles(symfoni hockey + soap)
