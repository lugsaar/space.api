#!/usr/bin/python3
#
# This script
# - checks the status in the network of the switch
# - changes the values
# - uploads the current status
#

import json
import os
import sys
import subprocess
import time  
from threading import Timer 
import paho.mqtt.client as mqttc

from helpers import customLogger

logger = customLogger('customLogger','check_status.log')



class MQTT2SpaceApiBridge(mqttc.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ## CONSTANTS
        self.HERE = os.path.dirname(__file__) or '.'
        self.DATA = os.path.join(self.HERE, 'api.json')
        self.CONFIG = os.path.join(self.HERE, 'config.json')

        self.has_changed = None
        self.data = None
        self.config = None
        self.last_update = None

    
        self._timer = None

        ## ALGORITHM
        subprocess.call(["git", "pull"], cwd=self.HERE)

        # load the data AFTER the pull
        with open(self.DATA) as data_file:
            self.data = json.load(data_file)


        with open(self.CONFIG) as config_file:
            self.config = json.load(config_file)

    def _check_state_frequency_fun(self, update_time):
        logger.info('checking last update time !!')

        if self.last_update < (time.time() - update_time):
            logger.info( 'last update more than {} minutes ago'.format(update_time) )
 
        self._timer = Timer(update_time, self._check_state_frequency_fun, [update_time] )
        self._timer.start() 

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#")
        # client.subscribe("space.api/state")
        if self.config['state_topic']:
            client.subscribe(self.config['state_topic'])


    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):

        if( self.config['state_topic'] and self.config['expected_key'] and self.config['expected_state_value'] ):

            if self.config['state_topic']is not None:
                state_topic = self.config['state_topic']
            else:
                logger.error('no state topic set to listen ...')

            if self.config['expected_key'] is not None:
                expected_key = self.config['expected_key']

            if self.config['expected_state_value'] is not None:
                expected_state_value = self.config['expected_state_value']


            if( msg.topic == self.config['state_topic']):

                if self._timer == None:
                    self._timer = Timer(300, self._check_state_frequency_fun, [300])
                    self._timer.start()
                    logger.info('state message received, starting timer first time ...')
                else:
                    self._timer.cancel()
                    self._timer = Timer(300, self._check_state_frequency_fun, [300])
                    self._timer.start()
                    logger.info('state message received while timer is running, reseting timer ...')
                    

                # logger.info(msg.topic+" " + str(msg.payload.decode('utf-8')))
                payload = json.loads( str(msg.payload.decode('utf-8'))  )

                # logger.info('json string' + str(payload))

                is_open = True if payload[expected_key] == expected_state_value else False

                # is_open = True if msg.payload.decode('utf-8').lower().capitalize() == "True" else False
                # is_open = bool(msg.payload.decode('utf-8'))


                self.has_changed = self.data["state"]["open"] != is_open
                self.data["state"]["open"] = is_open

                logger.info("Status " + ("changed to " if self.has_changed else "remains ") + ("open" if is_open else "closed") + ".")

                try: 

                    if self.has_changed:
                        self.last_update = time.time()

                        with open(self.DATA, "w") as f:
                            json.dump(self.data, f, indent=4)

                        subprocess.check_call(["git", "add", "api.json"], cwd=self.HERE)
                        subprocess.check_call(["git", "commit", "-m", "space is " + ("open" if is_open else "closed")], cwd=self.HERE)
                        subprocess.call(["git", "push"], cwd=self.HERE)
                        logger.info('pushing new state to GitHub Repo')
                except CalledProcessError:
                    logger.error('failed to commit state to api.json') 


if __name__ == '__main__':

    # Checking the value of the environment variable
    if os.environ.get('MQTT_HOST'):
        MQTT_HOST = os.environ.get('MQTT_HOST')
        logger.info('Try to connect to ' + str(MQTT_HOST) + ' ...')
    else:
        logger.error( 'No MQTT Host set ... exiting the application with error' )
        sys.exit(-1)

    if os.environ.get('MQTT_USER'):
        MQTT_USER = os.environ.get('MQTT_USER')
    else:
        logger.error( 'No MQTT User set ... exiting the application with error' )
        sys.exit(-1)

    if os.environ.get('MQTT_USER_PW'):
        MQTT_USER_PW = os.environ.get('MQTT_USER_PW')
    else:
        logger.error( 'No MQTT User password set ... exiting the application with error' )
        sys.exit(-1)


    bridge = MQTT2SpaceApiBridge()

    bridge.username_pw_set(MQTT_USER, password = MQTT_USER_PW)

    bridge.connect(MQTT_HOST, 1883, 60)
    
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    bridge.loop_forever()

    