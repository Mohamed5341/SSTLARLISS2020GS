# this code prints available data came from serial to terminal
import serial
import serial.tools.list_ports_linux as ports


#list of connected devices
lis = ports.comports()

#connect to device
device = serial.Serial(lis[0].device)


while True:# the program is always running
    while device.in_waiting:# check if available data
        print(device.readline().decode("utf-8"))


