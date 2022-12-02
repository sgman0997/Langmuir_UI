#!/usr/bin/env python3
import serial
import time

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)
    ser.reset_input_buffer()
    
    while True:
        ser.reset_input_buffer()
        while ser.in_waiting < 8:
            pass
        line = ser.readline().decode("utf-8").strip().split()
        print(line)