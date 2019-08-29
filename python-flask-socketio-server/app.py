#!/usr/bin/env python3

# read README.md for pre-reqs, and customize config.yaml

# to run:
#     python3 app.py

import base64
from pathlib import Path
import os
import ssl

import paho.mqtt.client as mqtt
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from yaml import safe_load

# determine path to this script
mypath = Path().absolute()

# Load a default image file
default_image_file = mypath / "static" / "default.png"
print("Using default cover image file {}".format(default_image_file))
default_image_mime_type = 'image/png'
default_image_b64_str = ''
with open(default_image_file, "rb") as imageFile:
    image_octets = imageFile.read()
    default_image_b64_str = base64.b64encode(image_octets).decode('utf-8')

# App will die here if config file is missing.
# Read only on startup. If edited, app must be relaunched to see changes
config_file = mypath / "config.yaml"
print("Using config file {}".format(config_file))
with config_file.open() as f:
    config = safe_load(f)

# subtrees of the config file
MQTT_CONF = config['mqtt']  # required section
WEBSERVER_CONF = config['web_server']  # required section
WEBUI_CONF = config.get('webui', {})  # if missing, assume defaults

# "base" topic - shaould match shairport-sync.conf {mqtt.topic}
TOPIC_ROOT = MQTT_CONF['topic']
print(TOPIC_ROOT)

# this variable will keep the most recent track info pieces sent to socketio
SAVED_INFO = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = WEBSERVER_CONF.get('secret_key', 'secret!')
socketio = SocketIO(app)

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


def populateTemplateData(config):
    """Use values from config file to form templateData for HTML template.

    Set default value if the key is not found in config (second arg in dict.get())"""
    templateData = {}

    if config.get('show_player', False):
        templateData['showPlayer'] = True

    if config.get('show_canvas', False):
        templateData['showCanvas'] = True

    if config.get('show_update_info', True):
        templateData['showUpdateInfo'] = True

    if config.get('show_artwork', True):
        templateData['showCoverArt'] = True

    if config.get('artwork_rounded_corners', False):
        templateData['showCoverArtRoundedCorners'] = True

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


def _generate_remote_command(command):
    """Return remote topic and message, given command.

    TODO: add checking on names?
    """
    topic = TOPIC_ROOT + "/remote"
    msg = command
    return topic, msg


def on_connect(client, userdata, flags, rc):
    """# For when MQTT client receives a CONNACK response from the server.

    Adding subscriptions in on_connect() means that they'll be re-subscribed
    for lost/re-connections to MQTT server.

    """

    # print("Connected with result code {}".format(rc))

    subtopic_list = list(known_track_metadata_types.keys())
    subtopic_list.extend(list(known_play_metadata_types.keys()))

    # if we are not showing cover art, do not subscribe to it
    if (populateTemplateData(MQTT_CONF)).get('showCoverArt'):
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
    """Forms playing metadata message and sends to browser client using socket.io.

    Also saves a copy of sent message (into SAVED_INFO dict), which is used to
    resend most-recent event messages in case the browser page is refreshed,
    another browser client connects, etc.

    Applies a naming convention of prepending string 'playing_' to metadata
    name in socketio sent event. Of course the same naming convention is used
    on receiving client event.

    """

    # print("{} update".format(metadata_name))
    msg = {'data': message.payload.decode('utf8')}
    emitted_metadata_name = "playing_{}".format(metadata_name)
    SAVED_INFO[emitted_metadata_name] = msg
    socketio.emit(emitted_metadata_name, msg)


def _send_play_event(metadata_name):
    """Forms play event message and sends to browser client using socket.io."""

    print("{}".format(metadata_name))
    socketio.emit(metadata_name, metadata_name)


def on_message(client, userdata, message):
    """Callback for when a subscribed-to MQTT message is received."""

    # if message.topic != _form_subtopic_topic("cover"):
    #     print(message.topic, message.payload)

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
        # print("cover update")
        if message.payload:
            mime_type = _guessImageMime(message.payload)
            image_b64_str = base64.b64encode(message.payload).decode('utf-8')
        else:
            mime_type = default_image_mime_type
            image_b64_str = default_image_b64_str
        msg = {'data': image_b64_str, 'mimetype': mime_type}
        SAVED_INFO['cover_art'] = msg
        socketio.emit('cover_art', msg)


# Configure and launch MQTT broker connection
mqttc = mqtt.Client(clean_session=True)
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

mqtt_host = MQTT_CONF['host']
mqtt_port = MQTT_CONF['port']
print("Connecting to broker", mqtt_host, 'port', mqtt_port)
mqttc.connect(mqtt_host, port=mqtt_port)
mqttc.loop_start()

templateData = populateTemplateData(WEBUI_CONF)


# Define Flask server routes
@app.route("/")
def main():
    return render_template('main.html',
                           async_mode=socketio.async_mode,
                           **templateData)


@app.route('/favicon.ico')
def favicon():
    """Handle favicon.ico requests."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@socketio.on('myevent')
def handle_my_custom_event(json):
    """Re-send now playing info.

    Using this event, typically emitted from browser client, to re-send now
    playing info on a page reload, e.g.

    """
    # print('received data: ' + str(json))
    if json.get('data'):
        print("myevent:", json['data'])

    for key, msg in SAVED_INFO.items():
        # print(key, msg)
        print(key, )
        socketio.emit(key, msg)


@socketio.on('remote_previtem')
def handle_previtem(json):
    print('handle_previtem', str(json))
    (topic, msg) = _generate_remote_command('previtem')
    mqttc.publish(topic, msg)


@socketio.on('remote_nextitem')
def handle_nextitem(json):
    print('handle_nextitem', str(json))
    (topic, msg) = _generate_remote_command('nextitem')
    mqttc.publish(topic, msg)


# what 'stop' does is not desired; cannot be resumed
@socketio.on('remote_stop')
def handle_stop(json):
    print('handle_stop', str(json))
    (topic, msg) = _generate_remote_command('stop')
    # mqttc.publish(topic, msg)


@socketio.on('remote_pause')
def handle_pause(json):
    print('handle_pause', str(json))
    (topic, msg) = _generate_remote_command('pause')
    mqttc.publish(topic, msg)


@socketio.on('remote_playpause')
def handle_playpause(json):
    print('handle_playpause', str(json))
    (topic, msg) = _generate_remote_command('playpause')
    mqttc.publish(topic, msg)


@socketio.on('remote_play')
def handle_play(json):
    print('handle_play', str(json))
    (topic, msg) = _generate_remote_command('play')
    mqttc.publish(topic, msg)


@socketio.on('remote_playresume')
def handle_playresume(json):
    print('handle_playresume', str(json))
    (topic, msg) = _generate_remote_command('playresume')
    mqttc.publish(topic, msg)


# launch the Flask (+socketio) webserver!
if __name__ == "__main__":
    web_host = WEBSERVER_CONF['host']
    web_port = WEBSERVER_CONF['port']
    web_debug = WEBSERVER_CONF['debug']
    print('Starting webserver')
    print('   http://{}:{}'.format(web_host, web_port))
    socketio.run(app, host=web_host, port=web_port, debug=web_debug)
