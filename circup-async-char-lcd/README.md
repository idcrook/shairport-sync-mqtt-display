![Display of now playing song track info](photo1.jpg)

`circup-async-char-lcd` works in conjunction with [`shairport-sync`](https://github.com/mikebrady/shairport-sync) + MQTT and an Adafruit<sup id="a1">[1](#f1)</sup> 16x2 Character LCD Display on a Raspberry Pi. It has remote-control support.

If you can build [`shairport-sync`](https://github.com/mikebrady/shairport-sync) from source on your Raspberry Pi, you should be able to get this working.

Before we begin
===============

First, see [REQUIREMENTS](../REQUIREMENTS.md) for your home network.

For app developement, Adafruit's [Adafruit RGB Negative 16x2 LCD+Keypad Kit for Raspberry Pi](https://www.adafruit.com/product/1110) LCD Pi Plate was used.

let's go
--------

For our purposes, this guide assumes a Raspberry Pi running Raspbian `bullseye` running on same Raspberry Pi where the display app runs.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

Quickstart
----------

Install system python dependencies and clone this repo. See [REQUIREMENTS Quickstart](../REQUIREMENTS.md#quickstart)


install
-------

python3's `venv` module is used for maintaining our dependencies.

```bash
sudo apt install python3-pip
sudo apt install python3-venv
cd circup-async-char-lcd/
python3 -m venv .venv
source .venv/bin/activate
pip3 install adafruit-circuitpython-charlcd
pip3 install paho-mqtt
pip3 install tomli

# required for backlight color analysis
pip3 install colorthief
sudo apt install libtiff5      # needed on stretch
sudo apt install libopenjp2-7  # needed on buster
sudo apt install libopenjp2-7  # needed on bullseye
```

config
------

Copy the example config file and customize.

```shell
cp config.example.toml config.secrets.toml
$EDITOR config.secrets.toml # $EDITOR would be nano, vi, etc.
```

1.	Configure the MQTT section (`mqtt:`) to reflect your environment.

	-	For the `topic`, I use something like `shairport-sync/SSHOSTNAME`
		-	this `topic` needs to match the `mqtt.topic` string in your `/etc/shairport-sync.conf` file
		-	`SSHOSTNAME` is the name of where `shairport-sync` is running
		-	Note, there is **no** leading slash ('`/`') in the `topic` string
	-	Use the same mqtt broker for `host` that you did in your MQTT broker config testing and `shairport-sync.conf`

2.	Customize the UI and remote control sections if desired.

running
=======

Assumed music playing using AirPlay® (e.g. iTunes®), an MQTT broker, and `shairport-sync` with MQTT support are already online. Also assumes that `config.toml` has been configured to match your home network environment.

```bash
# this is the python virtual environment we installed into
source .venv/bin/activate
python mqtt_lcd_display.py
# info should be displayed on the lcd
```

Automatically launch webserver on boot
--------------------------------------

There's a `systemd` service file at `circuitpython_char_lcd/etc/shairport-sync_charlcd.service` in this git repository.

The file's header includes instructions that can be used to install the python script as a `systemd` service. In this way, it will run automatically at boot-up. It will automatically serve metadata when `shairport-sync` configured for MQTT metadata is an AirPlay® target.

troubleshooting?
----------------

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

future ideas
============

Moved to [issues](https://github.com/idcrook/shairport-sync-mqtt-display/issues) and managed there.

inspired by
-----------

-	MQTT metadata support released in [`shairport-sync` 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)

Development
-----------

`circuitpython_char_lcd` is a [CircuitPython](http://circuitpython.org) (via Blinka) script which uses [MQTT](https://www.eclipse.org/paho/clients/python/) to display [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata. It has remote-control support and works great with Apple Music®

Original development setup:

-	*iTunes®* and Airfoil Airplay-ing to Raspberry Pi(s).
-	Raspberry Pi Model 3 B
	-	running `mosquitto` MQTT broker
	-	running `shairport-sync`, configured with MQTT to send [cover artwork and parsed metadata](https://github.com/idcrook/shairport-sync-mqtt-display/wiki/Build-shairport-sync-with-MQTT-support#salient-pieces-of-a-working-config-file)
-	Raspberry Pi Model B with a 16x2 CharLCD and keypad

	-	yes, an "original" Model B which was first sold in 2012
	-	running `mqtt_lcd_display.py`
	-	deployed on a Raspberry Pi running Raspberry Pi OS `bullseye`/`python3.9`
	-	Useful docs:
		-	[Character LCDs - Python & CircuitPython Usage](https://learn.adafruit.com/character-lcds/python-circuitpython#python-and-circuitpython-usage-7-12)
		-	[Adafruit 16x2 Character LCD + Keypad for Raspberry Pi - Python Usage](https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/python-usage)

---

<i id="f1">1</i>: Trademarks are the respective property of their owners.[⤸](#a1)
