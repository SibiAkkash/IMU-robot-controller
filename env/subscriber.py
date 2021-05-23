import numpy as np
import pygame
from pygame.locals import *

from ahrs.filters import EKF
from ahrs.common.quaternion import QuaternionArray
import paho.mqtt.client as mqtt
from opengl import draw, init, resizewin
import time
import json

HOST = '192.168.1.4'
PORT = 8883
topic = "sensornode/livestream"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to broker")
    else:
        print(f"Connect returned result code {str(rc)}")

# callback for when a message is received from broker

def on_message(client, userdata, msg):
    decoded_msg = msg.payload.decode('utf-8')
    parsed = json.loads(decoded_msg)
    # send data to estimate orientation
    print(f"Received msg: {msg.topic} -> {parsed}")


def main():
	pygame.init()
	display = (800, 600)
	pygame.display.set_mode(display, DOUBLEBUF | OPENGL)	
	resizewin(800, 600)
	init()

	client = mqtt.Client(client_id="", clean_session=True,
                         userdata=None, transport="websockets")

	client.on_connect = on_connect
	client.on_message = on_message

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()

			draw([ieuler_angles_ned])

			pygame.display.flip()
			pygame.time.wait(10)


# client = mqtt.Client()
client = mqtt.Client(client_id="", clean_session=True,
                     userdata=None, transport="websockets")
# set callbacks
client.on_connect = on_connect
client.on_message = on_message
# connect to broker
client.connect(HOST, PORT)
client.loop_start()
print(f'Subscribing to topic: {topic}')
client.subscribe(topic)
time.sleep(60)
client.loop_stop()
