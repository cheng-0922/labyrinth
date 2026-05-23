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
        在 warped_img 中偵測鋼珠，回傳 (row, col)，找不到回傳 None。

        策略：金屬球特徵是「中央亮、周圍有深色陰影環」，形成明顯圓形梯度。
        直接對灰階圖跑 HoughCircles（不做亮度遮罩），保留邊緣梯度資訊。
        用 HSV 排除遮罩去掉底板米色亮斑和綠色定位點的干擾區域。
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        cell_px = min(cell_h, cell_w)

        # 球的預期半徑範圍：10mm / 15mm × cell_px / 2，允許 ±35%
        r_min = int(cell_px * (10/15) / 2 * 0.65)
        r_max = int(cell_px * (10/15) / 2 * 1.35)

        # ── Step 1：建立排除遮罩，把底板亮斑和綠點塗黑 ──────────────────────
        # 底板米色：H≈15-35, S≈15-55, V>150 → 排除（大片不規則亮區）
        # 綠色定位點：H≈75-95 → 排除
        # 金屬球灰色：S<50, V 中等，不在排除範圍內
        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
        floor_mask  = cv2.inRange(hsv, np.array([15,  15, 160]), np.array([35,  55, 255]))
        green_mask  = cv2.inRange(hsv, np.array([75, 100, 100]), np.array([95, 255, 255]))
        exclude_mask = cv2.bitwise_or(floor_mask, green_mask)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 2：灰階 + Gaussian Blur，保留圓形梯度 ───────────────────────
        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
        # 排除區域填為底板平均灰度（~160），讓 Hough 不在那裡找邊緣
        gray[exclude_mask > 0] = 160
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 3：HoughCircles 直接找「中亮邊深」的圓 ──────────────────────
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=int(cell_px * 0.8),  # 同一格不會有兩個球
            param1=60,   # Canny 高門檻：只抓強梯度（牆角陰影環）
            param2=25,   # 累積門檻：需要夠多邊緣點在圓上才算數
            minRadius=r_min,
            maxRadius=r_max,
        )
        # ────────────────────────────────────────────────────────────────────

        if circles is None:
            if self.debug:
                cv2.imshow("Debug: Ball Gray (excluded)", gray)
            return None

        circles = np.round(circles[0]).astype(int)

        # ── Step 4：從候選圓中選「中心最亮」的那個（球中心 > 底板平均）────────
        best = None
        best_brightness = -1
        for cx, cy, r in circles:
            # 只取圓心附近 3×3 的平均亮度
            y1 = max(cy - 3, 0); y2 = min(cy + 3, h)
            x1 = max(cx - 3, 0); x2 = min(cx + 3, w)
            center_brightness = float(np.mean(gray[y1:y2, x1:x2]))
            if center_brightness > best_brightness:
                best_brightness = center_brightness
                best = (cx, cy, r)
        # ────────────────────────────────────────────────────────────────────

        if best is None:
            return None

        cx, cy, r = best
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))

        if self.debug:
            debug_img = warped_img.copy()
            # 畫出所有候選（藍色）
            for ccx, ccy, cr in circles:
                cv2.circle(debug_img, (ccx, ccy), cr, (255, 100, 0), 1)
            # 畫出選中的球（綠色）
            cv2.circle(debug_img, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col})", (cx + 5, cy - 5),
                        cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Ball Gray (excluded)", gray)
            cv2.imshow("Debug: Ball Detection", debug_img)

        return (row, col)