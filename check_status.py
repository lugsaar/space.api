#!/usr/bin/python3
#
# This script
# - checks the status in the network of the switch
# - changes the values
# - uploads the current status
#
import json
import os
import subprocess
import paho.mqtt.client as mqttc

from helpers import customLogger

logger = customLogger('customLogger','check_status.log')

has_changed = None
data = None

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")
    client.subscribe("space.api/state")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    

    if( msg.topic == "space.api/state"):

        logger.info(msg.topic+" " + str(msg.payload.decode('utf-8')))

        is_open = True if msg.payload.decode('utf-8').lower().capitalize() == "True" else False

        # is_open = bool(msg.payload.decode('utf-8'))

        global has_changed
        global data
        
        has_changed = data["state"]["open"] != is_open
        data["state"]["open"] = is_open

        logger.info("Status " + ("changed to " if has_changed else "remains ") + ("open" if is_open else "closed") + ".")

        try: 

            if has_changed:
                with open(DATA, "w") as f:
                    json.dump(data, f, indent=4)
                subprocess.check_call(["git", "add", "api.json"], cwd=HERE)
                subprocess.check_call(["git", "commit", "-m", "space is " + ("open" if is_open else "closed")], cwd=HERE)
            subprocess.call(["git", "push"], cwd=HERE)

        except CalledProcessError:
            logger.error('failed to commit state to api.json') 

if __name__ == '__main__':

    ## CONSTANTS
    HERE = os.path.dirname(__file__) or "."
    DATA = os.path.join(HERE, "api.json")
    # status.sh - ping
    # status.py - GPIO button press
    # STATUS = os.path.join(HERE, "status.py")

    client = mqttc.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("rohrpostix", 1883, 60)


    ## ALGORITHM
    subprocess.call(["git", "pull"], cwd=HERE)

    # load the data AFTER the pull
    with open(DATA) as f:
        data = json.load(f)

    # is_open = subprocess.call([STATUS]) == 0

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()