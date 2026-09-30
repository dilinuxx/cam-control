"""


"""

import serial

# CONSTANTS
serial_port = serial.Serial(port="COM1")
serial_port.baudrate = 115200
serial_port.timeout = 1

if __name__ == "__main__":

    msg = "Hello World"
    serial_port.write(bytearray(msg, 'ascii'))

    print("Success!!")
