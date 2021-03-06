#!/usr/bin/env python3
"""
A subclass of mqtt client which supports subscriptions going to multiple different callbacks. The purpose is to allow
a complex program to share one MQTT client among a number of destinct functions or even separate modules.
"""
__author__ = "Daniel Casner <www.danielcasner.org>"

import paho.mqtt.client as mqtt
import logging
import queue

def topic_join(*args):
    "Returns the tokens specified jouint by the MQTT topic namespace separatot"
    return "/".join(args)

class SharedClient(mqtt.Client):
    "MQTT client set up for shared use"
    
    class Subscription(list):
        "A list of callbacks that also has a stored QOS and topic"
        def __init__(self, topic, qos, callbacks=[]):
            list.__init__(self, callbacks)
            self.topic = topic
            self.qos = qos
    
    def __init__(self, *args, **kwargs):
        "Initalize client"
        mqtt.Client.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.queue  = queue.Queue(kwargs.get('queue_maxsize', 0))
        self.loop_timeout = kwargs.get('queue_timeout', 1.0)
        self._connected = False
        self._subscriptions = {}
    
    def subscribe(self, topic, qos, callback):
        "Subscribe to a given topic with callback"
        self.logger.info("Subscribing to {:s} at qos={:d}".format(topic, qos))
        needToSubscribe = True
        if topic in self._subscriptions:
            sub = self._subscriptions[topic]
            if qos > sub.qos:
                mqtt.Client.unsubscribe(self, topic)
                sub.qos = qos
            else:
                needToSubscribe = False
            sub.append(callback)
        else:
            self._subscriptions[topic] = self.Subscription(topic, qos, [callback])
        if self._connected and needToSubscribe:
            sub = self._subscriptions[topic]
            mqtt.Client.subscribe(self, sub.topic, sub.qos)
    
    def unsubscribe(self, topic, callback):
        "Unsubscribe a single callback"
        self.logger.info("Unsubscribing from {:s}".format(topic))
        self._subscriptions[topic].remove(callback)
        if len(self._subscriptions[topic]) == 0:
            mqtt.Client.unsubscribe(self, topic)
            del self._subscriptions[topic]
    
    def on_connect(self, client, userdata, flags, rc):
        "Callback on MQTT connection"
        self._connected = True
        if len(self._subscriptions):
            mqtt.Client.subscribe(self, [(s.topic, s.qos) for s in self._subscriptions.values()])
        
    def on_disconnect(self, client, userdata, rc):
        self._connected = False
        
    def on_message(self, client, userdata, msg):
        "Callback on MQTT message"
        self.logger.debug("Received {0.topic:s} -> {0.payload!r}".format(msg))
        for cb in self._subscriptions[msg.topic]:
            self.logger.debug("\tCalling {}".format(repr(cb)))
            self.queue.put((cb, msg), False)
    
    def __next__(self):
        try:
            cb, msg = self.queue.get(True, self.loop_timeout)
        except queue.Empty:
            pass
        else:
            cb(msg)
