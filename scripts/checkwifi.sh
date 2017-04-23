# http://weworkweplay.com/play/rebooting-the-raspberry-pi-when-it-loses-wireless-connection-wifi/
# /usr/local/bin/checkwifi.sh
# sudo chmod 775 /usr/local/bin/checkwifi.sh
# crontab -e
# */5 * * * * /usr/bin/sudo -H /usr/local/bin/checkwifi.sh >> /dev/null 2>&1

ping -c4 192.168.1.1 > /dev/null
 
if [ $? != 0 ] 
then
    echo "No network connection, restarting wlan0"
    /sbin/ifdown 'wlan0'
    sleep 5
    /sbin/ifup --force 'wlan0'
fi
