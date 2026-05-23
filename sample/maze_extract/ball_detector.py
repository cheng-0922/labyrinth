import cv2
import numpy as np


class BallDetector:
    """
    在 warped 迷宮影像中偵測 10mm 金屬鋼珠，回傳格子座標 (row, col)。

    設計假設：
    - 輸入是已透視校正的 warped 影像（迷宮填滿畫面）
    - 路徑寬 15mm，球徑 10mm → 球約佔格寬的 10/15 ≈ 67%
    - 金屬球特徵：有強烈高光亮點（亮白），整體比底板亮
    - 迷宮最大傾斜 20 度，球不會跑到牆壁 ROI 上
    """

    def __init__(self, maze_size=9, debug=False):
        self.maze_size = maze_size
        self.debug = debug

    def find_ball(self, warped_img):
        """
        在 warped_img 中偵測鋼珠。
        回傳 (row, col) 格子座標，若找不到回傳 None。
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size

        # 球在格子內的預期像素半徑範圍
        # 球徑 10mm / 格寬 15mm × cell_px / 2
        cell_px = min(cell_h, cell_w)
        r_min = int(cell_px * (10/15) / 2 * 0.6)   # 允許 40% 下浮（透視壓縮）
        r_max = int(cell_px * (10/15) / 2 * 1.3)   # 允許 30% 上浮

        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)

        # ── 高光遮罩：金屬球有強烈高光，亮度 > 200 ────────────────────────
        # 米色底板亮度約 150-180，金屬球高光 > 200，黑色牆頂 < 80
        _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # 去掉太小的高光（雜訊）和太大的區域（燈光反射）
        # 用形態學 open 消除孤立雜點
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_OPEN, kernel)
        # ────────────────────────────────────────────────────────────────────

        # ── Hough Circle 在高光遮罩上找圓 ──────────────────────────────────
        # 用 bright_mask 而非原圖，排除底板紋路干擾
        circles = cv2.HoughCircles(
            bright_mask,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=int(cell_px * 0.8),   # 同一格不會有兩個球
            param1=50,
            param2=10,                      # 低門檻：高光亮點輪廓不完整
            minRadius=r_min,
            maxRadius=r_max,
        )

        if circles is None:
            if self.debug:
                cv2.imshow("Debug: Ball Bright Mask", bright_mask)
            return None

        # 取最圓（param2 分數最高即第一個）的候選
        circles = np.round(circles[0]).astype(int)
        cx, cy, r = circles[0]

        # 座標轉格子
        col = int(cx / cell_w)
        row = int(cy / cell_h)

        # 邊界保護
        row = max(0, min(row, self.maze_size - 1))
        col = max(0, min(col, self.maze_size - 1))

        if self.debug:
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col})", (cx + 5, cy - 5),
                        cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Ball Bright Mask", bright_mask)
            cv2.imshow("Debug: Ball Detection", debug_img)

        return (row, col)
