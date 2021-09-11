`python-flask-socketio-server`
==============================

![Safari screencap - Dark mode on iPhone SE](screenshot1.png "Dark mode on iPhone SE")

-	Works along with [`shairport-sync`](https://github.com/mikebrady/shairport-sync) to host a webapp.

-	Webapp displays Airplay®<sup id="a1">[1](#f1)</sup> track metadata.

	-	Has remote-control support and works on mobile browsers.

-	If you use can build [`shairport-sync`](https://github.com/mikebrady/shairport-sync) from source, you should be able to get this webapp working.

Before we begin
===============

First, see [REQUIREMENTS](../REQUIREMENTS.md) for your home network.

One final requirement: A computer or other device with a web browser to display the live-streamed webpage.

Quickstart
----------

Install system python dependencies and clone this repo. See [REQUIREMENTS Quickstart](../REQUIREMENTS.md#quickstart)

Install
-------

We rely on python3's built-in `venv` module for python library dependencies.

```shell
cd ~/projects/shairport-sync-mqtt-display
cd python-flask-socketio-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

Copy the example config file (`config.example.yaml`) to a new file and customize.

```shell
cp config.example.yaml config.secrets.yaml
$EDITOR config.secrets.yaml # $EDITOR would be nano, vi, etc.
```

#### Configure the MQTT section (`mqtt:`) to reflect your environment.

For the *`topic`*, I use something like `shairport-sync/SS_HOSTNAME`

-	*`topic`* needs to match the `mqtt.topic` string in your `/etc/shairport-sync.conf` file
-	`SS_HOSTNAME` is name of server where `shairport-sync` is running
-	Note, there is **no** leading slash ('`/`') in the `topic` string

Use the same mqtt broker for `host` that you did in your MQTT broker config testing and `shairport-sync.conf`

You may need to add an entry for `mqtthostname` to  [/etc/hosts file](#name-or-service-not-known).

#### Customize the webpage UI section (`webui:`) if desired.

Controls like buttons appearing are set here.

### Testing / Running

Assumed music playing using AirPlay® (e.g. iTunes®), an MQTT broker, and `shairport-sync` with MQTT support are already online. Also assumes that `config.yaml` has been configured to match your home network environment.

```bash
cd ~/projects/shairport-sync-mqtt-display
cd python-flask-socketio-server
# this is the python virtual environment we installed into earlier
source venv/bin/activate
python app.py
# open it in your web browser, e.g.: open http://0.0.0.0:8080
```

Use IP address (in place of `0.0.0.0`) to connect from [other devices on your network](#browser-address-to-connect-to-on-home-network)

Here's an example startup

 > Using default cover image file /Users/dpc/projects/webdev/shairport-sync-mqtt-display/python-flask-socketio-server/static/img/default.png
 > Using config file /Users/dpc/projects/webdev/shairport-sync-mqtt-display/python-flask-socketio-server/config.yaml
 > shairport-sync/rpih1
 > Enabling MQTT logging
 > Connecting to broker rpihp1 port 1883
 > Starting webserver
 >    http://:::8080
 > WebSocket transport not available. Install eventlet or gevent and gevent-websocket for improved performance.
 > topic shairport-sync/rpih1/artist  * Serving Flask app "app" (lazy loading)
 > 1
 >  * Environment: production
 > topic shairport-sync/rpih1/album    WARNING: This is a development server. Do not use it in a production deployment.
 >    Use a production WSGI server instead.
 >  * Debug mode: off
 > 2
 > topic shairport-sync/rpih1/title 3
 > topic shairport-sync/rpih1/genre 4
 > topic shairport-sync/rpih1/songalbum 5
 > topic shairport-sync/rpih1/volume 6
 > topic shairport-sync/rpih1/client_ip 7
 > topic shairport-sync/rpih1/active_start 8
 > topic shairport-sync/rpih1/active_end 9
 > topic shairport-sync/rpih1/play_start 10
 > topic shairport-sync/rpih1/play_end 11
 > topic shairport-sync/rpih1/play_flush 12
 > topic shairport-sync/rpih1/play_resume 13
 > topic shairport-sync/rpih1/cover 14
 >  * Running on http://[::]:8080/ (Press CTRL+C to quit)

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

you should add the mqtt broker host that you are using to `/etc/hosts` on the computer that is running this Flask webserver app. For example, an entry like:

```
192.168.1.42 mqtthostname
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
