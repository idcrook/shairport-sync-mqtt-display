`python-flaschen-taschen`
==============================

![](photo.png "running")

Let's Go!
---------

For our purposes, this guide assumes:

-	Raspberry Pi running Raspbian `buster`
-	with AirPlay receiver and MQTT broker running on same Raspberry Pi as this webapp.

See [wiki](https://github.com/idcrook/shairport-sync-mqtt-display/wiki) for additional pointers.

Requirements
------------

Install system python dependencies and clone this repo. See [REQUIREMENTS Quickstart](../REQUIREMENTS.md#quickstart)

Install
-------

We rely on python3's built-in `venv` module for python library dependencies, and PIL [Pillow — documentation](https://pillow.readthedocs.io/en/stable/) for image manipulation.

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
--------------

in terminal

```console
$ make FT_BACKEND=terminal
$ ./ft-server -D32x32 --hd-terminal
UDP-server: ready to listen on 1337
```

on rgb-matrix

```shell
make FT_BACKEND=rgb-matrix
sudo ./ft-server --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=2 --led-rows=32 --led-cols=32 --led-show-refresh --led-brightness=50
```

Automatically launch on boot
--------------------------------------

There's a `systemd` service file at `/etc/shairport-sync_rgb-matrix-server.service` in this git repository.

There's a `systemd` service file at `/etc/shairport-sync_rgb-matrix-client.service` in this git repository.

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

---
