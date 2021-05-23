import numpy as np
import ahrs
from ahrs.filters import EKF
from ahrs.common.orientation import acc2q
from ahrs.common.quaternion import QuaternionArray
from ahrs.utils.io import load
import pandas as pd
import math

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def drawText(position, textString, size):
    font = pygame.font.SysFont("Courier", size, True)
    textSurface = font.render(textString, True, (255, 255, 255, 255), (0, 0, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glRasterPos3d(*position)
    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)


def draw(angles) -> None :
	# print(f'drawing phone orientation... {angles}')
	# psi, theta, phi -> # yaw, pitch, roll
	
	#? roll(x), pitch(y), yaw(z) -> Normal
	#? roll(y), pitch(x), yaw(z) -> phone
	
	[yaw, pitch, roll] = angles
	# convert to radians
	pitch *= 180.0 / math.pi
	yaw   *= 180.0 / math.pi
	yaw   -= -1.15  # magnetic Declination at Chennai, TamilNadu, India is - 1 degress 15 min
	roll  *= 180.0 / math.pi

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glLoadIdentity()
	glTranslatef(0, 0.0, -7.0)

	drawText((-2.6, -1.8, 2), "Yaw: %f, Pitch: %f, Roll: %f" %(yaw, pitch, roll), 16)

	glRotatef(-roll, 0.00, 0.00, 1.00)
	glRotatef(pitch, 1.00, 0.00, 0.00)
	glRotatef(yaw, 0.00, 1.00, 0.00)

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

def init():
	glShadeModel(GL_SMOOTH)
	glClearColor(0.0, 0.0, 0.0, 0.0)
	glClearDepth(1.0)
	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LEQUAL)
	glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

def resizewin(width, height):
    """
    For resizing window
    """
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0*width/height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


'''
	* NED reference frame: North, East, Down 
'''

def process_data(acc_path: str, gyro_path: str, mag_path: str, frame='NED') -> np.ndarray:
	# process data
	acc = pd.read_csv(f'../data/{acc_path}')
	gyro = pd.read_csv(f'../data/{gyro_path}')
	mag = pd.read_csv(f'../data/{mag_path}')
	print(f'Read sensor data')

	# drop timestamp column
	acc.drop(['Timestamp'], axis=1, inplace=True)
	gyro.drop(['Timestamp'], axis=1, inplace=True)
	mag.drop(['Timestamp'], axis=1, inplace=True)
	
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

	print('Getting orientation estimates')
	# get orientation estimates for each sensor sample
	ekf = EKF(gyr=gyro_list, acc=acc_list, mag=mag_list, frame=frame)
	euler_angles = QuaternionArray(ekf.Q).to_angles()
	print('Converted quaternions to euler angles')
	
	return euler_angles

euler_angles_ned = process_data(
		acc_path="acc.csv", 
		gyro_path="ang_vel.csv", 
		mag_path="mag.csv", 
		frame='NED'
	)

euler_angles_enu = process_data(
		acc_path="acc.csv", 
		gyro_path="ang_vel.csv", 
		mag_path="mag.csv", 
		frame='ENU'
	)

num_samples = len(euler_angles_ned)
  
def main():
	pygame.init()
	display = (800, 600)
	pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
	resizewin(800, 600)
	init()

	for i in range(num_samples):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()	
		
		draw(euler_angles_ned[i])

		pygame.display.flip()
		pygame.time.wait(10) 

if __name__ == "__main__":
	main()
	pygame.quit()
	quit()	
		