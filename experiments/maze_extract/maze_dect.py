import cv2
import csv
import numpy as np
from picamera2 import Picamera2

def extract_maze_to_grid(img, maze_size, output_csv="maze_grid.csv"):
    """
    使用邊緣與直線偵測，將影像轉換為 2D 陣列表格並儲存為 CSV
    """
    # 1. 轉灰階並模糊化去噪 (有助於後續的邊緣偵測)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Canny 邊緣偵測 (抓取所有輪廓)
    # 參數 50, 150 是雙閾值，可依據現場光線微調
    edges = cv2.Canny(blurred, 50, 150)

    # 3. 霍夫直線轉換 (Hough Line Transform) - 強化並過濾真正的直線
    height, width = edges.shape
    # 建立一個全黑的遮罩，用來畫出系統認定的「乾淨直線」
    clean_lines_mask = np.zeros((height, width), dtype=np.uint8)

    # 調整這些參數來適應你的迷宮：
    # threshold: 認定為直線的最低票數 (越低越敏感)
    # minLineLength: 線段的最短長度 (過濾掉短的雜訊)
    # maxLineGap: 允許線段中間斷裂的最大距離 (把斷掉的線接起來)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=15, maxLineGap=10)

    # 將偵測到的直線畫到全黑的遮罩上
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 用白線 (255) 畫出牆壁，粗度設為 3 確保佔有一定面積
            cv2.line(clean_lines_mask, (x1, y1), (x2, y2), 255, 3)

    # 4. 根據「乾淨的線條遮罩」切分網格
    cell_h = height // maze_size
    cell_w = width // maze_size
    maze_grid = np.zeros((maze_size, maze_size), dtype=int)

    # 5. 走訪網格 (這次檢查整個格子，而不是只看中心點)
    for row in range(maze_size):
        for col in range(maze_size):
            y1 = row * cell_h
            y2 = (row + 1) * cell_h
            x1 = col * cell_w
            x2 = (col + 1) * cell_w

            # 取出該格子的所有像素
            cell_roi = clean_lines_mask[y1:y2, x1:x2]

            # 計算該格子內「白線」(牆壁)的像素總量
            white_area = cv2.countNonZero(cell_roi)
            cell_area = cell_h * cell_w

            # 若該格子內線條的面積佔了超過一定比例 (例如 5%)，就視為牆壁
            # 這個 0.05 (5%) 可依據你希望的靈敏度調整
            if (white_area / cell_area) > 0.05:
                maze_grid[row][col] = 1 
            else:
                maze_grid[row][col] = 0 

    # 6. 輸出與存檔
    print("\n--- 解析完成的迷宮陣列 ---")
    print(maze_grid)

    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(maze_grid)
    print(f"✅ 已成功將地圖儲存至 {output_csv}")

    # 回傳只剩下「乾淨直線」的圖片，你在 cv2.imshow 預覽時會非常清楚看到電腦抓到哪裡
    return clean_lines_mask, maze_grid

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
            thresh_img, grid = extract_maze_to_grid(frame, maze_size=30, output_csv="maze.csv")

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
