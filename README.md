shairport-sync-mqtt-display
===========================

Utilities for displaying [`shairport-sync`](https://github.com/mikebrady/shairport-sync) metadata provided via MQTT<sup id="a1">[1](#f1)</sup>

Real-time webapp
----------------

[python-flask-socketio-server](python-flask-socketio-server) in this repo

![iOS screenshot](python-flask-socketio-server/screenshot1.png)

-	Python-based (Flask) webserver app
	-	Connects to MQTT broker and shows track info
	-	Real-time updates using socket.io
	-	Support for mobile browsers.
	-	***WIP***: Playback controls

---

<i id="f1">1</i>: MQTT metadata support released in `shairport-sync` [Version 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)[⤸](#a1)
