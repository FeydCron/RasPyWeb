 ======================
 Installationsanleitung
 ======================
 
 ---------
 CRON-Jobs
 ---------
 
 Befehl:
 > crontab -e
 
 In Crontab-Datei eintragen:
 @reboot         cd /home/pi && python3 -m raspyweb.RasPyWeb
 */5 * * * *     wget --tries=1 -O - http://127.0.0.1:8081/ext/evt.src?timer=cron
