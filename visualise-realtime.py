
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

