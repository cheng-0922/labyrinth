import cv2
import numpy as np

def convert_to_mdf_maze(input_img_path="maze_tem.png", output_path="test_maze.jpg"):
    print(f"🎨 正在讀取網站迷宮 {input_img_path} 並進行木板化...")
    
    maze_img = cv2.imread(input_img_path, cv2.IMREAD_GRAYSCALE)
    if maze_img is None:
        print(f"❌ 找不到圖片 {input_img_path}")
        return

    _, thresh = cv2.threshold(maze_img, 127, 255, cv2.THRESH_BINARY_INV)

    width, height = 800, 800
    base_color = (140, 180, 210) 
    mdf = np.full((height, width, 3), base_color, dtype=np.uint8)
    
    noise = np.random.randint(-20, 20, (height, width, 3), dtype=np.int16)
    mdf = np.clip(mdf + noise, 0, 255).astype(np.uint8)

    pad = 120 
    maze_roi_size = width - 2*pad
    resized_maze = cv2.resize(thresh, (maze_roi_size, maze_roi_size), interpolation=cv2.INTER_NEAREST)

    wall_color = (30, 30, 30)
    roi = mdf[pad:height-pad, pad:width-pad]
    roi[resized_maze == 255] = wall_color
    mdf[pad:height-pad, pad:width-pad] = roi

    # ==========================================
    # 【更新邏輯】：4 個紅色定位點正中心精準對齊頂點
    # ==========================================
    red_color = (0, 0, 220)
    marker_radius = 15 # 半徑 25 小於單一網格的大小 (70)，因此紅點不會跨界干擾到通道
    
    # 直接畫在 (pad, pad) 也就是迷宮框線的正角落！
    cv2.circle(mdf, (pad, pad), marker_radius, red_color, -1)
    cv2.circle(mdf, (width - pad, pad), marker_radius, red_color, -1)
    cv2.circle(mdf, (width - pad, height - pad), marker_radius, red_color, -1)
    cv2.circle(mdf, (pad, height - pad), marker_radius, red_color, -1)

    # 透視變形與輸出 (保持不變)
    final_canvas = np.full((1000, 1000, 3), (220, 220, 220), dtype=np.uint8)
    pts_original = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    pts_warped = np.float32([[150, 100], [900, 180], [850, 900], [100, 850]])
    
    M = cv2.getPerspectiveTransform(pts_original, pts_warped)
    warped_maze = cv2.warpPerspective(mdf, M, (1000, 1000), borderMode=cv2.BORDER_TRANSPARENT)
    
    mask = np.any(warped_maze > 0, axis=-1)
    final_canvas[mask] = warped_maze[mask]

    cv2.imwrite(output_path, final_canvas)
    print(f"✅ 成功生成精準對齊版測試圖：{output_path}")

if __name__ == "__main__":
    convert_to_mdf_maze()