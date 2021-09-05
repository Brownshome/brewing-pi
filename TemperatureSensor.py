#!/bin/env python3
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
			raise RuntimeError('Unable to find temperature sensor')
	
	def readLine(self, file):
		line = file.readline().strip()
		retryCount = 0
		
		while not line:
			retryCount += 1
			if retryCount > 10:
				raise RuntimeError('No data in file')
			line = file.readline().strip()
		
		return line
	
	def readTemperature(self):
		with io.open(_deviceDirectory + self._deviceID + '/w1_slave', "r") as file:
			if not self.readLine(file).endswith('YES'):
				raise RuntimeError('Invalid CRC')
			number = self.readLine(file).partition('t=')[2]
			return float(number) / 1000.0

if __name__ == "__main__":
	GPIO.setmode(GPIO.BCM)
	TISensor = TemperatureSensor()
	PV = TISensor.readTemperature()
	print('PV = '+str(PV))
