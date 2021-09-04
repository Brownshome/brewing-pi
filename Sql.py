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
                self._brewID, self._start_time, self._sg_sample_time, self._bottle_time, self._setpoint, self._deadband_high, self._deadband_low, self._high_trip_point, self._low_trip_point, self._sg_reading = currentBrew
            return self
        except:
            self.__exit__(*sys.exc_info())
            raise RuntimeError()
    
    def __exit__(self, exception_type, exception_value, exception_trace):
        """Cleanup from the 'with' statement"""
        if self._connection != None:
            self._connection.close()
    
    def isBrewRunning(self):
        return self._brewID != None
    
    def setpoint(self):
        return self._setpoint
    
    def BrewID(self):
        return self._brewID
    
    def sg_sample_time(self):
        return self._sg_sample_time
    
    def bottle_time(self):
        return self._bottle_time
    
    def start_time(self):
        return self._start_time
    
    def deadband_high(self):
        return self._deadband_high
    
    def deadband_low(self):
        return self._deadband_low
    
    def high_trip_point(self):
        return self._high_trip_point
    
    def low_trip_point(self):
        return self._low_trip_point
    
    def _readCurrentBrew(self):
        """Reads the current brewing settings, this will return None if the brewing is not currently enabled"""
        try:
            cursor = self._connection.cursor()
            query = "SELECT id, start_time, sg_sample_time, bottle_time, set_point, deadband_high, deadband_low, high_trip_point, low_trip_point, sg_reading FROM brews WHERE end_time IS NULL AND start_time IS NOT NULL"
            cursor.execute(query)
            return cursor.fetchone()
        finally:
            cursor.close()
    
    def writeCurrentStatus(self, time_stamp, temperature, controller_op, brew_stage):
        """Writes the temperature and brew data to the database"""
        try:
            cursor = self._connection.cursor()
            query = "INSERT INTO timeseries (id, time, temperature, set_point, controller_op, brew_stage, sg) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (self._brewID, time_stamp, temperature, self._setpoint, controller_op, brew_stage, self._sg_reading))
        finally:
            cursor.close()

