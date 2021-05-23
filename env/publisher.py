import paho.mqtt.client as mqtt
import time
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print("Connected successfully")
	else:
		print(f"Connect returned result code {str(rc)}")

# callback for when a PUBLISH message is received from server
def on_message(client, userdata, msg):
	print(f"Received msg: {msg.topic} -> {msg.payload.decode('utf-8')}")


broker = 'localhost'
port = 1883
topic = "sensornode/livestream"
client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port)

for i in range(10):
	client.publish(topic, f'msg no: {i + 1}')
	time.sleep(2)

