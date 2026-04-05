import serial
import time

bt = serial.Serial('COM5', 115200, timeout=1)  # replace COM5 with your port
time.sleep(2)  # wait for connection

bt.write(b'RED\n')
print("Sent: RED")
bt.close()