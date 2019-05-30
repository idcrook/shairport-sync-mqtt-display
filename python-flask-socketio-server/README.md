`python-flask-socketio-server` is a [Flask](http://flask.pocoo.org) webapp which uses [MQTT](https://www.eclipse.org/paho/clients/python/) and [socket.io](https://github.com/miguelgrinberg/Flask-SocketIO) to serve [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata. It has remote-control support and works great with Apple Music®<sup id="a1">[1](#f1)</sup>

If you use [`shairport-sync`](https://github.com/mikebrady/shairport-sync), you should be able to get this webapp working.

![Safari screencap](screenshot1.png)

Quickstart
==========

First, some requirements

1.	*AirPlay®*
	-	iTunes® on a computer can use AirPlay®. The *Music* app in iOS™ works too
2.	*`shairport-sync`* as AirPlay® receiver
	-	`shairport-sync` needs to be built with *MQTT support*. See [wiki - Build shairport-sync](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support)
3.	*MQTT broker*
	-	An MQTT broker, like `mosquitto`, visible on same network. See [wiki - Configure MQTT broker](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Configure-mosquitto-MQTT-broker)
4.	*Webserver*
	-	A computer with Python™3 that can run this webserver app (tested on macOS™)

2., 3., and 4. can all be on the same computer, for example, a Raspberry Pi®

For our purposes, we are assuming a Raspberry Pi running Raspbian `stretch`. And the rest of this "quickstart" depends on the requirements 1.) 2.) and 3.) being met.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

let's go
--------

```bash
# Install a python3 dev setup and other libraries
sudo apt install -y python3-dev python3-pip python3-venv \
python3-setuptools python3-wheel git mosquitto-clients

# test MQTT broker access, from two different bash sessions
# .. mosquitto_sub ...
# .. mosquitto_pub ...

git clone https://github.com/idcrook/shairport-sync-mqtt-display.git
cd shairport-sync-mqtt-display
# now proceed to the next section: "install"
```

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
pip install wheel # not required; avoids a pyyaml benign build error
pip install pyyaml
```

config
------

```shell
cp config.example.yaml config.secrets.yaml
$EDITOR config.secrets.yaml # $EDITOR would be nano, vi, etc.
```

1.	Configure the MQTT section (`mqtt:`) to match your setup.

	-	For the `topic`, I use something like `shairport-sync/SSHOSTNAME`
		-	`SSHOSTNAME` is the name of where `shairport-sync` is running
		-	Note, there is **no** leading slash ('`/`') in the `topic` string
		-	`topic` needs to match the `mqtt.topic` string in your `/etc/shairport-sync.conf` file
	-	Use the same mqtt broker for `host` that you did in your MQTT broker config testing and `shairport-sync.conf`

2.	Customize the webpage UI section (`webui:`) if desired.

running
=======

Assumed music playing using AirPlay® (e.g. iTunes®), an MQTT broker, and `shairport-sync` with MQTT support, are already online. Also assumes that `config.yaml` has been configured to match your environment.

```bash
# this is the python virtual environment we installed into
source env/bin/activate
python app.py
# open it in your web browser, e.g.: open http://0.0.0.0:8080
```

Use IP address to connect from [other devices on your network](#connecting-across-home-network)

troubleshooting
---------------

Plan to gather here any troubleshooting guidance that comes up.

### troubleshooting running

If you get an error like

```
socket.gaierror: [Errno -2] Name or service not known
```

you should add the mqtt broker host that you are using to `/etc/hosts`, for example something like.

```
192.168.1.42 rpi
```

#### connecting across home network

To connect from across your home network, you will need to use the LAN IP address of your webserver computer. Placed in an URL, it might be something like `http://192.168.1.42:8080`.

The commands `ifconfig` or `ip addr show` can reveal host IP addresses.

future ideas
============

Moved to [issues](https://github.com/idcrook/shairport-sync-mqtt-display/issues) and managed there.

inspired by
===========

-	MQTT metadata support released in [`shairport-sync` 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)
-	many examples using the older metadata Unix pipe technique, including https://github.com/idubnori/shairport-sync-trackinfo-reader

#### Development

Original development setup:

-	iTunes® streaming to (multiple, simultaneous) Raspberry Pi (`shairport-sync`\)
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send cover artwork and parsed metadata
-	`app.py` running on macOS
	-	connected to MQTT broker over home LAN
	-	tested on python3.7 installed from Homebrew
	-	Safari browser on macOS™, iOS™
-	`app.py` also tested on a Raspberry Pi running Raspbian `stretch`/`python3.5`

---

<i id="f1">1</i>: Trademarks are the respective protperty own their owners.[⤸](#a1)
