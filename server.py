#!/usr/bin/env python2
import paho.mqtt.client as mqtt
import BaseHTTPServer
import threading
import json

#settings
root_topic = "$SYS"
brocker_address = "iot.eclipse.org"

http_port = 3000
#global variables
mqtt_values = {}
#code
def add_value_to_dict(dictionary, key, value):
    path = key.split("/", 1);
    if (not path[0]) and path[1]:
        add_value_to_dict(dictionary, path[1], value)
        return
    if (len(path)<2) or not path[1]:
        dictionary[path[0]] = value
        return
    if type(dictionary.get(path[0])) is not dict:
        dictionary[path[0]] = {}
    add_value_to_dict(dictionary[path[0]], path[1], value)

#mqtt special
def on_mqtt_connect(client, userdata, flags, rc):
    client.subscribe(root_topic+"/#");

def on_mqtt_message(client, userdata, msg):
    add_value_to_dict(mqtt_values, msg.topic, msg.payload)

def start_update_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(brocker_address, 1883, 60)
    mqtt_client.loop_forever()
    mqtt_client.disconnect()
#http special

def subdict_from_path(dict, path):
    if dict is None:
        return dict
    subpaths = path.split("/", 1)
    if len(subpaths)<2:
        if not subpaths[0]:
            return dict
        else:
            return dict.get(subpaths[0])
    if not subpaths[0]:
        if not subpaths[1]:
            return dict
        else:
            return subdict_from_path(dict, subpaths[1])
    if (not subpaths[1]):
        return dict.get(subpaths[0])
    return subdict_from_path(dict.get(subpaths[0]), subpaths[1])

class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        values = subdict_from_path(mqtt_values, s.path)
        if dict is None:
            s.send_response(404)
            s.send_header("Content-type", "text/html; charset=utf-8")
            s.end_headers()
        else:
            s.send_response(200)
            s.send_header("Content-type", "application/json; charset=utf-8")
            s.end_headers()

    def do_GET(s):
        values = subdict_from_path(mqtt_values, s.path)
        if values is None:
            s.send_response(404)
            s.send_header("Content-type", "text/html; charset=utf-8")
            s.end_headers()
            s.wfile.write("<!doctype html><html><head><title>Post mqtt message</title></head>")
            s.wfile.write("<body><H3>Post mqtt message</H3>")
            s.wfile.write("<p>Brocker not contain %s topic. But you can post it</p>" % s.path)
            s.wfile.write("<form action=\"/\" method=\"post\">")
            s.wfile.write("<p>Topic:<input type=\"text\" value=\"%s\" name=\"topic\" /></p>" % s.path)
            s.wfile.write("<p>Value:<input type=\"text\" name=\"value\" /></p>")
            s.wfile.write("<p><input type=\"submit\" value=\"Post\" /></p>")
            s.wfile.write("</form>")
            s.wfile.write("</body></html>")
        else:
            s.send_response(200)
            s.send_header("Content-type", "application/json; charset=utf-8")
            s.end_headers()
            s.wfile.write(json.dumps(values, ensure_ascii=False))

    def log_message(format, *args):
        #print json.dumps(mqtt_values, ensure_ascii=False)
        return


def start_listen_http():
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class(('', http_port), HttpHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
#start application
def start():
    mqtt_thread = threading.Thread(target=start_update_mqtt)
    http_thread = threading.Thread(target=start_listen_http)
    mqtt_thread.start()
    http_thread.start()
    mqtt_thread.join()
    http_thread.join()

start()
