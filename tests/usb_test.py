import serial
import time

port = serial.Serial('COM5', 115200, timeout=1)
time.sleep(2)  # wait for connection to settle

colour = "RED"  # change this to test each colour
port.write((colour + '\n').encode())
print(f"Sent: {colour}")

port.close()