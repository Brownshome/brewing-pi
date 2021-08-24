"""This module controls interacting with an external MySQL server"""

import sys
import mysql.connector

class BrewingDatabase:
	def __init__(self, username = 'brewing_pi', host = '10.1.1.10', database = 'brewing'):
		self._username = username
		self._host = host
		self._database = database
		self._brewID = None
		self._connection = None
	
	def __enter__(self):
		"""
		   This is for use with the 'with' statement
		   This function raises mysql.connection.Error if it is unable to connect
		"""
		try:
			self._connection = mysql.connector.connect(
				user = self._username,
				host = self._host,
				database = self._database,
				charset = 'utf8',
				collation = 'utf8_general_ci')
			
			currentBrew = self._readCurrentBrew()
			if currentBrew != None:
				self._brewID, self._setpoint = currentBrew
			
			return self
		except:
			self.__exit__(*sys.exc_info())
			raise
	
	def __exit__(self, exception_type, exception_value, exception_trace):
		"""Cleanup from the 'with' statement"""
		if self._connection != None:
			self._connection.close()
	
	def isBrewRunning(self):
		return self._brewID != None
	
	def setpoint(self):
		return self._setpoint
	
	def _readCurrentBrew(self):
		"""Reads the current brewing setpoint, this will return None if the brewing is not currently enabled"""
		try:
			cursor = self._connection.cursor()
			query = "SELECT id, set_point FROM brews WHERE end_time IS NULL"
			cursor.execute(query)
			return cursor.fetchone()
		finally:
			cursor.close()
	
	def writeCurrentStatus(self, temperature, isHeating):
		"""Writes the temperature and wether the heating mat is on to the database"""
		try:
			cursor = self._connection.cursor()
			query = "INSERT INTO timeseries (id, temperature, set_point, is_heating) VALUES (%s, %s, %s, %s)"
			cursor.execute(query, (self._brewID, temperature, self.setpoint, isHeating))
		finally:
			cursor.close()
