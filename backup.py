import bpy
import math
import socket
import json
from os import link
from mathutils import Euler

import numpy as np
from numpy.core.fromnumeric import resize
import paho.mqtt.client as mqtt

import threading, queue
import csv
from datetime import datetime

from ahrs.filters import EKF
from ahrs.common.quaternion import QuaternionArray
from ahrs.common.orientation import ecompass, q2rpy, acc2q

imu_topic = "stream/imu"
jaw_angle_topic = "stream/jaw_angle"
link_angle_topic = "stream/link_angle"

class OrientationViewer:
    def __init__(self, broker_host: str, broker_port: int):
        # Get armature:
        self.arm1 = bpy.data.objects["Armature.001"]
        # Select as active and set mode:
        bpy.context.view_layer.objects.active = self.arm1
        bpy.ops.object.mode_set(mode="POSE")
        # Get bones for each limb:
        self.jawBone = self.arm1.pose.bones[4]
        self.limb3 = self.arm1.pose.bones[3]
        self.limb2 = self.arm1.pose.bones[2]
        self.limb1 = self.arm1.pose.bones[1]
        # Initialise MQTT client
        self.client = mqtt.Client(
            client_id="", clean_session=True, userdata=None, transport="websockets"
        )
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        # Store host, port
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.is_connected = False
        # orietation estimates
        self.Q = []
        #? initialise filter object on arrival of first measurement
        # TODO set to frequency of phone sensors
        # self.ekf = EKF(frequency=10)

    def connect_to_broker(self):
        self.client.connect(self.broker_host, self.broker_port)
        # runs a thread in the background that calls loop()
        # call loop_stop() to stop the thread
        self.client.loop_start()
        # subscribe to the sensornode/livestream topic
        print(f"Subscribing to topics: {imu_topic}, {jaw_angle_topic}, {link_angle_topic}")
        self.client.subscribe([(imu_topic, 0), (jaw_angle_topic, 0), (link_angle_topic, 0)])
        self.start()

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print(mid)

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
        # print(msg.topic, decoded_msg)
        if msg.topic == link_angle_topic:
            link_angle = json.loads(decoded_msg)["link_angle"]
            self.limb3.rotation_euler = Euler((0, 0, -link_angle), "XYZ")
            print(link_angle)
        elif msg.topic == jaw_angle_topic:
            jaw_angle = json.loads(decoded_msg)["jaw_angle"]
            self.jawBone.rotation_euler = Euler((0, 0, -(jaw_angle / 10)), "XYZ")
            print(jaw_angle)
        elif msg.topic == imu_topic:
            sensor_data = json.loads(decoded_msg)
            q.put(sensor_data)
            self.update_estimate(sensor_data)

    def update_estimate(self, measurement):
        acc, gyro, mag = measurement["acc"], measurement["gyro"], measurement["mag"]

        acc = np.array([acc["x"], acc["y"], acc["z"]])
        gyro = np.array([gyro["x"], gyro["y"], gyro["z"]])
        mag = np.array([mag["x"], mag["y"], mag["z"]])

        if len(self.Q) == 0:
            # this is the first measurement
            # initialising the filter expects arguments as N x 3 array
            acc = np.array([acc])
            gyro = np.array([gyro])
            mag = np.array([mag])

              # initialise filter object on first measure
            self.ekf = EKF(gyr=gyro, acc=acc, mag=mag, frequency=20, frame="ENU")
            estimate = self.ekf.Q[0]

            # store the first measurement
            self.iRef = q2rpy(estimate)

        else:
            # run the update step of the kalman filter
            # using the apriori estimate and current sensor measurements
            estimate = self.ekf.update(q=self.Q[-1], gyr=gyro, acc=acc, mag=mag)

        # store it the orientation estimate for the next timestep
        self.Q.append(estimate)

    def start(self):
        # When we get message from broker, update orientation
        while True:
            if len(self.Q) == 0:
                continue
            gData = q2rpy(self.Q[-1]) - self.iRef
            print(gData)
            # 0 up/down, 2 left/right
            self.limb2.rotation_euler = Euler((-gData[2], 0, gData[0]), "XYZ")
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)


def main():
    myIP = socket.gethostbyname_ex(socket.gethostname())[-1][-1]
    PORT = 8883
    viewer = OrientationViewer(myIP, PORT)
    viewer.connect_to_broker()


"""
- X on Limb 2 to turn the arm [gyro]
- Z on Limb 2 to tilt the arm [gyro]
- Z on Limb 3 to bend the arm [slider]
- Z on Limb 4 (jawBone) to open (0.5)/close (0) [slider]
"""


def reset():
    # Get armature:
    arm1 = bpy.data.objects["Armature.001"]
    # Select as active and set mode:
    bpy.context.view_layer.objects.active = arm1
    bpy.ops.object.mode_set(mode="POSE")
    # Get bones for each limb:
    jawBone = arm1.pose.bones[4]
    limb3 = arm1.pose.bones[3]
    limb2 = arm1.pose.bones[2]
    limb1 = arm1.pose.bones[1]
    base = arm1.pose.bones[0]
    # Set default rotation:
    jawBone.rotation_euler = Euler((0, 0, 0), "XYZ")
    limb3.rotation_euler = Euler((0, 0, 0.15), "XYZ")
    limb2.rotation_euler = Euler((0, 0, -0.5), "XYZ")
    base.rotation_euler = limb1.rotation_euler = Euler((0, 0, 0), "XYZ")


if __name__ == "__main__":
    main()
    # reset()
