#!/bin/bash

read -p "Setup WiFi network auto reconnect?`echo $'\n[Y/n]?'``echo $'\n> '`" answer
if [[ $answer = Y ]] || [[ $answer = y ]] ; then
    # http://weworkweplay.com/play/rebooting-the-raspberry-pi-when-it-loses-wireless-connection-wifi/
	sudo cp checkwifi.sh /usr/local/bin/checkwifi.sh
    sudo chmod 775 /usr/local/bin/checkwifi.sh
    read -p "Copy the following line and paste it at the bottom of the /tmp/crontab.rDmnwm/crontab file in the Nano editor. Press ENTER once you've copied it:`echo $'\n\n*/5 * * * * /usr/bin/sudo -H /usr/local/bin/checkwifi.sh >> /dev/null 2>&1\n\n'``echo $'\n> '`" copy
    if [[ $copy = "" ]]; then
        crontab -e
    else
        echo "You pressed '$key'"
    fi

fi

read -p "Install project Python requirements?`echo $'\n[Y/n]?'``echo $'\n> '`" answer
if [[ $answer = Y ]] || [[ $answer = y ]] ; then
    sudo pip install -r ../requirements.txt
fi

sudo chmod 777 ../bin/foyodo
