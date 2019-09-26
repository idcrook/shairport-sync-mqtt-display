[![GitHub license](https://img.shields.io/github/license/idcrook/shairport-sync-mqtt-display.svg)](https://github.com/idcrook/shairport-sync-mqtt-display/blob/master/LICENSE)

Utilities to display [`shairport-sync`](https://github.com/mikebrady/shairport-sync) metadata (via MQTT)<sup id="a1">[1](#f1)</sup>

Webserver webapp
----------------

![Screenshot - Dark mode on iPhone SE](python-flask-socketio-server/screenshot1.png "Dark mode on iPhone SE")

[python-flask-socketio-server](python-flask-socketio-server/)

-	Displays currently playing track info, including cover art.
-	Configurable UI. Dark-mode support.
-	Support for mobile browsers. Webapp manifest.
-	Playback controls.

Display on 16x2 Character LCD
=============================

![Photo - Running on as Raspberry Pi](circuitpython_char_lcd/photo1.jpg "Running on a Pi with 16x2 Character LCD display")

[circuitpython_char_lcd](circuitpython_char_lcd/)

-	Configurable display and UI.
-	Playback remote control support.
-	Tested using CircuitPython i2c LCD library on a Raspberry Pi.

#### License

Code and documentation Copyright © 2019 David Crook under [MIT License](LICENSE).

---

<i id="f1">1</i>: MQTT metadata support released in `shairport-sync` [Version 3.3](https://github.com/mikebrady/shairport-sync/releases/tag/3.3)[⤸](#a1)
