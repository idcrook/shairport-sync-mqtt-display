#!/usr/bin/env python3

# read README.md for pre-reqs, and customize config.yaml

# to run:
#     python3 app.py

import base64
import os
import ssl
from yaml import safe_load

import paho.mqtt.client as mqtt
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO

# App will die if config file is missing. Only read on startup, so if it is
# edited, app must be relaunched to see changes
config_file = "config.yaml"
with open(config_file) as f:
    config = safe_load(f)

# subtrees of the config file
MQTT_CONF = config['mqtt']  # required section
WEBSERVER_CONF = config['web_server']  # required section
WEBUI_CONF = config.get('webui', {})  # if missing, assume defaults

# "base" topic - shairport-sync.conf {mqtt.topic}
TOPIC_ROOT = MQTT_CONF['topic']
print(TOPIC_ROOT)

# this variable will keep the most recent track info pieces sent to socketio
SAVED_INFO = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = WEBSERVER_CONF.get('secret_key', 'secret!')
socketio = SocketIO(app)


def _guessImageMime(magic):
    """Peeks at a couple bytes in image binary to identify image format."""

    if magic.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif magic.startswith(b'\x89PNG\r\n\x1a\r'):
        return 'image/png'
    else:
        return "image/jpg"


known_track_metadata_types = {
    'artist': 'showArtist',
    'album': 'showAlbum',
    'title': 'showTitle',
    'genre': 'showGenre'
}


def populateTemplateData(config):
    """Use values from config file to form templateData for HTML template."""
    templateData = {}
    if config.get('show_player', False):  # default : False
        templateData['showPlayer'] = True

    if config.get('show_canvas', False):  # default : False
        templateData['showCanvas'] = True

    if config.get('show_update_info', True):  # default : True
        templateData['showUpdateInfo'] = True

    if config.get('show_artwork', True):  # default : True
        templateData['showCoverArt'] = True

    if config.get('show_track_metadata', True):  # default : True
        metadata_types = config.get(
            'track_metadata',
            ['artist', 'album', 'title'])  # defaults to these three
        for metadata_type in metadata_types:
            print(metadata_type)
            if metadata_type in known_track_metadata_types:
                templateData[known_track_metadata_types[metadata_type]] = True

    return templateData


# The callback for when MQTT client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}".format(rc))

    # adding subscriptions in on_connect() means that if we will still be
    # subscribed if there lost/reconnect connection to the MQTT server
    for subtopic in ('cover', 'artist', 'album', 'title', 'genre'):
        sub = TOPIC_ROOT + "/" + subtopic
        print("Subscribing to topic", sub)
        # QoS==0 should be fine
        (result, msg_id) = client.subscribe(sub, 0)
        # print(msg_id)


# Callback for when a subscribed-to MQTT message received
def on_message(client, userdata, message):
    if message.topic == TOPIC_ROOT + "/" + "artist":
        print("artist update")
        msg = {'data': message.payload.decode('utf8')}
        SAVED_INFO['playing_artist'] = msg
        socketio.emit('playing_artist', msg)
    if message.topic == TOPIC_ROOT + "/" + "album":
        print("album update")
        msg = {'data': message.payload.decode('utf8')}
        SAVED_INFO['playing_album'] = msg
        socketio.emit('playing_album', msg)
    if message.topic == TOPIC_ROOT + "/" + "genre":
        print("genre update")
        msg = {'data': message.payload.decode('utf8')}
        SAVED_INFO['playing_genre'] = msg
        socketio.emit('playing_genre', msg)
    if message.topic == TOPIC_ROOT + "/" + "title":
        print("title update")
        msg = {'data': message.payload.decode('utf8')}
        SAVED_INFO['playing_title'] = msg
        socketio.emit('playing_title', msg)
    if message.topic == TOPIC_ROOT + "/" + "cover":
        print("cover update")
        mime_type = _guessImageMime(message.payload)
        b64_image = base64.b64encode(message.payload).decode('utf-8')
        msg = {'data': b64_image, 'mimetype': mime_type}
        SAVED_INFO['cover_art'] = msg
        socketio.emit('cover_art', msg)


# Configure and launch MQTT broker connection
mqttc = mqtt.Client()
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

mqtt_host = MQTT_CONF['host']
mqtt_port = MQTT_CONF['port']
print("Connecting to broker", mqtt_host, 'port', mqtt_port)
mqttc.connect(mqtt_host, port=mqtt_port, keepalive=60)
mqttc.loop_start()

templateData = populateTemplateData(WEBUI_CONF)


@app.route("/")
def main():
    return render_template('main.html',
                           async_mode=socketio.async_mode,
                           **templateData)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# using this event from browser client to re-send now playing info on a page reload, e.g.
@socketio.on('myevent')
def handle_my_custom_event(json):
    print('received data: ' + str(json))
    for key, msg in SAVED_INFO.items():
        # print(key, msg)
        print(key, )
        socketio.emit(key, msg)


# launch the Flask (socketio) webserver!
if __name__ == "__main__":
    web_host = WEBSERVER_CONF['host']
    web_port = WEBSERVER_CONF['port']
    web_debug = WEBSERVER_CONF['debug']
    print('Starting webserver')
    print('   http://{}:{}'.format(web_host, web_port))
    socketio.run(app, host=web_host, port=web_port, debug=web_debug)
