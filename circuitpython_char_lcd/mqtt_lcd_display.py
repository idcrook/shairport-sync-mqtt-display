#!/usr/bin/env python3

# Refer to README.md for pre-reqs, and customize config.yaml

# to run:
#     python3 mqtt_lcd_display.py

# TODO: implement MQTT display buffer updates
# TODO: implement track info scrolling settings and controls
# TODO: correctly implement signal handling (graceful shutdown)
# TODO: implement remote controls
# TODO: -  validate remote commands provided in config file
# TODO: implement backlight color via color sampling of cover art

import os
from pathlib import Path
import signal
import ssl
import sys
import time

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import paho.mqtt.client as mqtt
from yaml import safe_load

# determine path to this script
mypath = Path().absolute()

# App will die here if config file is missing.
# Read only on startup. If edited, app must be relaunched to see changes
config_file = mypath / "config.yaml"
print("Using config file {}".format(config_file))
with config_file.open() as f:
    config = safe_load(f)

# subtrees of the config file
MQTT_CONF = config['mqtt']  # required section
DISPLAYUI_CONF = config.get('displayui')  # required section
REMOTECONTROL_CONF = config.get('remotecontrol', {})

# "base" topic - should match shairport-sync.conf {mqtt.topic}
TOPIC_ROOT = MQTT_CONF['topic']
print(TOPIC_ROOT)

# this variable will keep the most recent playing track info
SAVED_INFO = {}

# Global variable for text update
UPDATE_DISPLAY = False

# Global variable for backlight update
UPDATE_DISPLAY_COLOR = False

known_play_metadata_types = {
    'play_end': 'play_end',
    'play_start': 'play_start',
    'play_flush': 'play_flush',
    'play_resume': 'play_resume'
}

known_track_metadata_types = {
    'artist': 'showArtist',
    'album': 'showAlbum',
    'title': 'showTitle',
    'genre': 'showGenre'
}


def resolveConfigData(config):
    """Use values from config file-style to resolve settings.

    Set default value if the key is not found in config (second arg in dict.get())"""
    templateData = {}

    if config.get('show_backlight_color', False):
        templateData['showBacklightColor'] = True

    if config.get('show_track_metadata', True):
        metadata_types = config.get(
            'track_metadata',
            ['artist', 'album', 'title'])  # defaults to these three
        for metadata_type in metadata_types:
            if metadata_type in known_track_metadata_types:
                templateData[known_track_metadata_types[metadata_type]] = True

    return templateData


def _form_subtopic_topic(subtopic):
    """Return full topic path given subtopic."""
    topic = TOPIC_ROOT + "/" + subtopic
    return topic


# Available commands listed in shairport-sync.conf
known_remote_commands = [
    "command", "beginff", "beginrew", "mutetoggle", "nextitem", "previtem",
    "pause", "playpause", "play", "stop", "playresume", "shuffle_songs",
    "volumedown", "volumeup"
]


def _generate_remote_command(command):
    """Return MQTT topic and message for a given remote command."""

    if command in known_remote_commands:
        print(command)
        topic = TOPIC_ROOT + "/remote"
        msg = command
        return topic, msg
    else:
        raise ValueError('Unknown remote command: {}'.format(command))


def on_connect(client, userdata, flags, rc):
    """For when MQTT client receives a CONNACK response from the server.

    Adding subscriptions in on_connect() means that they'll be re-subscribed
    for lost/re-connections to MQTT server.
    """

    print("Connected with result code {}".format(rc))

    subtopic_list = list(known_track_metadata_types.keys())
    subtopic_list.extend(list(known_play_metadata_types.keys()))

    # only subscribe to cover art if we are going to use it
    if (resolveConfigData(DISPLAYUI_CONF)).get('showBacklightColor'):
        subtopic_list.append('cover')

    for subtopic in subtopic_list:
        topic = _form_subtopic_topic(subtopic)
        print("topic", topic, end=' ')
        (result, msg_id) = client.subscribe(topic, 0)  # QoS==0 should be fine
        print(msg_id)


def _guessImageMime(magic):
    """Peeks at leading bytes in binary object to identify image format."""

    if magic.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif magic.startswith(b'\x89PNG\r\n\x1a\r'):
        return 'image/png'
    else:
        return "image/jpg"


