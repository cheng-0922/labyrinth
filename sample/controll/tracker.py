import cv2
import time

class MarbleTracker:
    def __init__(self, target_width=320, target_height=240):
        self.resolution = (target_width, target_height)
        self.bg_gray = None

    def capture_background(self, picam2):
        print("🎥 準備擷取基準背景... 請確保迷宮上【沒有】彈珠！")
        time.sleep(2)  
        
        try:
            metadata = picam2.capture_metadata()
            exposure_time = metadata.get('ExposureTime')
            analogue_gain = metadata.get('AnalogueGain')
            
            if exposure_time and analogue_gain:
                picam2.set_controls({
                    "AeEnable": False, 
                    "ExposureTime": exposure_time, 
                    "AnalogueGain": analogue_gain,
                    "AwbEnable": False 
                })
                picam2.capture_array() # 消耗掉過渡幀
                print("🔒 相機自動曝光與白平衡已成功鎖定！")
        except Exception as e:
            print(f"⚠️ 警告：相機曝光鎖定失敗 ({e})")

        raw_frame = picam2.capture_array()
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
        frame_resized = cv2.resize(frame, self.resolution)
        
        self.bg_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        self.bg_gray = cv2.GaussianBlur(self.bg_gray, (11, 11), 0)
        print("✅ 基準背景建立完成！")

    def detect(self, picam2):
        if self.bg_gray is None:
            return None, None, None

        raw_frame = picam2.capture_array()
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
        frame_resized = cv2.resize(frame, self.resolution)
        
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        
        diff = cv2.absdiff(self.bg_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 50:
                (x, y), radius = cv2.minEnclosingCircle(largest_contour)
                return int(x), int(y), frame_resized
                
        return None, None, frame_resized