 ======================
 Installationsanleitung
 ======================
 
 ---------
 CRON-Jobs
 ---------
 
 Befehl:
 > crontab -e
 
 In Crontab-Datei eintragen:
 @reboot     python3 /home/pi/berry/Berry.py
 @reboot     wget --tries=1 -O - http://127.0.0.1:8081/modules/Clock.cmd?clock=run
 */5 * * * * wget --tries=1 -O - http://127.0.0.1:8081/modules/Clock.cmd?clock=run
