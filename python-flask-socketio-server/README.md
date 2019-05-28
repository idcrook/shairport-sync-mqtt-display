[Flask](http://flask.pocoo.org) app which includes [MQTT](https://www.eclipse.org/paho/clients/python/) and [socket.io](https://github.com/miguelgrinberg/Flask-SocketIO) to serve [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata.

![Safari screencap](screenshot1.png)

install
=======

on computer where you want to run python webserver (in a git clone of this repo)

```bash
cd python-flask-socketio-server
python3 -m venv env
source env/bin/activate
pip install flask
pip install flask-socketio
pip install paho-mqtt
pip install pyyaml
```

config
------

```
cp config.example.yaml config.secrets.yaml
$EDITOR  config.secrets.yaml
```

run
===

Assumed that an MQTT broker, `shairport-sync` with MQTT support, and music playing using AirPlay® (e.g. iTunes®) are already online.

```bash
source env/bin/activate
python app.py
# connect to webserver, e.g.:  open http://0.0.0.0:8080
```

### Development

My development setup:

-	iTunes streaming to (muliple, simultaneous) Raspberry Pi (`shairport-sync`\)
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send cover artwork and parsed metadata
-	this webserver `app.py` running on macOS
	-	connected to MQTT broker over home LAN
	-	tested on python3.7 installed from Homebrew
	-	Safari browser on macOS

See no reason that webserver itself couldn't run on a Raspberry Pi, just haven't tested that.

future ideas
============

1.	Add websockets support
	-	should be simple matter of adding `eventlet` lib?
2.	Add support or example for displaying to character LCD display
3.	Add playback controls?
4.	add smarter player state observation / display

inspired by
===========

-	MQTT metadata support released in [`shairport-sync` 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)
-	https://github.com/idubnori/shairport-sync-trackinfo-reader which utilizes older metadata pipe technique
