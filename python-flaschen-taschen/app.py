#!/usr/bin/env python3

# read README.md for pre-reqs, and customize config.yaml

# to run:
#     python3 app.py

import base64
from pathlib import Path
import io
import os
import ssl
import time

import paho.mqtt.client as mqtt
from yaml import safe_load
from PIL import Image  #, ImageOps

# https://github.com/hzeller/flaschen-taschen/raw/master/api/python/flaschen.py
import flaschen

# determine path to this script
mypath = Path(__file__).resolve().parent

# Load a default image file
default_image_file = mypath / ".." / "python-flask-socketio-server" / "static" / "img" / "default-inverted.png"
print("Using default cover image file {}".format(default_image_file))

# App will die here if config file is missing.
# Read only on startup. If edited, app must be relaunched to see changes
config_file = mypath / "config.yaml"
print("Using config file {}".format(config_file))
with config_file.open() as f:
    config = safe_load(f)

# subtrees of the config file
MQTT_CONF = config["mqtt"]  # required section

# "base" topic - should match shairport-sync.conf {mqtt.topic}
TOPIC_ROOT = MQTT_CONF["topic"]
print(TOPIC_ROOT)

FLASCHEN_CONF = config["flaschen"]  # required section
FLASCHEN_SERVER = FLASCHEN_CONF.get("server", 'localhost')
FLASCHEN_PORT = FLASCHEN_CONF.get("port", 1337)
FLASCHEN_ROWS = FLASCHEN_CONF.get("led-rows", 32)
FLASCHEN_COLS = FLASCHEN_CONF.get("led-columns", 32)

flaschen_client = None
DEFAULT_IMAGE = None
FLASCHEN_SIZE = (FLASCHEN_COLS, FLASCHEN_ROWS)

# this variable will keep the most recent track info pieces
SAVED_INFO = {}

known_play_metadata_types = {
    "songalbum": "songalbum",
    "volume": "volume",
    "client_ip": "client_ip",
    "active_start": "active_start",
    "active_end": "active_end",
    "play_start": "play_start",
    "play_end": "play_end",
    "play_flush": "play_flush",
    "play_resume": "play_resume",
}

# Other known 'ssnc' include:
#    'PICT': 'show'

known_core_metadata_types = {
    "artist": "showArtist",
    "album": "showAlbum",
    "title": "showTitle",
    "genre": "showGenre",
    "cover": "showCoverArt",
}



def _form_subtopic_topic(subtopic):
    """Return full topic path given subtopic."""
    topic = TOPIC_ROOT + "/" + subtopic
    return topic


# Available commands listed in shairport-sync.conf
known_remote_commands = [
    "command",
    "beginff",
    "beginrew",
    "mutetoggle",
    "nextitem",
    "previtem",
    "pause",
    "playpause",
    "play",
    "stop",
    "playresume",
    "shuffle_songs",
    "volumedown",
    "volumeup",
]

def flaschenSendThumbnailImage(client, image):
    for x in range(FLASCHEN_COLS):
        for y in range(FLASCHEN_ROWS):
            # these will be RGBA
            color = image.getpixel((x, y))
            client.set(x, y, (color[0], color[1], color[2]))
    client.send()

def on_connect(client, userdata, flags, rc, properties=None):
    """For when MQTT client receives a CONNACK response from the server.

    Adding subscriptions in on_connect() means that they'll be re-subscribed
    for lost/re-connections to MQTT server.
    """

    # print("Connected with result code {}".format(rc))

    subtopic_list = list(known_core_metadata_types.keys())
    subtopic_list.extend(list(known_play_metadata_types.keys()))

    for subtopic in subtopic_list:
        topic = _form_subtopic_topic(subtopic)
        print("topic", topic, end=" ")
        (result, msg_id) = client.subscribe(topic, 0)  # QoS==0 should be fine
        print(msg_id)


def on_message(client, userdata, message, properties=None):
    """Callback for when a subscribed-to MQTT message is received."""

    if message.topic != _form_subtopic_topic("cover"):
        print(message.topic, message.payload)
    else:
        print(message.topic, len(message.payload))

    # cover art
    if message.topic == _form_subtopic_topic("cover"):
        if message.payload:
            try:
                image = createMatrixImage(io.BytesIO(message.payload))
            except Exception as e:
                print(f"Invalid cover art, using default: {e}")
                image = DEFAULT_IMAGE
        else:
            image = DEFAULT_IMAGE
        msg = {"data": image}
        SAVED_INFO["cover_art"] = msg
        flaschenSendThumbnailImage(flaschen_client, image)

    # clear matrix when inactive
    if message.topic == _form_subtopic_topic("active_end"):
        image = Image.new('RGBA', FLASCHEN_SIZE, (0, 0, 0, 0))
        flaschenSendThumbnailImage(flaschen_client, image)

def createMatrixImage(fileobj):
    with Image.open(fileobj) as image:
        size = FLASCHEN_SIZE
        if hasattr(fileobj, 'name'):
            print(fileobj.name, end=' ')
        print(image.format, f"{image.size} x {image.mode}")
        image.thumbnail(size, Image.LANCZOS)
        background = Image.new('RGBA', size, (0, 0, 0, 0))
        background.paste(image, (int((size[0] - image.size[0]) / 2), int((size[1] - image.size[1]) / 2)))
        return background

# Load default image
DEFAULT_IMAGE = createMatrixImage(default_image_file)
print(DEFAULT_IMAGE)

# FIXME: handle netword errors better
flaschen_client = flaschen.Flaschen(FLASCHEN_SERVER,
                                    FLASCHEN_PORT,
                                    FLASCHEN_COLS,
                                    FLASCHEN_ROWS)

# Configure MQTT broker connection
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# register callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

if MQTT_CONF.get("use_tls"):
    tls_conf = MQTT_CONF.get("tls")
    print("Using TLS config", tls_conf)
    # assumes full valid TLS configuration for paho lib
    if tls_conf:
        mqttc.tls_set(
            ca_certs=tls_conf["ca_certs_path"],
            certfile=tls_conf["certfile_path"],
            keyfile=tls_conf["keyfile_path"],
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None,
        )

        if tls_conf.get("allow_insecure_server_certificate", False):
            # from docs: Do not use this function in a real system. Setting value
            # to True means there is no point using encryption.
            mqttc.tls_insecure_set(True)

if MQTT_CONF.get("username"):
    username = MQTT_CONF.get("username")
    print("MQTT username:", username)
    pw = MQTT_CONF.get("password")
    if pw:
        mqttc.username_pw_set(username, password=pw)
    else:
        mqttc.username_pw_set(username)

if MQTT_CONF.get("logger"):
    print("Enabling MQTT logging")
    mqttc.enable_logger()

# Launch MQTT broker connection
mqtt_host = MQTT_CONF["host"]
mqtt_port = MQTT_CONF["port"]
print("Connecting to broker", mqtt_host, "port", mqtt_port)
mqttc.connect(mqtt_host, port=mqtt_port)
# loop_start run a thread in the background
mqttc.loop_start()



# launch the Flask (+socketio) webserver!
if __name__ == "__main__":
    
    while True:
        time.sleep(1)
