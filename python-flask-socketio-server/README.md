![Safari screencap - Dark mode on iPhone SE](screenshot1.png "Dark mode on iPhone SE")

`python-flask-socketio-server` works in conjunction with [`shairport-sync`](https://github.com/mikebrady/shairport-sync) to host a webapp that displays Airplay®<sup id="a1">[1](#f1)</sup> track metadata. It has remote-control support and works great on mobile browsers.

If you use [`shairport-sync`](https://github.com/mikebrady/shairport-sync) you should be able to get this webapp working.

Before we begin
===============

First, some requirements for your home network.

1.	*AirPlay®* source
	-	iTunes® on a computer. Music* app in iOS™. Rogue Amoeba's [Airfoil](https://rogueamoeba.com/airfoil/) app (which happens to work with Spotify app on macOS)
2.	*`shairport-sync`* as AirPlay® receiver
	-	`shairport-sync` needs to be built with *MQTT support*. See [wiki - Build shairport-sync](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support)
3.	*MQTT broker*
	-	An MQTT broker, like `mosquitto`, visible on same network. See [wiki - Configure MQTT broker](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Configure-mosquitto-MQTT-broker)
4.	*Webserver*
	-	Any computer that can run this Python 3-based webserver app (tested on macOS™ and Raspbian)

Requirements 2., 3., and 4. can all be hosted on the same computer, like a Raspberry Pi®, for example

One final requirement: A web-browser to display the served webpage.

let's go
--------

For our purposes, this guide assumes a Raspberry Pi running Raspbian `stretch`, with the above requirements 1.) 2.) and 3.) being already met, and with req's 2.) and 3.) running on same Raspberry Pi where the webserver app (4.) runs.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

Quickstart
----------

Install python dependencies and clone this repo

```bash
# Install a python3 dev setup and other libraries
sudo apt install -y python3-pip python3-venv \
python3-setuptools python3-wheel git mosquitto-clients

# Validate MQTT broker config. E.g., from two different bash sessions:
# .. mosquitto_sub ...
# .. mosquitto_pub ...

# grab a copy of this repo
git clone https://github.com/idcrook/shairport-sync-mqtt-display.git
cd shairport-sync-mqtt-display
# now proceed to the next section: "install"
```

install
-------

Steps to run on computer for webserver (in a git clone of this repo). We rely on python3's built-in `venv` module for dependencies.

```bash
cd python-flask-socketio-server
python3 -m venv env
source env/bin/activate
pip install flask
pip install flask-socketio
pip install wheel # not required; avoids pyyaml or paho-mqtt bdist_wheel error
pip install paho-mqtt
pip install pyyaml
```

config
------

Copy the example config file and customize.

```shell
cp config.example.yaml config.secrets.yaml
$EDITOR config.secrets.yaml # $EDITOR would be nano, vi, etc.
```

1.	Configure the MQTT section (`mqtt:`) to reflect your environment.

	-	For the `topic`, I use something like `shairport-sync/SSHOSTNAME`
		-	this `topic` needs to match the `mqtt.topic` string in your `/etc/shairport-sync.conf` file
		-	`SSHOSTNAME` is the name of where `shairport-sync` is running
		-	Note, there is **no** leading slash ('`/`') in the `topic` string
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

Use IP address (in place of `0.0.0.0`) to connect from [other devices on your network](#browser-address-to-connect-to-on-home-network)

Automatically launch webserver on boot
--------------------------------------

There's a `systemd` service file at `python-flask-socketio-server/etc/shairport-sync_web.service` in this git repository.

The file's header includes instructions that can be used to install the python webserver as a systemd service. In this way, it will run automatically at boot-up. It will automatically serve metadata when `shairport-sync` configured with MQTT metqadata is an AirPlay® target.

troubleshooting?
----------------

TODO: move troubleshooting section to wiki

troubleshooting running
-----------------------

#### Name or service not known

If you get an error like

```
socket.gaierror: [Errno -2] Name or service not known
```

you should add the mqtt broker host that you are using to `/etc/hosts` on the computer that is hosting the webserver apple. For example, and entry like:

```
192.168.1.42 rpi
```

#### Browser address to connect to on home network

To connect from across your home network, you will need to use the LAN IP address of your webserver computer. Placed in an URL, it might be something like `http://192.168.1.42:8080`.

The commands `ifconfig` or `ip addr show` can reveal host IP addresses.

future ideas
============

Moved to [issues](https://github.com/idcrook/shairport-sync-mqtt-display/issues) and managed there.

inspired by
-----------

-	MQTT metadata support released in [`shairport-sync` 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)
-	many projects using `shairport-sync`'s older metadata pipe technique, including https://github.com/idubnori/shairport-sync-trackinfo-reader for styling inspiration

Development
-----------

`python-flask-socketio-server` is a [Flask](http://flask.pocoo.org) webapp which uses [MQTT](https://www.eclipse.org/paho/clients/python/) and [socket.io](https://github.com/miguelgrinberg/Flask-SocketIO) to serve [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata. It has remote-control support and works great with Apple Music®

Original development setup:

-	*iTunes®* and Airfoil Airplay-ing to Raspberry Pi(s).
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send [cover artwork and parsed metadata](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support#salient-pieces-of-a-working-config-file)
	-	running `app.py`
-	`app.py`
	-	configured to connect to MQTT broker
	-	developed in `python3.7` installed from Homebrew on macOS Mojave
	-	deployed on a Raspberry Pi running Raspbian `stretch`/`python3.5`
-	Safari browser on *macOS*™, Mobile Safari on *iOS*™ 9 and *iOS*™ 12. Chrome.
	-	Dark mode tested in *macOS*™ Safari 12, *iOS*™ Mobile Safari 13

---

<i id="f1">1</i>: Trademarks are the respective property of their owners.[⤸](#a1)