def _send_and_store_playing_metadata(metadata_name, message):
    """Saves currently playing metadata info.

    Applies a naming convention of prepending string 'playing_' to metadata
    name in saving data structure.
    """

    global UPDATE_DISPLAY
    # print("{} update".format(metadata_name))
    saved_metadata_name = "playing_{}".format(metadata_name)
    SAVED_INFO[saved_metadata_name] = message.payload.decode('utf8')
    UPDATE_DISPLAY = True


def _send_play_event(metadata_name):
    """Forms play event message and sends to browser client using socket.io."""

    print("{}".format(metadata_name))
    # socketio.emit(metadata_name, metadata_name)


def on_message(client, userdata, message):
    """Callback for when a subscribed-to MQTT message is received."""

    if message.topic != _form_subtopic_topic("cover"):
        print(message.topic, message.payload)

    # Playing track info fields
    if message.topic == _form_subtopic_topic("artist"):
        _send_and_store_playing_metadata("artist", message)
    if message.topic == _form_subtopic_topic("album"):
        _send_and_store_playing_metadata("album", message)
    if message.topic == _form_subtopic_topic("genre"):
        _send_and_store_playing_metadata("genre", message)
    if message.topic == _form_subtopic_topic("title"):
        _send_and_store_playing_metadata("title", message)

    # Player state
    if message.topic == _form_subtopic_topic("play_start"):
        _send_play_event("play_start")
    if message.topic == _form_subtopic_topic("play_end"):
        _send_play_event("play_end")
    if message.topic == _form_subtopic_topic("play_flush"):
        _send_play_event("play_flush")
    if message.topic == _form_subtopic_topic("play_resume"):
        _send_play_event("play_resume")

    # cover art
    if message.topic == _form_subtopic_topic("cover"):
        print("cover update")
        if message.payload:
            mime_type = _guessImageMime(message.payload)
            print(len(message.payload), mime_type)
            # TODO: get dominant color and translate to RGB backlight space
        else:
            pass


# Configure MQTT broker connection
mqttc = mqtt.Client()

# register callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

if MQTT_CONF.get('use_tls'):
    tls_conf = MQTT_CONF.get('tls')
    print("Using TLS config", tls_conf)
    # assumes full valid TLS configuration for paho lib
    if tls_conf:
        mqttc.tls_set(ca_certs=tls_conf['ca_certs_path'],
                      certfile=tls_conf['certfile_path'],
                      keyfile=tls_conf['keyfile_path'],
                      cert_reqs=ssl.CERT_REQUIRED,
                      tls_version=ssl.PROTOCOL_TLSv1_2,
                      ciphers=None)

        if tls_conf.get('allow_insecure_server_certificate', False):
            # from docs: Do not use this function in a real system. Setting value
            # to True means there is no point using encryption.
            mqttc.tls_insecure_set(True)

if MQTT_CONF.get('username'):
    username = MQTT_CONF.get('username')
    print("MQTT username:", username)
    pw = MQTT_CONF.get('password')
    if pw:
        mqttc.username_pw_set(username, password=pw)
    else:
        mqttc.username_pw_set(username)

if MQTT_CONF.get('logger'):
    print('Enabling MQTT logging')
    mqttc.enable_logger()

# Launch MQTT broker connection
mqtt_host = MQTT_CONF['host']
mqtt_port = MQTT_CONF['port']
print("Connecting to broker", mqtt_host, 'port', mqtt_port)
mqttc.connect(mqtt_host, port=mqtt_port)
# loop_start run a thread in the background
mqttc.loop_start()

# @socketio.on('myevent')
# def handle_my_custom_event(json):
#     """Re-send now playing info.

#     Using this event, typically emitted from browser client, to re-send now
#     playing info on a page reload, e.g.

#     """
#     # print('received data: ' + str(json))
#     if json.get('data'):
#         print("myevent:", json['data'])

#     for key, msg in SAVED_INFO.items():
#         # print(key, msg)
#         print(key, )
#         socketio.emit(key, msg)

# @socketio.on('remote_previtem')
# def handle_previtem(json):
#     print('handle_previtem', str(json))
#     (topic, msg) = _generate_remote_command('previtem')
#     mqttc.publish(topic, msg)

# @socketio.on('remote_nextitem')
# def handle_nextitem(json):
#     print('handle_nextitem', str(json))
#     (topic, msg) = _generate_remote_command('nextitem')
#     mqttc.publish(topic, msg)

