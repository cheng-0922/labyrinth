import serial
import time

class MazeController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.arduino = None
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            print(f"🔌 成功連接 Arduino 控制板 ({port})!")
        except Exception as e:
            print(f"⚠️ 找不到 Arduino 控制板，進入【純軟體模擬模式】。({e})")

    def tilt_and_stop(self, direction_code, tilt_time=0.4):
        cmd_map = {1: b'N', 2: b'S', 3: b'W', 4: b'E'}
        cmd = cmd_map.get(direction_code)

        if not cmd:
            return

        direction_names = {1: "北", 2: "南", 3: "西", 4: "東"}
        print(f"⚙️ 馬達作動：向 {direction_names[direction_code]} 傾斜...")

        if self.arduino:
            self.arduino.write(cmd)
            self.arduino.flush()  # 確保指令立刻推送到 Arduino
        
        time.sleep(tilt_time) 
        
        print("🛑 煞車打平！")
        if self.arduino:
            self.arduino.write(b'C')
            self.arduino.flush()
        
        time.sleep(0.5) 

    def cleanup(self):
        if self.arduino:
            self.arduino.write(b'C')
            self.arduino.flush()
            self.arduino.close()
            print("🔌 Arduino 已安全斷線。")