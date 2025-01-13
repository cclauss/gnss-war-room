from datetime import timedelta
import os
import time
from typing import Any, Callable
import paho.mqtt.enums as mqttEnums
from paho.mqtt.client import Client as MqttClient, MQTTMessage, DisconnectFlags
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties
from pynmeagps import NMEAReader, NMEAMessage
from config import Config
from gnss.nmea import GnssData, updateGnssDataWithMessage


def createMqttSubscriberClient(
	config: Config, onNewDataCallback: Callable[[bytes, GnssData], None]
) -> MqttClient:
	"""Create the subscriber MQTT client"""
	mqttClient = MqttClient(mqttEnums.CallbackAPIVersion.VERSION2)
	mqttClient.on_message = createSubscriberCallback(
		onNewDataCallback, timedelta(seconds=int(config.satelliteTTL))
	)

	try:
		mqttClient.connect(config.mqttHost, config.mqttPort)
		mqttClient.loop_start()
	except ConnectionRefusedError:
		print("Error! Unable to connect to MQTT broker. Don't Panic!")
		retryConnect(mqttClient, config)

	mqttClient.on_disconnect = onDisconnect
	mqttClient.subscribe("gnss/rawMessages")
	return mqttClient


def createMqttPublisherClient(config: Config) -> MqttClient:
	"""Create the publisher MQTT client"""
	mqttClient = MqttClient(mqttEnums.CallbackAPIVersion.VERSION2, client_id="publisher")

	publisherPassword = os.environ.get("GNSS_PUBLISHER_PASSWORD")
	if publisherPassword:
		mqttClient.username_pw_set("gnssreceiver", publisherPassword)

	try:
		mqttClient.connect(config.mqttHost, config.mqttPort)
		mqttClient.loop_start()
	except ConnectionRefusedError:
		print("Error! Unable to connect to MQTT broker. Don't Panic!")
		retryConnect(mqttClient, config)

	mqttClient.on_disconnect = onDisconnect
	return mqttClient


def retryConnect(mqttClient: MqttClient, config: Config, attemptsLeft=5):
	"""Retry connecting to the MQTT broker if it fails on startup"""
	if attemptsLeft < 0:
		print("Failed to connect!")
		os.abort()

	time.sleep(1)
	print(f"Retrying, {attemptsLeft} attempts remaining.")
	try:
		mqttClient.connect(config.mqttHost, config.mqttPort)
		mqttClient.loop_start()
	except ConnectionRefusedError:
		retryConnect(mqttClient, config, attemptsLeft - 1)


def onDisconnect(
	_client: MqttClient,
	_userdata: Any,
	_disconnectFlags: DisconnectFlags,
	_reasonCode: ReasonCode,
	_properties: Properties,
):
	"""Exit the program if the MQTT broker disconnects, as attempting to reconnect doesn't seem to work"""
	print("Disconnected from MQTT broker, exiting")
	os.abort()


def createSubscriberCallback(
	onNewDataCallback: Callable[[bytes, GnssData], None], satelliteTTL: timedelta
) -> Callable[[MqttClient, Any, MQTTMessage], None]:
	"""Create a callback for the MQTT subscriber client to handle incoming messages"""
	gnssData = GnssData()

	def onMessage(_client: MqttClient, _userdata: Any, message: MQTTMessage):
		nonlocal gnssData
		nonlocal onNewDataCallback
		parsedMessage = NMEAReader.parse(message.payload)
		if not isinstance(parsedMessage, NMEAMessage):
			return
		gnssData = updateGnssDataWithMessage(gnssData, parsedMessage, satelliteTTL)
		onNewDataCallback(message.payload, gnssData)

	return onMessage
