# Controls the temperature sensor (DS18B20)

import os
import io

import RPi.GPIO as GPIO

_deviceDirectory = '/sys/bus/w1/devices/'

def _findDeviceId(family):
	return next(
		device for device in os.listdir(_deviceDirectory)
		if device.startswith(str(family) + '-') and os.path.isfile(_deviceDirectory + device + '/w1_slave'))

class TemperatureSensor:
	def __init__(self, pin = 4, pullState = GPIO.PUD_UP, family = 28):
		GPIO.setup(4, GPIO.IN, pull_up_down = pullState)
		self._deviceID = _findDeviceId(family)
		if self._deviceID == None:
			raise RuntimeException('Unable to find temperature sensor')
	
	def readTemperature(self):
		with io.open(_deviceDirectory + self._deviceID + '/w1_slave', "r") as file:
			if not file.readline().endswith('YES\n'):
				raise RuntimeException('Invalid CRC')
			number = file.readline().partition('t=')[2]
			return float(number) / 1000.0
