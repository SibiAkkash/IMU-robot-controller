
## Steps to run
Clone the repo
### Create a virtual environment
* `python -m venv env`
* `cd env/`
* Activate the virtual env
### Install requirements
* `python -m pip install -r requirements.txt`

## Local mosquitto broker
* Download [mosquitto](https://mosquitto.org/download/)
* `cd` into the install location
* Add these lines to the `mosquitto.conf` file, to allow remote clients to connect. 
```
per_listener_settings true
listener 1883
protocol mqtt

listener 8883
protocol websockets
```

* **Remove trailing spaces from the above lines, if any**
* Start the broker by running `mosquitto -c [path-to-mosquitto.conf] -v`


The `subscriber.py` and `publisher.py` have sample implementations of pub sub with mqtt.  

_Set appropriate IP and port of the mosquitto broker_.  