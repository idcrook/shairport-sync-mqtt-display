#!/usr/bin/env python3

# Refer to README.md for pre-reqs, and customize config.yaml

# to run:
#     python3 mqtt_lcd_display.py

# TODO: implement MQTT display buffer updates
# TODO: implement track info scrolling settings and controls
# TODO: correctly implement signal handling (graceful shutdown)

import os
from pathlib import Path
import signal
import shutil
import ssl
import sys
import tempfile
import time

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import paho.mqtt.client as mqtt
from yaml import safe_load
try:
    from colorthief import ColorThief  # pip install colorthief
except ImportError:
    print('For backlight colors from cover art:')
    print('    pip install colorthief')
    print('    sudo apt install libtiff5')
    print('    sudo apt install libopenjp2-7')

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


def _normalizeRGB8bToBacklightRGB(rgb):
    """Takes an (R,G,B) 8-bit (0-255) ordered tuple and converts it to backlight-compatible tuple.

    CircuitPython adafruit_character_lcd library expects (R,G,B) fields in range of 0-100.
    """

    rgb_sum = (rgb[0] + rgb[1] + rgb[2])
    scale_factor = 100.0 * 3
    # scaled (100, 100, 100) if they're all equal (sum should add up to 300)
    r_scaled = int((rgb[0] / rgb_sum) * scale_factor)
    g_scaled = int((rgb[1] / rgb_sum) * scale_factor)
    b_scaled = int((rgb[2] / rgb_sum) * scale_factor)

    #
    r_norm = 100 if r_scaled > 99 else (50 if r_scaled > 95 else 0)
    g_norm = 100 if g_scaled > 99 else (50 if g_scaled > 95 else 0)
    b_norm = 100 if b_scaled > 99 else (50 if b_scaled > 95 else 0)

    if (r_norm + g_norm + b_norm) != 0:
        backlight_rgb = (r_norm, g_norm, b_norm)
    else:
        #rgb_norm = list((r_norm, g_norm, b_norm))
        backlight_rgb = [0, 0, 0]
        # set value for color that has highest value
        print(max(rgb))
        print(rgb.index(max(rgb)))
        backlight_rgb[rgb.index(max(rgb))] = 50
        #backlight_rgb = (50, 50, 50)

    if True:
        print("rgb", rgb)
        print("rgb scaled", (r_scaled, g_scaled, b_scaled))
        print("rgb norm", (r_norm, g_norm, b_norm))

    if True:
        print("backlight_rgb = {}".format(backlight_rgb))
    return backlight_rgb


def _normalizeRGB8bToBacklightRGB2(rgb):
    """Takes an (R,G,B) 8-bit (0-255) ordered tuple and converts it to backlight-compatible tuple.

    CircuitPython adafruit_character_lcd library expects (R,G,B) fields in
    range of 0-100 for PWM-controlled hardware. In practice, values of 0, 50 or
    100 are discernable.
    """

    rgb_sum = rgb[0] + rgb[1] + rgb[2]
    scale_factor = 99.0
    r_scaled = int((rgb[0] / rgb_sum) * scale_factor)
    g_scaled = int((rgb[1] / rgb_sum) * scale_factor)
    b_scaled = int((rgb[2] / rgb_sum) * scale_factor)
    backlight_rgb = (r_scaled, g_scaled, b_scaled)
    if True:
        print(backlight_rgb)
    return backlight_rgb


