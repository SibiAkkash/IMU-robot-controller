import numpy as np
import pandas as pd
from ahrs.common.orientation import q2rpy
from ahrs.filters.ekf import EKF

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from opengl import draw, initWindow, resizewin

def json_to_ndarray(data):
    """ 
    Convert python list of python objects to np.ndarray
    
    data: [{'x': float, 'y': float, 'z': float}]
    output: [[x1, y1, z1], [x2, y2, z2], ...]

    """
    tmp = []
    for row in data.index:
        msmt = data.loc[row]
        tmp.append([msmt['x'], msmt['y'], msmt['z']])
    return np.array(tmp)

tmp = pd.read_json("../logs/log.json")

acc = json_to_ndarray(tmp['acc'])
gyro = json_to_ndarray(tmp['gyro'])
mag = json_to_ndarray(tmp['mag'])

ekf = EKF(gyr=gyro, acc=acc, mag=mag)

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    resizewin(800, 600)
    initWindow()

    # game loop
    for i in range(len(ekf.Q)):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
        draw(q2rpy(ekf.Q[i]))

        pygame.display.flip()
        pygame.time.wait(100)
    
if __name__ == "__main__":
    main()


