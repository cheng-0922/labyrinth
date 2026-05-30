
import serial
import time

PORT = "/dev/ttyACM0"   # Arduino USB 預設；若找不到改成 /dev/ttyACM1
BAUD = 9600

class ArduinoSerial:
    def __init__ (self, port, baud= 9600):
        try:
            self.ser = serial.Serial(port, baud , timeout=0)
        except serial.SerialException as e:
            print(f"❌ 無法開啟序列埠：{e}")
            print("請確認 Arduino 已接上 USB，並執行：ls /dev/ttyACM*")

    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode()

        self.ser.write(msg)

    def send_line(self, msg):
        if isinstance(msg, str):
            msg = (msg + "\n").encode()

        self.ser.write(msg)

    def read(self):
        if self.ser.in_waiting:

            try:
                return (
                    self.ser.readline()
                    .decode("utf-8", errors="replace")
                    .strip()
                )

            except Exception:
                return None

        return None

    def close(self):
        self.ser.close()

