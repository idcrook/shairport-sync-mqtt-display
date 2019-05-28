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

app = Flask(__name__)
socketio = SocketIO(app)

# app will die if config file is missing
config_file = "config.yaml"
with open(config_file) as f:
    config = safe_load(f)

# subtree of the config file
MQTT_CONF = config['mqtt']
TOPIC_ROOT = MQTT_CONF['topic']
print(TOPIC_ROOT)

# (Unused) for webpage
templateData = {}
# this variable will keep the most recent track info pieces sent to socketio
SAVED_INFO = {}


def _guessImageMime(magic):
    """Peeks at a couple bytes in image binary to identify image format."""

    if magic.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif magic.startswith(b'\x89PNG\r\n\x1a\r'):
        return 'image/png'
    else:
        return "image/jpg"


# The callback for when MQTT client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}".format(rc))

    # adding subscriptions in on_connect() means that if we will still be
    # subscribed if there lost/reconnect connection to the MQTT server
    for subtopic in ('cover', 'artist', 'album', 'title'):
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
    TLS_CONF = MQTT_CONF.get('tls')
    print("Using TLS config", TLS_CONF)
    # assumes full valid TLS configuration for paho lib
    if TLS_CONF:
        mqttc.tls_set(ca_certs=TLS_CONF['ca_certs_path'],
                      certfile=TLS_CONF['certfile_path'],
                      keyfile=TLS_CONF['keyfile_path'],
                      cert_reqs=ssl.CERT_REQUIRED,
                      tls_version=ssl.PROTOCOL_TLSv1_2,
                      ciphers=None)

mqtt_host = MQTT_CONF['host']
mqtt_port = MQTT_CONF['port']
print("Connecting to broker", mqtt_host, 'port', mqtt_port)
mqttc.connect(mqtt_host, port=mqtt_port, keepalive=60)
mqttc.loop_start()


@app.route("/")
def main():
    # Pass the template data into the template main.html and return it to the user
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
    WEBSERVER_CONF = config['web_server']
    web_host = WEBSERVER_CONF['host']
    web_port = WEBSERVER_CONF['port']
    web_debug = WEBSERVER_CONF['debug']
    print('Starting webserver')
    print('   http://{}:{}'.format(web_host, web_port))
    socketio.run(app, host=web_host, port=web_port, debug=web_debug)