# # what 'stop' does is not desired; cannot be resumed
# @socketio.on('remote_stop')
# def handle_stop(json):
#     print('handle_stop', str(json))
#     (topic, msg) = _generate_remote_command('stop')
#     # mqttc.publish(topic, msg)

# @socketio.on('remote_pause')
# def handle_pause(json):
#     print('handle_pause', str(json))
#     (topic, msg) = _generate_remote_command('pause')
#     mqttc.publish(topic, msg)

# @socketio.on('remote_playpause')
# def handle_playpause(json):
#     print('handle_playpause', str(json))
#     (topic, msg) = _generate_remote_command('playpause')
#     mqttc.publish(topic, msg)

# @socketio.on('remote_play')
# def handle_play(json):
#     print('handle_play', str(json))
#     (topic, msg) = _generate_remote_command('play')
#     mqttc.publish(topic, msg)

# @socketio.on('remote_playresume')
# def handle_playresume(json):
#     print('handle_playresume', str(json))
#     (topic, msg) = _generate_remote_command('playresume')
#     mqttc.publish(topic, msg)


def lcd_startup_splash(lcd):
    print(lcd, "Startup splash screen")
    # Set LCD color to red
    lcd.color = [100, 0, 0]
    lcd.message = "shairport-sync\nmqtt_lcd_display"
    time.sleep(0.5)

    # Set LCD color to green
    lcd.color = [0, 100, 0]
    time.sleep(0.5)

    # Set LCD color to blue
    lcd.color = [0, 0, 100]
    time.sleep(0.5)

    # Set LCD color to purple
    lcd.color = [50, 0, 50]
    time.sleep(0.5)

    # Set LCD color to yellow
    lcd.color = [50, 50, 0]

    # print a scrolling message
    start_msg = "Starting up...\n"
    lcd.message = start_msg
    for i in range(len(start_msg)):
        time.sleep(0.1)
        lcd.move_left()
    lcd.clear()


# # systemd: time_display.service: State 'stop-sigterm' timed out. Killing.
# def handler_stop_signals(signum, frame):
#     lcd.color = [0, 0, 0]
#     lcd.message = "Exiting"
#     time.sleep(3)
#     lcd.clear()
#     # Raises SystemExit(0):
#     sys.exit(0)

# signal.signal(signal.SIGINT, handler_stop_signals)
# signal.signal(signal.SIGTERM, handler_stop_signals)

# Initialize display and launch the main loop
if __name__ == "__main__":
    lcd_columns = 16
    lcd_rows = 2
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

    if DISPLAYUI_CONF.get('show_lcd_splash', False):
        lcd_startup_splash(lcd)

    # Set LCD color to yellow
    lcd.color = [50, 50, 0]
    lcd.clear()

    def graceful_exit():
        # f-strings require python3.6; buster comes with python3.7
        msg = "Exiting..."
        fmt_msg = f"{msg:{lcd_columns}s}\n{' ':{lcd_columns}s}"
        lcd.message = fmt_msg

        #time.sleep(3)
        # Turn off LCD backlights
        lcd.color = [0, 0, 0]
        lcd.clear()

        # Raises SystemExit(0):
        sys.exit(0)

    print('Starting main loop')
    while True:
        try:
            button_press = 0
            # TODO: implement song metadata display refresh
            # FIXME: implement the actual mqtt remote controls
            # scan for button presses
            if lcd.down_button:
                lcd.message = "Down!   "
                button_press = 1
            elif lcd.left_button:
                lcd.message = "Left!   "
                button_press = 1
            elif lcd.right_button:
                lcd.message = "Right!  "
                button_press = 1
            elif lcd.select_button:
                lcd.message = "Select! "
                button_press = 1
            elif lcd.up_button:
                lcd.message = "Up!     "
                button_press = 1

            if button_press:
                time.sleep(0.7)
                lcd.clear()
                UPDATE_DISPLAY = True

            if UPDATE_DISPLAY:
                # reset global variable
                UPDATE_DISPLAY = False

                print(SAVED_INFO)

                # TODO: Handle more than artist and title metadata
                artist = SAVED_INFO.get('playing_artist', "Artist")
                title = SAVED_INFO.get('playing_title', "Title")
                backlight_color = [30, 30, 90]
                fmt_msg = f"{artist:{lcd_columns}s}\n{title:{lcd_columns}s}"

                # FIXME: hard-coded color
                lcd.color = [30, 30, 90]
                lcd.message = fmt_msg

                # TODO: refresh display

        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Exiting...")
            graceful_exit()
