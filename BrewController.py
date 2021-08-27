# Fermentation Batch Controller
#---------------------------------------
# This program will output to heating and cooling devices to keep the brew at a set point.
# This program will execute using the cron task
# LEDs are driven to indicate if the temperature is under control.
# The brew duration is monitored, and prompts are raised to measure sg and bottle.
# Data for the brew including the setpoint, timings, and control settings are retrieved from a master database.
# A local copy of these values is stored in case the link to the external database is lost
# Each program scan, the temperature and control data is output back to an sql database
#
# Data Flow
#    Local Name        |        Description
#-----------------------------------------------------------------------------------------------------
#   id, setpoint       |   Read from Brew Record, Output to local record, and to sql TimeSeries. 
#                      |   Not passed to sql write function, as it is local to that function.
#----------------------|------------------------------------------------------------------------------
# deadbands for alarms |   Read from Brew Record, Output to local record, and to sql TimeSeries. 
#   and controller,    | 
# brew timer period    |
#     durations,       |
#  brew start time     |
#----------------------|------------------------------------------------------------------------------
# Actual Temperature,  |    Derrived from controller program or read from GPIO. 
# Heater and Cooler OP |    Stored to sql TimeSeries, and to local storage, 
#     Brew Period      |    as a local backup in case the sql is lost


import os
import csv
import TemperatureSensor
import Sql
from pathlib import Path
import RPi.GPIO as GPIO
from datetime import datetime
from datetime import timedelta

# Variable Declarations
#FilePath = "C:\\Users\\Martin\\Documents\\Python Stuff\\"
FilePath = str(Path.home()) + '/brew/'
now = datetime.now()
RedGP = 14
GrnGP = 15
BluGP = 18
HtrGP = 2
ClrGP = 3

# Setup IO
#GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(HtrGP,GPIO.OUT) # Heating
GPIO.setup(ClrGP,GPIO.OUT) # Cooling
GPIO.setup(RedGP,GPIO.OUT) # Red LED
GPIO.setup(GrnGP,GPIO.OUT) # Green LED
GPIO.setup(BluGP,GPIO.OUT) # Blue LED

# Function Declarations
def WritePreviousRecord(FileName, DataStr, TypeStr):
    file = open(FileName, TypeStr)
    file.write(DataStr)
    file.close()

def SetLED(LEDColour):
    if LEDColour == 'Red':
        GPIO.output(RedGP,1)
        GPIO.output(GrnGP,0)
        GPIO.output(BluGP,0)
    if LEDColour == 'Green':
        GPIO.output(RedGP,0)
        GPIO.output(GrnGP,1)
        GPIO.output(BluGP,0)
    if LEDColour == 'Blue':
        GPIO.output(RedGP,0)
        GPIO.output(GrnGP,0)
        GPIO.output(BluGP,1)

def SetOP(ContrlMode):
    if ContrlMode == 'Heat':
        GPIO.output(HtrGP,1)
        GPIO.output(ClrGP,0)
    elif ContrlMode == 'Cool':
        GPIO.output(HtrGP,0)
        GPIO.output(ClrGP,1)
    else:
        GPIO.output(HtrGP,0)
        GPIO.output(ClrGP,0)

# Read Brew Data from File (id, brew_name, start_time, sg_sample_time, bottle_time, set_point, deadband_high, deadband_low, high_trip_point, low_trip_point)
# If this File is not Found, run NewBatch.py to Start a new brew
#BatchData = ReadPreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\ThisBatch.CSV')
with Sql.BrewingDatabase() as BrewData:
    BrewID = int(BrewData.BrewID())
    print('ID = '+str(BrewID))
    SGSampleTime = BrewData.sg_sample_time()
    print('SGSamplesec = '+str(SGSampleTime))
    BottleTime = BrewData.bottle_time()
    print('BottleTime = '+str(BottleTime))
    StartTime = BrewData.start_time()
    print('StartTime = '+str(StartTime))
    SP = float(BrewData.setpoint())
    print('SP = '+str(SP))
    dbHigh = float(BrewData.deadband_high())
    print('dbHigh = '+str(dbHigh))
    dbLow = float(BrewData.deadband_low())
    print('dbLow = '+str(dbLow))
    HighDevTP = float(BrewData.high_trip_point())
    print('HighDevTP = '+str(HighDevTP))
    LowDevTP = float(BrewData.low_trip_point())
    print('LowDevTP = '+str(LowDevTP))

# Read Previous Record from local file (StartTime, id, Temperature, SP, TempBand, TimePeriod)
with open(FilePath + 'LastReadings.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        OldST = row[0]
        print('Oldid = '+str(OldST))
        OldSP = row[3]
        print('OldSP = '+str(OldSP))
        OldOP = int(row[4])
        print('OldOP = '+str(OldOP))
        OldTP = int(row[5])
        print('OldTP = '+str(OldTP))

# If sql data is lost, substitute local values

# Read Current Temperature
TISensor = TemperatureSensor.TemperatureSensor()
PV = TISensor.readTemperature()
print('PV = '+str(PV))

# Determine Current Temperature Band
if PV > (SP + HighDevTP):
    TempBand = 2 #HighAlarm
    ControllerOP = -1 #Cool
elif PV > (SP + dbHigh):
    TempBand = 1 #High
    ControllerOP = -1 #Cool
elif PV > SP:
    TempBand = 0 #Good
    ControllerOP = min(OldOP,0)
elif PV > (SP - dbLow):
    TempBand = 0 #Good
    ControllerOP = max(OldOP,0)
elif PV > (SP - LowDevTP):
    TempBand = -1 #Low
    ControllerOP = 1 #Heat
else:
    TempBand = -2 #LowAlarm
    ControllerOP = 1 #Heat
print('TempBand = '+str(TempBand))
print('ControllerOP = '+str(ControllerOP))

# Drive LEDS
if TempBand > 0:
    SetLED('Red')
elif TempBand < 0:
    SetLED('Blue')
else:
    SetLED('Green')

# Drive Heater / Cooler Outputs
if ControllerOP > 0:
    SetOP('Heat')
elif ControllerOP < 0:
    SetOP('Cool')
else:
    SetOP('None')

# Determine Current Time Period
Duration = now - StartTime
if Duration > SGSampleTime:
    TimePeriod = 2 #Sampling
elif Duration > BottleTime:
    TimePeriod = 3 #Bottling
else:
    TimePeriod = 1 #Fermenting
print('TimePeriod = '+str(TimePeriod))
print('TimeStamp = '+str(now))

# Prompt Time Actions

# Write the New DataLine to the local File (Time, id, Temperature, SP, TempBand, TimePeriod)
NewData = StartTime.strftime("%d/%m/%Y %H:%M:%S") + ", " + str(BrewID) + ", " + str(PV) + ", " + str(SP) + ", " + str(ControllerOP) + ", " + str(TimePeriod)
WritePreviousRecord(FilePath + 'LastReadings.csv',NewData,"w")

# Append the New DataLine to the sql database (Time, Temperature, SP, TempBand, TimePeriod)
with Sql.BrewingDatabase() as BrewData:
    BrewData.writeCurrentStatus(now, PV, ControllerOP, TimePeriod)