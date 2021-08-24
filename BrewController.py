import os
import csv
#import RPi.GPIO as GPIO
from datetime import datetime
from datetime import timedelta

# Variable Declarations

# Function Declarations
def WritePreviousRecord(FileName, DataStr, TypeStr):
    file = open(FileName, TypeStr)
    file.write(DataStr)
    file.close()
#def ReadPreviousRecord(FileName):
#    with open(FileName) as csvfile:
#        csvreader = csv.reader(csvfile, delimiter=',')
#        for row in csvreader:
#            csvrow = .join(row)
#    return csvrow
def getCPUtemp():
    cTemp = os.popen('vcgencmd measure_temp').readline()
    return float(cTemp.replace("temp=","").replace("'C\n",""))

# Read Brew Data from File (Name, StartTime, SGSampleTime (days), BottleTime (days), InitialSP, dbHigh, dbLow, HighDevTP, LowDevTP)
# If this File is not Found, run NewBatch.py to Start a new brew
#BatchData = ReadPreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\ThisBatch.CSV')
with open('C:\\Users\\Martin\\Documents\\Python Stuff\\ThisBatch.CSV') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        SGSamplesec = float(row[2]) * 86400
        BottleTime = float(row[3]) * 86400
        StartTime = datetime.strptime(row[1], "%d/%m/%Y %H:%M:%S")
        SP = float(row[4])
        dbHigh = float(row[5])
        dbLow = float(row[6])
        HighDevTP = float(row[7])
        LowDevTP = float(row[8])
with open('C:\\Users\\Martin\\Documents\\Python Stuff\\LastReadings.CSV') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        OldOP = int(row[3])
        OldTP = int(row[4])

# Read Previous Record from file (Time, Temperature, SP, TempBand, TimePeriod)
#LastData = ReadPreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\LastReadings.CSV')
#SP = LastData[3]

# Read Current Temperature
#PV = getCPUtemp()
PV = float(input("what's the temp man? "))

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

# Drive LEDS
# Drive Heater / Cooler Outputs
# Determine Current Time Period
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
TimePeriod = 1 #Fermenting
Duration = now - StartTime
if Duration.seconds > SGSamplesec:
    TimePeriod = 2 #Sampling
elif Duration.seconds > BottleTime:
    TimePeriod = 3 #Bottling
    
# Prompt Time Actions
# Append the  New DataLine to File (Time, Temperature, SP, TempBand, TimePeriod)
NewData = dt_string + ", " + str(PV) + ", " + str(SP) + ", " + str(ControllerOP) + ", " + str(TimePeriod)
WritePreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\LastReadings.CSV',NewData,"w")
WritePreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\AllReadings.CSV',"\n"+NewData,"a")