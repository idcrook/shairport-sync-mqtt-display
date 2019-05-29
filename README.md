shairport-sync-mqtt-display
===========================

Utilities for displaying [`shairport-sync`](https://github.com/mikebrady/shairport-sync)-provided metadata (via MQTT[^1])

Real-time webapp
----------------

[python-flask-socketio-server](python-flask-socketio-server) in this repo

![iOS screenshot](python-flask-socketio-server/screenshot1.png)

-	Python-based (Flask) webserver app
	-	Connects to MQTT broker and shows track info
	-	Real-time updates using socket.io
	-	Support for mobile browsers.
	-	***WIP***: Playback controls

[^1]: MQTT metadata support released in `shairport-sync` [Version 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)
