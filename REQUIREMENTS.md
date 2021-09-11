Requirements
============

These are helpers for exposing *Apple*<sup id="a1">[1](#f1)</sup> *AirPlay®* metadata.

All the utilities rely on [`shairport-sync`](https://github.com/mikebrady/shairport-sync) + MQTT configured with metadata support.

Hardware and Network Requirements
=================================

Before we begin, first, some requirements for your home network. Requirements 2., 3., and 4. can all be hosted on the same computer, including a single Raspberry Pi®

1.	*AirPlay®* source<sup id="a2">[2](#f2)</sup>

2.	*`shairport-sync`* as AirPlay® receiver

	-	`shairport-sync` needs to be built with *MQTT support*.
	-	It also needs to properly configured to connect to MQTT broker.
	-	See [wiki - Build shairport-sync with MQTT support on Raspberry Pi](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support-on-Raspberry-Pi)

3.	*MQTT broker*

	-	An MQTT broker, like `mosquitto`, visible on same network.
	-	See [wiki - Configure MQTT broker](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Configure-mosquitto-MQTT-broker)

4.	*Renderer*

	-	*Webserver* for `python-flask-socketio-server`

		-	Any computer that can run this Python 3-based Flask app (tested on macOS™ and Raspberry Pi OS)

	-	*Character LCD Display* for `circuitpython_char_lcd`

		-	A Raspberry Pi for running the [CircuitPython](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) script with a Character LCD display attached. A keypad for performing as a remote control is optional, but a nice feature.

	-	*HUB75 RGB LED Matrix Panel(s)* for `python-flaschen-taschen` -- and something to drive them

		-	A Raspberry Pi 3 B with a [Adafruit RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345) was used to develop, attached to a powered [32x32 RGB LED Matrix Panel - 6mm pitch](https://www.adafruit.com/product/1484) from Adafruit.

MQTT and shairport-sync config
------------------------------

For our purposes, these instructions assume or were tested with:

-	a Raspberry Pi running Raspberry Pi OS `buster`
-	AirPlay receiver (`shairport-sync`) and MQTT broker (`mosquitto`) running on same Raspberry Pi as the helper utilities.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

**IMPORTANT**: Validate your MQTT broker config. See [Configure MQTT broker - wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Configure-mosquitto-MQTT-broker) for one way to set up a broker.

As described above, `shairport-sync` will need to be built with MQTT and metadata support. See [wiki - Build shairport-sync with MQTT support on Raspberry Pi](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support-on-Raspberry-Pi)

Test something like the following, done by using two separate shell sessions:

```shell
sudo apt install mosquitto-clients
# .. mosquitto_sub ...
mosquitto_sub -v -d -h mqttbrokerhost -t test/topic1
# .. mosquitto_pub ...
mosquitto_pub    -d -h mqttbrokerhost -t test/topic1 -m "helo"
```

Quickstart
----------

Install python dependencies and clone this repository

```shell
# Install a python3 dev setup and other libraries
sudo apt install -y python3-pip python3-venv build-essential \
    python3-setuptools python3-wheel git

# place a clone of this repo in ~/projects/
mkdir ~/projects
cd ~/projects
git clone https://github.com/idcrook/shairport-sync-mqtt-display.git
cd shairport-sync-mqtt-display
```

now go back to the "install" section:

-	[circuitpython_char_lcd](circuitpython_char_lcd/README.md#install) install
-	[python-flaschen-taschen](python-flaschen-taschen/README.md#install) install
-	[python-flask-socketio-server](python-flask-socketio-server/README.md#install) install

Development setup
-----------------

Original development setup:

-	*iTunes®* and Airfoil Airplay-ing to Raspberry Pi(s).
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send [cover artwork and parsed metadata](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support#salient-pieces-of-a-working-config-file)

### `python-flask-socketio-server`

Since both **python** and web technologies are very cross-platform, development was done on both a *Mac* running *macOS* and a *Raspberry Pi Model 3 B* running *Raspberry Pi OS (buster)*

### `circuitpython_char_lcd`

Adafruit's [Adafruit RGB Negative 16x2 LCD+Keypad Kit for Raspberry Pi](https://www.adafruit.com/product/1110) LCD Pi Plate was used.

Useful docs:

-	[Character LCDs - Python & CircuitPython Usage](https://learn.adafruit.com/character-lcds/python-circuitpython#python-and-circuitpython-usage-7-12)
-	[Adafruit 16x2 Character LCD + Keypad for Raspberry Pi - Python Usage](https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/python-usage)

### `python-flaschen-taschen`

-	A Raspberry Pi 3 B with a [Adafruit RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345) was used to develop, attached to a powered [32x32 RGB LED Matrix Panel - 6mm pitch](https://www.adafruit.com/product/1484) from Adafruit.

Useful docs:

-	[Adafruit RGB Matrix + Real Time Clock HAT for Raspberry Pi | Adafruit Learning System](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi)
-	[hzeller/rpi-rgb-led-matrix: Controlling up to three chains of 64x64, 32x32, 16x32 or similar RGB LED displays using Raspberry Pi GPIO](https://github.com/hzeller/rpi-rgb-led-matrix)
-	[hzeller/flaschen-taschen: Noisebridge Flaschen Taschen display](https://github.com/hzeller/flaschen-taschen) - a network UDP client/server system for panel displaying.

---

<i id="f1">1</i>: Trademarks are the respective property of their owners.[⤸](#a1)

<i id="f2">2</i>: *AirPlay®* source could be

-	iTunes® or Music app in iOS™/macOS™
-	Rogue Amoeba's [Airfoil](https://rogueamoeba.com/airfoil/) app (which can even send Spotify artwork from macOS app)

[⤸](#a2)
