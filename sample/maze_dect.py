import cv2
import csv
import numpy as np
from picamera2 import Picamera2

def extract_maze_to_grid(img, maze_size, output_csv="maze_grid.csv"):
    """
    將傳入的影像轉換為 2D 陣列表格並儲存為 CSV
    """
    # 1. 判斷傳入的影像是否需要轉灰階 (避免重複轉換報錯)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 2. 進行二值化處理 (設定閾值 128，黑白反轉)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)

    height, width = thresh.shape
    cell_h = height // maze_size
    cell_w = width // maze_size
    maze_grid = np.zeros((maze_size, maze_size), dtype=int)

    # 3. 走訪網格取中心點平均值
    for row in range(maze_size):
        for col in range(maze_size):
            center_y = int((row * cell_h) + (cell_h / 2))
            center_x = int((col * cell_w) + (cell_w / 2))

            # 取中心 3x3 區域
            roi = thresh[max(0, center_y-1):min(height, center_y+2), 
                         max(0, center_x-1):min(width, center_x+2)]
            
            # 判斷牆壁(1)與通道(0)
            if np.mean(roi) > 127:
                maze_grid[row][col] = 1 
            else:
                maze_grid[row][col] = 0 

    # 4. 輸出與存檔
    print("\n--- 解析完成的迷宮陣列 ---")
    print(maze_grid)

    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(maze_grid)
    print(f"✅ 已成功將地圖儲存至 {output_csv}")

    return thresh, maze_grid # 回傳二值化圖片方便預覽

# ================= 主程式 =================

print("啟動相機中... (請將迷宮對準鏡頭，按下 's' 擷取，按下 'q' 離開)")

# 1. 初始化 Pi 5 相機
picam2 = Picamera2()
picam2.start()

try:
    while True:
        # 2. 持續抓取相機畫面
        frame = picam2.capture_array()
        
        # 3. 顯示即時預覽畫面，方便使用者對齊迷宮
        cv2.imshow("Maze Camera Preview", frame)

        # 4. 監聽鍵盤輸入
        key = cv2.waitKey(1) & 0xFF
        
        # 若按下 's' 鍵 (Save/Scan)，則進行迷宮解析
        if key == ord('s'):
            print("\n正在掃描迷宮...")
            # 傳入彩色 frame 進行解析，尺寸設為 8x8
            thresh_img, grid = extract_maze_to_grid(frame, maze_size=8, output_csv="maze.csv")

            # 顯示電腦看到的黑白二值化結果，用來確認有沒有誤判
            cv2.imshow("Threshold Result", thresh_img)
            
        # 若按下 'q' 鍵 (Quit)，則打破迴圈結束程式
        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("程式已手動中斷")

finally:
    # 5. 安全釋放資源
    picam2.stop()
    cv2.destroyAllWindows()
    print("相機已安全關閉")
