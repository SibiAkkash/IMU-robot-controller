# connect to mqtt broker
# set callbacks - on message, on connect
# subscribe to topic
# open a pygame window - all setting up needed for window

# draw loop
# on message handler is fired everytime a message is received from broker
# this should be sent to EKF to update orientation estimate
# the output euler angles should be sent to update orientation of cube

# store kalman filter object reference
# store incoming sensor measurements in a buffer
# on message -> call update routine of kalman filter -> add this to buffer
# draw loop takes the latest value from buffer to draw in screen

import time
import json

import numpy as np
from numpy.core.fromnumeric import resize
import paho.mqtt.client as mqtt

from ahrs.filters import EKF
from ahrs.common.quaternion import QuaternionArray
from ahrs.common.orientation import ecompass, q2rpy, acc2q

import pygame
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GLU import *

from opengl import draw, initWindow, resizewin

import threading, queue
import csv
from datetime import datetime
from typing import Dict, List

TOPIC = "sensornode/livestream"

q = queue.Queue()
log_file = open("../logs/log.json", "a")


def worker():
    while True:
        measurement = q.get()
        # log data to txt file
        # print("logging data...")
        # acc_log.write(json.dumps(measurement))
        json.dump(measurement, log_file)
        # print(measurement)
        q.task_done()


class OrientationViewer:
    def __init__(self, broker_host: str, broker_port: int):
        # initialise mqtt client
        self.client = mqtt.Client(
            client_id="", clean_session=True, userdata=None, transport="websockets"
        )
        # set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        # store host, port
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.is_connected = False
        # orietation estimates
        self.Q = []
        # initialise kalman filter object
        # ? initialise filter object on arrival of first measurement
        # TODO set to frequency of phone sensors
        # self.ekf = EKF(frequency=10)

    def connect_to_broker(self):
        self.client.connect(self.broker_host, self.broker_port)

        # runs a thread in the background that calls loop()
        # call loop_stop() to stop the thread
        self.client.loop_start()

        # subscribe to the sensornode/livestream topic
        print(f"Subscribing to topic {TOPIC}")
        self.client.subscribe(TOPIC)

        # start visualisation
        self.start()

    def disconnect_from_broker(self):
        if self.is_connected:
            self.client.loop_stop()
            self.is_connected = False
            print("Disconnected from broker")
            # print(self.Q)
        else:
            print("You haven't connected to the broker yet !")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected succesfully to broker")
            self.is_connected = True
        else:
            print(f"Connect returned result code {str(rc)}")

    def on_message(self, client, userdata, msg):
        decoded_msg = msg.payload.decode("utf-8")
        sensor_data = json.loads(decoded_msg)
        # print(sensor_data)
        # add to queue for logging
        q.put(sensor_data)
        self.update_estimate(sensor_data)

    def update_estimate(self, measurement):
        acc, gyro, mag = measurement["acc"], measurement["gyro"], measurement["mag"]

        acc = np.array([acc["x"], acc["y"], acc["z"]])
        gyro = np.array([gyro["x"], gyro["y"], gyro["z"]])
        mag = np.array([mag["x"], mag["y"], mag["z"]])

        if len(self.Q) == 0:
            # * this is the first measurement
            # initialising the filter expects arguments as N x 3 array
            acc = np.array([acc])
            gyro = np.array([gyro])
            mag = np.array([mag])

            # * initialise filter object on first measure
            self.ekf = EKF(gyr=gyro, acc=acc, mag=mag, frequency=20, frame="ENU")
            estimate = self.ekf.Q[0]

            # estimate orientation with acc and mag
            # estimate = ecompass(acc, mag, representation="quaternion")

            # estimate orientation with acc
            # estimate = acc2q(acc)

        else:
            # run the update step of the kalman filter
            # using the apriori estimate and current sensor measurements
            # estimate = self.ekf.update(q=self.Q[-1], gyr=gyro, acc=acc)
            estimate = self.ekf.update(q=self.Q[-1], gyr=gyro, acc=acc, mag=mag)

        # store it the orientation estimate for the next timestep
        self.Q.append(estimate)

    def start(self):
        pygame.init()
        display = (800, 600)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

        resizewin(800, 600)
        initWindow()

        # if we get message from broker, update orientation estimate
        # draw the new orientation
        # * game loop
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.disconnect_from_broker()
                    quit()

            # no measurements have been received till now
            if len(self.Q) == 0:
                continue

            # print(q2rpy(self.Q[-1]))
            draw(q2rpy(self.Q[-1]))

            pygame.display.flip()
            # pygame.time.wait(16)


viewer = OrientationViewer("192.168.1.7", 8883)
# threading.Thread(target=worker, daemon=True).start()
viewer.connect_to_broker()
# block until all sensor data has been logged
# q.join()
# close log file
log_file.close()
time.sleep(10)
viewer.disconnect_from_broker()