def _send_and_store_playing_metadata(metadata_name, message):
    """Saves currently playing metadata info.

    Applies a naming convention of prepending string 'playing_' to metadata
    name in saving data structure.
    """

    global UPDATE_DISPLAY
    # print("{} update".format(metadata_name))
    saved_metadata_name = "playing_{}".format(metadata_name)
    if metadata_name == 'dominant_color':
        SAVED_INFO[saved_metadata_name] = message
    else:
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

            with tempfile.NamedTemporaryFile() as fp:
                fp.write(message.payload)
                if False:  # for debugging
                    fname = fp.name
                    fname_copy = fname + '.bin'
                    print(fname, fname_copy)
                    shutil.copy(fname, fname_copy)

                # get dominant color of cover art image
                image_to_analyze = ColorThief(fp)
                dominant_color = image_to_analyze.get_color(quality=20)
                print(dominant_color)
                _send_and_store_playing_metadata("dominant_color",
                                                 dominant_color)

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
    lcd_row_max_columns = 31
    lcd_rows = 2
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

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

    if DISPLAYUI_CONF.get('show_lcd_splash', False):
        lcd_startup_splash(lcd)

    def _get_formatted_msg_and_props():
        artist = SAVED_INFO.get('playing_artist', "Artist")
        title = SAVED_INFO.get('playing_title', "Title")
        formatted_msg = f"{artist:{lcd_row_max_columns}.{lcd_row_max_columns}s}\n{title:{lcd_row_max_columns}.{lcd_row_max_columns}s}"

        # for longer strings
        artist_len = len(artist)
        title_len = len(title)
        max_len = max(list([artist_len, title_len]))

        return (formatted_msg, max_len)

    default_rgb_backlight_color = DISPLAYUI_CONF.get(
        'default_rgb_backlight_color', (0, 255, 0))

    def _get_backlight_color():
        dominant_color = SAVED_INFO.get('playing_dominant_color',
                                        default_rgb_backlight_color)
        backlight_color = _normalizeRGB8bToBacklightRGB(dominant_color)
        return backlight_color

    def _handle_button_pressed(button_pressed=None):
        print(button_pressed)
        command = REMOTECONTROL_CONF['buttons'].get(button_pressed, None)
        if command:
            (topic, msg) = _generate_remote_command(command)
            mqttc.publish(topic, msg)
        else:
            print(f'-E- Could not find command for button = {button_pressed}')

    # Set LCD color to yellow
    lcd.color = [50, 50, 0]
    lcd.clear()

    # initialize SAVED_INFO
    if True:
        SAVED_INFO['playing_artist'] = "Unknown Artist"
        SAVED_INFO['playing_album'] = "Unknown Album"
        SAVED_INFO['playing_genre'] = "Unknown Genre"
        SAVED_INFO['playing_title'] = "Unknown Title"
        SAVED_INFO['playing_dominant_color'] = default_rgb_backlight_color
        UPDATE_DISPLAY = True

    print('Starting main loop')
    while True:
        try:
            button_press = 0
            button_pressed = None
            # scan for button presses
            if lcd.down_button:
                lcd.message = "Down!   "
                button_press = 1
                button_pressed = 'button_down'
            elif lcd.left_button:
                lcd.message = "Left!   "
                button_press = 1
                button_pressed = 'button_left'
            elif lcd.right_button:
                lcd.message = "Right!  "
                button_press = 1
                button_pressed = 'button_right'
            elif lcd.select_button:
                lcd.message = "Select! "
                button_press = 1
                button_pressed = 'button_select'
            elif lcd.up_button:
                lcd.message = "Up!     "
                button_press = 1
                button_pressed = 'button_up'

            if button_press:
                UPDATE_DISPLAY = True
                _handle_button_pressed(button_pressed=button_pressed)
                time.sleep(0.7)

            # FIXME: needs a debounce or other for previtem twice in a row
            #     otherwise a long song animation will block out the button
            #     handling
            if UPDATE_DISPLAY and button_press == 0:
                # reset global variable
                UPDATE_DISPLAY = False

                if False:
                    print(SAVED_INFO)

                fmt_msg1, max_len = _get_formatted_msg_and_props()
                backlight_color = _get_backlight_color()

                lcd.color = backlight_color
                lcd.message = fmt_msg1

                scroll_sleep_length = 0.45
                if max_len > lcd_columns:
                    extra_chars = min(max_len, (2 * lcd_columns) - 1)
                    fmt_msg, junk = _get_formatted_msg_and_props()
                    lcd.color = _get_backlight_color()
                    lcd.message = fmt_msg
                    for i in range(extra_chars - lcd_columns):
                        # if MQTT message comes in, stop scrolling
                        if UPDATE_DISPLAY:
                            continue
                        time.sleep(scroll_sleep_length)
                        lcd.move_left()
                    time.sleep(scroll_sleep_length)
                    lcd.home()
                    fmt_msg, junk = _get_formatted_msg_and_props()
                    lcd.color = _get_backlight_color()
                    lcd.message = fmt_msg

        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Exiting...")
            graceful_exit()
            raise SystemExit
