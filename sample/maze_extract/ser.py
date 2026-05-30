
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
    ser.write(b'r')
    time.sleep(3)
    while True:
        response = ser.readline().decode("utf-8", errors = "replace").strip()
        if response :
            print (response)
        cmd = input("command : (s-auto atart, r-reset, j- play in joystick, q:quit")
        if len(cmd)==1:
            ser.write(b'{cmd}')
        
        



if __name__ == "__main__":
    main()
