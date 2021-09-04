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
    if LEDColour == 'Alarm':
        GPIO.output(RedGP,1)
        GPIO.output(GrnGP,1)
        GPIO.output(BluGP,1)
    if LEDColour == 'Off':
        GPIO.output(RedGP,0)
        GPIO.output(GrnGP,0)
        GPIO.output(BluGP,0)
    if __name__ == "__main__":
        print("LEDs set to " + LEDColour)


def SetOP(ContrlMode):
    if ContrlMode == 'Heat':
        GPIO.output(HtrGP,0)
        GPIO.output(ClrGP,1)
    elif ContrlMode == 'Cool':
        GPIO.output(HtrGP,1)
        GPIO.output(ClrGP,0)
    else:
        GPIO.output(HtrGP,1)
        GPIO.output(ClrGP,1)
    if __name__ == "__main__":
        print("Controller set to " + ContrlMode)

# Read Previous Record from local file (StartTime, id, Temperature, SP, TempBand, TimePeriod)
try:
    with open(FilePath + 'LastReadings.csv') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            OldID = int(row[1])
            if OldID > 0:
                OldST = datetime.strptime(row[0],"%d/%m/%Y %H:%M:%S")
                OldSP = float(row[3])
                OldOP = int(row[4])
                OldTP = int(row[5])
                Old_HighDevTP = float(row[6])
                Old_dbHigh = float(row[7])
                Old_dbLow = float(row[8])
                Old_LowDevTP = float(row[9])
            if __name__ == "__main__":
                print('OldID = '+str(OldID))
                if OldID > 0:
                    print('OldST = '+str(OldST))
                    print('OldSP = '+str(OldSP))
                    print('OldOP = '+str(OldOP))
                    print('OldTP = '+str(OldTP))
                    print('Old_dbHigh = '+str(Old_dbHigh))
                    print('Old_dbLow = '+str(Old_dbLow))
                    print('Old_HighDevTP = '+str(Old_HighDevTP))
                    print('Old_LowDevTP = '+str(Old_LowDevTP))

except FileNotFoundError: # Turn off control
    OldID = 0
    OldOP = 0
    if __name__ == "__main__":
        print('Local record not read')
        print('OldID = '+str(OldID))

# Read Brew Data from File (id, brew_name, start_time, sg_sample_time, bottle_time, set_point, deadband_high, deadband_low, high_trip_point, low_trip_point)
try:
    with Sql.BrewingDatabase() as BrewData:
        noSql = False
        if not BrewData.isBrewRunning(): # no brew running so dont control
            NewData = ", " + str(0) + ", , , ,"
            WritePreviousRecord(FilePath + 'LastReadings.csv',NewData,"w")
            ControllerOP = 0
            SetOP('None')
            SetLED('Off')
            if __name__ == "__main__":
                print('SQL read OK, no brew running, exiting')
            exit()
        BrewID = int(BrewData.BrewID())
        SGSampleTime = BrewData.sg_sample_time()
        BottleTime = BrewData.bottle_time()
        StartTime = BrewData.start_time()
        SP = float(BrewData.setpoint())
        dbHigh = float(BrewData.deadband_high())
        dbLow = float(BrewData.deadband_low())
        HighDevTP = float(BrewData.high_trip_point())
        LowDevTP = float(BrewData.low_trip_point())
        if __name__ == "__main__":
            print('ID = '+str(BrewID))
            print('SGSamplesec = '+str(SGSampleTime))
            print('BottleTime = '+str(BottleTime))
            print('StartTime = '+str(StartTime))
            print('SP = '+str(SP))
            print('dbHigh = '+str(dbHigh))
            print('dbLow = '+str(dbLow))
            print('HighDevTP = '+str(HighDevTP))
            print('LowDevTP = '+str(LowDevTP))
except RuntimeError as err: # If sql data is not available, substitute local values
    if OldID == 0: 
        if __name__ == "__main__":
            SetLED('Alarm')
            SetOP('None')
            print('SQL not read, and no local record, exiting')
            exit
    BrewID = OldID
    SP = OldSP
    StartTime = OldST
    TimePeriod = OldTP
    HighDevTP = Old_HighDevTP
    dbHigh = Old_dbHigh
    dbLow = Old_dbLow
    LowDevTP = Old_LowDevTP
    noSql = True
    if __name__ == "__main__":
        print('SQL not read, using local record')

# Read Current Temperature
TISensor = TemperatureSensor.TemperatureSensor()
PV = TISensor.readTemperature()
if __name__ == "__main__":
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
if __name__ == "__main__":
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
if not noSql:
    Duration = now - StartTime
    if Duration > SGSampleTime:
        TimePeriod = 2 #Sampling
    elif Duration > BottleTime:
        TimePeriod = 3 #Bottling
    else:
        TimePeriod = 1 #Fermenting
if __name__ == "__main__":
    print('TimePeriod = '+str(TimePeriod))
    print('TimeStamp = '+str(now))

# Write the New DataLine to the local File (Time, id, Temperature, SP, TempBand, TimePeriod)
NewData = StartTime.strftime("%d/%m/%Y %H:%M:%S")
NewData = NewData + ", " + str(BrewID) + ", " + str(PV) + ", " + str(SP)
NewData = NewData + ", " + str(ControllerOP) + ", " + str(TimePeriod)
NewData = NewData + ", " + str(HighDevTP) + ", " + str(dbHigh) + ", " + str(dbLow) + ", " + str(LowDevTP)
WritePreviousRecord(FilePath + 'LastReadings.csv',NewData,"w")

if __name__ == "__main__":
    exit

# Append the New DataLine to the sql database (Time, Temperature, SP, TempBand, TimePeriod)
with Sql.BrewingDatabase() as BrewData:
    BrewData.writeCurrentStatus(now, PV, ControllerOP, TimePeriod)
