`python-flask-socketio-server` is a [Flask](http://flask.pocoo.org) webapp which uses [MQTT](https://www.eclipse.org/paho/clients/python/) and [socket.io](https://github.com/miguelgrinberg/Flask-SocketIO) to serve [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata. It has remote-control support and works great with Apple Music®<sup id="a1">[1](#f1)</sup>

If you use [`shairport-sync`](https://github.com/mikebrady/shairport-sync), you should be able to get this webapp working.

![Safari screencap](screenshot1.png)

Quickstart
==========

First, some requirements for your home network.

1.	*AirPlay®*
	-	iTunes® on a computer. Music* app in iOS™. Rogue Amoeba's [Airfoil](https://rogueamoeba.com/airfoil/) app too (which works with Spotify, e.g.)
2.	*`shairport-sync`* as AirPlay® receiver
	-	`shairport-sync` needs to be built with *MQTT support*. See [wiki - Build shairport-sync](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support)
3.	*MQTT broker*
	-	An MQTT broker, like `mosquitto`, visible on same network. See [wiki - Configure MQTT broker](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Configure-mosquitto-MQTT-broker)
4.	*Webserver*
	-	Computer with Python 3 that can run this webserver app 

2., 3., and 4. can all be on the same computer, for example, a Raspberry Pi®

For Quickstart purposes, we are assuming a Raspberry Pi running Raspbian `stretch`, with the system `python3.5` used. And the rest of this "quickstart" depends on the requirements 1.) 2.) and 3.) being met.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

let's go
--------

```bash
# Install a python3 dev setup and other libraries
sudo apt install -y python3-pip python3-venv \
python3-setuptools python3-wheel git mosquitto-clients

# Validate MQTT broker config. E.g., from two different bash sessions:
# .. mosquitto_sub ...
# .. mosquitto_pub ...

git clone https://github.com/idcrook/shairport-sync-mqtt-display.git
cd shairport-sync-mqtt-display
# now proceed to the next section: "install"
```

install
=======

Steps to run on computer for webserver (in a git clone of this repo). We rely on python3's built-in `venv` module for dependencies.

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

Copy the example config file and customize.

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

Assumed music playing using AirPlay® (e.g. iTunes®), an MQTT broker, and `shairport-sync` with MQTT support are already online. Also assumes that `config.yaml` has been configured to match your home network environment.

```bash
# this is the python virtual environment we installed into
source env/bin/activate
python app.py
# open it in your web browser, e.g.: open http://0.0.0.0:8080
```

Use IP address (in place of `0.0.0.0`) to connect from [other devices on your network](#connecting-across-home-network)

#### Automatically start on boot

There's a `systemd` service file at `python-flask-socketio-server/etc/shairport-sync_web.service`

It includes instructions in its header that can be used to install the python webserver as a system service., so it will run automatically at boot-up.

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
-	many projects using `shairport-sync`'s older metadata pipe technique, including https://github.com/idubnori/shairport-sync-trackinfo-reader for styling inspiration

#### Development

Original development setup:

-	iTunes® streaming to Raspberry Pi(s)
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send [cover artwork and parsed metadata](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support#salient-pieces-of-a-working-config-file) 
-	`app.py` 
	-	configured to connect to MQTT broker
	-	developed in python3.7 installed from Homebrew on macOS Mojave
	-	also tested on a Raspberry Pi running Raspbian `stretch`/`python3.5`
-	Client app in Safari browser on macOS™, Mobile Safari on iOS™ 9 and iOS™ 12. Chrome.

---

<i id="f1">1</i>: Trademarks are the respective property of their owners.[⤸](#a1)
