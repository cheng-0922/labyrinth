import cv2
from picamera2 import Picamera2

# 1. 初始化 Pi 5 的新版相機介面
picam2 = Picamera2()
# 設定預覽解析度 (降低解析度可以大幅提升 AI 辨識的幀率)
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# 2. 載入 OpenCV 內建的人臉辨識模型 (Haar Cascade)
# 這是一個輕量級的模型，不需要 AI 加速卡也能在 Pi 5 CPU 上順暢執行
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

print("相機已啟動，請看向鏡頭！(在影像視窗按下 'q' 鍵退出)")

try:
    while True:
        # 3. 從相機抓取一張影像轉換為陣列
        frame = picam2.capture_array()
        
        # 將彩色影像轉為灰階，減少運算量
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 4. 進行人臉偵測
        # 回傳的 faces 會包含所有人臉的座標 (x, y) 與寬高 (w, h)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # 5. 在畫面上畫出綠色方框標示人臉
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, 'Face Detected!', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # 顯示影像畫面
        cv2.imshow('Pi 5 Face Detection Demo', frame)

        # 偵測鍵盤輸入，按下 'q' 鍵打破迴圈
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("程式已手動中斷")

finally:
    # 6. 安全關閉相機與視窗
    picam2.stop()
    cv2.destroyAllWindows()
    print("相機已安全關閉")