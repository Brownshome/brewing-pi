import os
import csv
from pathlib import Path
import RPi.GPIO as GPIO
from datetime import datetime
from datetime import timedelta

# Variable Declarations
#FilePath ='C:\\Users\\Martin\\Documents\\Python Stuff\\'
FilePath = str(Path.home()) + '/brew/'
RedGP = 14
GrnGP = 15
BluGP = 18
TIGP = 2
HtrGP = 3
ClrGP = 4

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
with open(FilePath + 'ThisBatch.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        SGSamplesec = float(row[2]) * 86400
        print('SGSamplesec = '+str(SGSamplesec))
        BottleTime = float(row[3]) * 86400
        print('BottleTime = '+str(BottleTime))
        StartTime = datetime.strptime(row[1], "%d/%m/%Y %H:%M:%S")
        print('StartTime = '+str(StartTime))
        SP = float(row[4])
        print('SP = '+str(SP))
        dbHigh = float(row[5])
        print('dbHigh = '+str(dbHigh))
        dbLow = float(row[6])
        print('dbLow = '+str(dbLow))
        HighDevTP = float(row[7])
        print('HighDevTP = '+str(HighDevTP))
        LowDevTP = float(row[8])
        print('LowDevTP = '+str(LowDevTP))
with open(FilePath + 'LastReadings.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        OldOP = int(row[3])
        print('OldOP = '+str(OldOP))
        OldTP = int(row[4])
        print('OldTP = '+str(OldTP))

# Read Previous Record from file (Time, Temperature, SP, TempBand, TimePeriod)
#LastData = ReadPreviousRecord('C:\\Users\\Martin\\Documents\\Python Stuff\\LastReadings.CSV')
#SP = LastData[3]

# Read Current Temperature
PV = getCPUtemp()
print('PV = '+str(PV))

#PV = float(input("what's the temp man? "))

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

# Setup IO
# GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TIGP,GPIO.IN) # TI
GPIO.setup(HtrGP,GPIO.OUT) # Heating
GPIO.setup(ClrGP,GPIO.OUT) # Cooling
GPIO.setup(RedGP,GPIO.OUT) # Red LED
GPIO.setup(GrnGP,GPIO.OUT) # Green LED
GPIO.setup(BluGP,GPIO.OUT) # Blue LED

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
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
TimePeriod = 1 #Fermenting
Duration = now - StartTime
if Duration.seconds > SGSamplesec:
    TimePeriod = 2 #Sampling
elif Duration.seconds > BottleTime:
    TimePeriod = 3 #Bottling
print('TimePeriod = '+str(TimePeriod))

# Prompt Time Actions
# Append the  New DataLine to File (Time, Temperature, SP, TempBand, TimePeriod)
NewData = dt_string + ", " + str(PV) + ", " + str(SP) + ", " + str(ControllerOP) + ", " + str(TimePeriod)
WritePreviousRecord(FilePath + 'LastReadings.csv',NewData,"w")
WritePreviousRecord(FilePath + 'AllReadings.csv',"\n"+NewData,"a")
