`python-flaschen-taschen`
=========================

![](photo.png "running")

Let's Go!
---------

For our purposes, this guide might assume:

-	Raspberry Pi Model 3 B running Raspbian `buster`
-	AirPlay receiver (`shairport-sync`) and MQTT broker (`mosquitto`) running on same Raspberry Pi as the helper utilities.

Requirements
------------

Install system python dependencies and clone this repo. See [REQUIREMENTS Quickstart](../REQUIREMENTS.md#quickstart)

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

Install
-------

We rely on python3's built-in `venv` module for python library dependencies.

The album art manipulation will be handled by PIL (Python Imaging Library) [Pillow](https://pillow.readthedocs.io/en/stable/).

```shell
sudo apt install python3-pillow
cd ~/projects/shairport-sync-mqtt-display
cd python-flaschen-taschen
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

Testing
-------

Install and use the libraries used in [Adafruit tutorial](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi) for *Adafruit RGB Matrix + Real Time Clock HAT*.

Borrowing from the tutorial:

```shell
mkdir -p ~/projects/rgb-matrix
cd  ~/projects/rgb-matrix

curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh >rgb-matrix.sh
sudo bash rgb-matrix.sh
```

Respond to the prompts. A reboot may be needed when complete. This will clone the `hzeller/rpi-rgb-led-matrix` repo from GitHub.

-	See [GitHub - hzeller/rpi-rgb-led-matrix: Controlling up to three chains of 64x64, 32x32, 16x32 or similar RGB LED displays using Raspberry Pi GPIO](https://github.com/hzeller/rpi-rgb-led-matrix)

Run a demo (assuming your Pi + HAT + LED Matrix are powered and hooked up correctly)

```
cd  ~/projects/rgb-matrix
cd rpi-rgb-led-matrix/examples-api-use

sudo ./demo -D0 --led-rows=32 --led-cols=32 --led-slowdown-gpio=2 --led-brightness=50
```

If all goes well, an animated rotating square will be depicted on the LED panel.

flaschen-taschen
----------------

The `flaschen-taschen` project is a client/server system for managing LED matrix display output.

-	See [GitHub - hzeller/flaschen-taschen: Noisebridge Flaschen Taschen display](https://github.com/hzeller/flaschen-taschen)

```shell
cd  ~/projects/rgb-matrix
git clone --recursive https://github.com/hzeller/flaschen-taschen.git

cd flaschen-taschen
```

### Server

#### Output in Terminal

works great with [iTerm2 - macOS Terminal Replacement](https://iterm2.com/).

```console
$ cd  ~/projects/rgb-matrix/flaschen-taschen/server
$ make FT_BACKEND=terminal
$ ./ft-server -D32x32 --hd-terminal
UDP-server: ready to listen on 1337
```

#### Output on LED Matrix

```console
$ cd  ~/projects/rgb-matrix/flaschen-taschen/server
$ make FT_BACKEND=rgb-matrix
# sudo ./ft-server --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=2 --led-rows=32 --led-cols=32 --led-show-refresh --led-brightness=50
```

### Client

FIXME:

This is command line examples, demo apps, and finally the app found here (it acts as a client).

Automatically launch on boot
----------------------------

FIXME:

There's a `systemd` service file at `/etc/shairport-sync_rgb-matrix-server.service` in this git repository.

There's a `systemd` service file at `/etc/shairport-sync_rgb-matrix-client.service` in this git repository.

troubleshooting running
-----------------------

#### Name or service not known

If you get an error like

```
socket.gaierror: [Errno -2] Name or service not known
```

you should add the mqtt broker host that you are using to `/etc/hosts` on the computer that is running this client app. For example, an entry like:

```
192.168.1.42 	mqtthostname
```

---
