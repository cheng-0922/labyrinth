
import serial
import time

PORT = "/dev/ttyACM0"   # Arduino USB 預設；若找不到改成 /dev/ttyACM1
BAUD = 9600

def main():
    print(f"開啟 {PORT} @ {BAUD} baud ...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=3)
    except serial.SerialException as e:
        print(f"❌ 無法開啟序列埠：{e}")
        print("請確認 Arduino 已接上 USB，並執行：ls /dev/ttyACM*")
        return

    # Arduino reset 後需要約 2 秒才準備好接收
    time.sleep(2)
    ser.reset_input_buffer()

    print("送出：PING")
    ser.write(b"PING\n")

    response = ser.readline().decode("utf-8", errors="replace").strip()
    if response == "PONG":
        print("✅ 通訊成功！收到：PONG")
    else:
        print(f"❌ 收到非預期回應：'{response}'")
        print("請確認 Arduino 已燒錄 arduino_serial_test.ino")

    ser.close()

if __name__ == "__main__":
    main()
