#-------------------------------------------------------------------#
#               Bike lock/unlocker
#
# Raspberry Pi reads RFID input and determines access rights
#
# If correct RFID received (currently hardcoded to blue dongle with 
# number 04:BA:1E:8A:FE:16:90), RPi sends unlock/lock signal to 
# VEX IQ which operates motor and lights TouchLED either green 
# (unlocking) or red(locking)
#
# Run this program on RPi and main.py on VEX IQ
#
# Authors: Core Electronics (sample code) & Rob Poulter (serial comms)
# Modification for task: Sharon Harrison
# March 1st 2024
#-------------------------------------------------------------------#


import platform
import serial
import time
from PiicoDev_RFID import PiicoDev_RFID
from PiicoDev_Unified import sleep_ms

SERIAL_DEVICE_MACOS = "/dev/tty.usbmodem1103"
SERIAL_DEVICE_WIN = "COM7"
SERIAL_DEVICE_LINUX = "/dev/ttyACM1"

SYSTEM = platform.system()  # 'Darwin', 'Linux', 'Windows'
if SYSTEM == "Darwin":
    PORT_NAME = SERIAL_DEVICE_MACOS
elif SYSTEM == "Linux":
    PORT_NAME = SERIAL_DEVICE_LINUX
elif SYSTEM == "Windows":
    PORT_NAME = SERIAL_DEVICE_WIN

serial_port_file = serial.Serial(
    PORT_NAME,
    115200,
    timeout=0,
    write_timeout=0,
    inter_byte_timeout=None,
)  

def send_msg(serial_port, msg):
    try:
        line = msg
        serial_port.write(f"M:{line}:E\n".encode())
        serial_port.flush()
    except:
        pass


def read_serial(serial_port):
    try:
        data = serial_port.read(1024)
        if data:
            print(data.decode(), end='')
    except:
        pass


rfid = PiicoDev_RFID()

# A list of authorised users
authorised_users = ['04:BA:1E:8A:FE:16:90', '04:65:6C:FA:3F:74:81','04:D0:80:FA:3F:74:80', '04:C5:AE:8A:FE:16:90','04:BA:1E:8A:FE:15:90', '04:87:7F:42:E8:14:91'] 


def get_vals():
    command = "lock"
    allow = ""
    while True:        
        if rfid.tagPresent():    # if an RFID tag is present
            id = rfid.readID()   # get the id
            print(id)            # print the id
            if id in authorised_users:  # check if the tag is in the authorised-user list
                print('Access Granted!\n')
                allow = "true"
                if command == "unlock":
                    command = "lock"
                elif command == "lock":
                    command = "unlock" 
            else:
                print('Access denied!\n')
                allow = "false"  
        # send values to the VEX brain
        packet = str((command) + "," + str(allow))
        send_msg(serial_port_file, packet)
        print(packet) # this can be removed once you are confident it is working
        # give IQ time to be updated and respond with motor movement
        sleep_ms(2000)
        allow = ""
        id = ""

get_vals()