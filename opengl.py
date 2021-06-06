import numpy as np
import pandas as pd
import math
from ahrs.filters import EKF
from ahrs.common.orientation import acc2q
from ahrs.common.quaternion import QuaternionArray

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


def drawText(position, textString, size):
    font = pygame.font.SysFont("Courier", size, True)
    textSurface = font.render(textString, True, (255, 255, 255, 255), (0, 0, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glRasterPos3d(*position)
    glDrawPixels(
        textSurface.get_width(),
        textSurface.get_height(),
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        textData,
    )


def quat_to_ypr(q):
    yaw = math.atan2(
        2.0 * (q[1] * q[2] + q[0] * q[3]), q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3]
    )
    pitch = -math.sin(2.0 * (q[1] * q[3] - q[0] * q[2]))
    roll = math.atan2(
        2.0 * (q[0] * q[1] + q[2] * q[3]), q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3]
    )
    pitch *= 180.0 / math.pi
    yaw *= 180.0 / math.pi
    yaw -= -1.15  # Declination at Chandrapur, Maharashtra is - 0 degress 13 min
    roll *= 180.0 / math.pi
    return [yaw, pitch, roll]


def draw(quat) -> None:
    # psi, theta, phi -> # yaw, pitch, roll

    # ? roll(x), pitch(y), yaw(z) -> Normal
    # ? roll(y), pitch(x), yaw(z) -> phone

    # print(quat)
    # [ 0.63203606  0.04095045 -0.27498346 -0.72335163]
    [w, nx, ny, nz] = quat

    [yaw, pitch, roll] = quat_to_ypr(quat)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0.0, -7.0)

    drawText((-2.6, -1.8, 2), "Yaw: %f, Pitch: %f, Roll: %f" % (yaw, pitch, roll), 16)

    glRotatef(2 * math.acos(w) * 180.00 / math.pi, -1 * nx, nz, ny)

    # glRotatef(-yaw, 0.00, 0.00, 1.00)
    # glRotatef(pitch, 1.00, 0.00, 0.00)
    # glRotatef(roll , 0.00, 1.00, 0.00)

    glBegin(GL_QUADS)

    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(1.0, 0.2, 1.0)

    glColor3f(1.0, 0.5, 0.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(1.0, -0.2, -1.0)

    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)

    glColor3f(1.0, 1.0, 0.0)
    glVertex3f(1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, -1.0)

    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, 1.0)

    glColor3f(1.0, 0.0, 1.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, -1.0)

    glEnd()


def initWindow():
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


def resizewin(width, height):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0 * width / height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def process_data(acc_path: str, gyro_path: str, mag_path: str, frame="NED") -> np.ndarray:
    # process data
    acc = pd.read_csv(f"../data/{acc_path}")
    gyro = pd.read_csv(f"../data/{gyro_path}")
    mag = pd.read_csv(f"../data/{mag_path}")
    print(f"Process data called ? Read sensor data")

    # drop timestamp column
    acc.drop(["Timestamp"], axis=1, inplace=True)
    gyro.drop(["Timestamp"], axis=1, inplace=True)
    mag.drop(["Timestamp"], axis=1, inplace=True)

    # find the min shape, some sensors have less samples
    num_samples = min(acc.shape[0], gyro.shape[0], mag.shape[0])

    # reshape all sensors to same no of samples
    acc.drop(acc.index[num_samples:], inplace=True)
    gyro.drop(gyro.index[num_samples:], inplace=True)
    mag.drop(mag.index[num_samples:], inplace=True)

    assert acc.shape == mag.shape == gyro.shape

    # convert to np.ndarray
    acc_list = acc.to_numpy()
    gyro_list = gyro.to_numpy()
    mag_list = mag.to_numpy()
    print(acc_list[:2])
    print(gyro_list[:2])
    print(mag_list[:2])

    print("Getting orientation estimates")

    Q = []
    ekf = EKF()
    initial = acc2q(acc_list[0])
    Q.append(initial)
    for t in range(1, 2):
        estimate = ekf.update(Q[-1], gyro_list[t], acc_list[t])
        print(estimate)
        Q.append(estimate)

    # get orientation estimates for each sensor sample
    ekf = EKF(gyr=gyro_list, acc=acc_list, mag=mag_list, frame=frame)
    euler_angles = QuaternionArray(ekf.Q).to_angles()
    print("Converted quaternions to euler angles")

    return euler_angles
