# Connecting real devices to TheLogWatch (cloud version)

You need two values from Render → your service → **Environment**:
- `SERVER` = your Render URL, e.g. `https://logwatch-api.onrender.com`
- `KEY` = the `INGEST_KEY` value

The dashboard's **Connect devices & phones** button shows both, pre-filled.

## Why a relay?
Routers and Raspberry Pis send logs as **syslog over UDP** on the local network. Render (and every
similar host) only accepts HTTPS, so those logs can't reach it directly. `syslog_relay.py` runs on
the booth laptop, listens for syslog, and forwards everything to the server over HTTPS.

```
router / Pi  --UDP 5514-->  booth laptop (syslog_relay.py)  --HTTPS-->  Render API  -->  MongoDB
Windows PC   --------------------HTTPS (windows_forwarder.ps1)-------->  Render API
phones       --------------------HTTPS (phone page on Netlify)-------->  Render API
```

```sh
python3 syslog_relay.py --server SERVER --key KEY
```
It prints the laptop's address. Use that address below. Name devices by IP in `devices.json`.

## OpenWRT router
```sh
uci set system.@system[0].log_ip='LAPTOP_IP'
uci set system.@system[0].log_port='5514'
uci set system.@system[0].log_proto='udp'
uci commit system && /etc/init.d/log restart
```
Or LuCI: *System → System → Logging → External system log server*.
Live moments: join a new phone to its Wi-Fi, type the LuCI password wrong 5 times, enable UPnP.

## Consumer routers (Netgear, TP-Link, ASUS)
*Administration → System Log → Remote syslog server* = the laptop IP. Most only send to port 514, so
run the relay as admin/sudo with `--port 514`.

## Raspberry Pi / Linux
```sh
echo '*.* @LAPTOP_IP:5514' | sudo tee /etc/rsyslog.d/90-logwatch.conf && sudo systemctl restart rsyslog
```
Or skip the relay and send straight to the cloud:
`journalctl -f -o short | python3 send_log.py --server SERVER --key KEY --source linux --device "Pi" -`

## Windows PC (goes straight to the cloud, no relay)
Admin PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\windows_forwarder.ps1 -Server SERVER -Key KEY
```
Live moments: wrong password at the lock screen a few times;
`net user demo_intruder P@ssw0rd123! /add` (then `net user demo_intruder /delete`).

## Phones
Visitors scan the QR code from **Connect devices & phones**. The link carries the ingest key, so
only people at the booth can send. Rotate `INGEST_KEY` in Render after the event.

## Any file or command
```sh
python3 send_log.py --server SERVER --key KEY --source router --device "Home router" router.log
curl -X POST "SERVER/api/ingest?source=browser&device=Laptop" -H "X-Ingest-Key: KEY" --data-binary @history.log
```
