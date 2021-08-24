"""This module controls interacting with an external MySQL server"""

import mysql.connector

class BrewingDatabase:
	def __init__(self, username = 'admin', password = 'password', host = '10.1.1.10', database = 'brewing'):
		self.username = username
		self.password = password
		self.host = host
		self.database = database
		self.brewID = None
	
	def __enter__(self):
		"""
		   This is for use with the 'with' statement
		   This function raises mysql.connection.Error if it is unable to connect
		"""
		try:
			self.connection = mysql.connector.connect(
				user = self.username,
				password = self.password,
				host = self.host,
				database = self.database)
			
			self._brewID, self.setpoint = self._readCurrentBrew()
		except:
			self.__exit__(*sys.exc_info())
			raise
	
	def __exit__(self, exception_type, exception_value, exception_trace):
		"""Cleanup from the 'with' statement"""
		self.connection.close()
	
	def isBrewRunning(self):
		return self._brewID != None
	
	def setpoint(self):
		return self.setpoint
	
	def _readCurrentBrew(self):
		"""Reads the current brewing setpoint, this will return None if the brewing is not currently enabled"""
		try:
			cursor = self.connection.cursor()
			query = "SELECT id, set_point FROM brews WHERE end_time IS NOT NULL"
			cursor.execute(query)
			return cursor.fetchone()
		finally:
			cursor.close()
	
	def writeCurrentStatus(self, temperature, is_heating):
		"""Writes the temperature and wether the heating mat is on to the database"""
		try:
			cursor = self.connection.cursor()
			query = "INSERT INTO timeseries SELECT %s, %s, %s"
			cursor.execute(query)
		finally:
			cursor.close()
