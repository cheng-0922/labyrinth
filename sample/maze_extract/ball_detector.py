import cv2
import numpy as np
Lthres = 200

 
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
 
        實測數值：
          球中心高光 L≈250，底板 L≈160-210，牆頂 L≈90-110
        策略：
          1. 灰階閾值 230 → 只有球中心高光通過（底板最亮 210 < 230）
          2. 找輪廓 → 用圓形度 (4π·A/P²) 過濾，球是圓形，亮斑是不規則形
          3. 用面積範圍過濾（球的預期像素面積）
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        cell_px = min(cell_h, cell_w)
 
        # 球的預期半徑：10mm / 15mm × cell_px / 2
        r_expected = cell_px * (10/15) / 2
        area_min = np.pi * (r_expected * 0.5) ** 2   # 允許 50% 下浮
        area_max = np.pi * (r_expected * 1.4) ** 2   # 允許 40% 上浮
 
        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
 
        # ── Step 1：高光閾值，球中心 L≈250，底板最亮 L≈210，門檻設 230 ────────
        _, bright = cv2.threshold(gray, Lthres, 255, cv2.THRESH_BINARY)
        # ────────────────────────────────────────────────────────────────────
 
        # ── Step 2：輪廓 + 圓形度過濾 ────────────────────────────────────────
        contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
        best = None          # (cx, cy, area)
        best_circularity = 0
 
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < area_min or area > area_max:
                continue     # 面積不符
 
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
 
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < 0.6:
                continue     # 不夠圓（底板亮斑通常 < 0.4）
 
            if circularity > best_circularity:
                best_circularity = circularity
                M = cv2.moments(cnt)
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                best = (cx, cy, area)
        # ────────────────────────────────────────────────────────────────────
 
        if best is None:
            if self.debug:
                cv2.imshow("Debug: Ball Bright (thr=230)", bright)
            return None
 
        cx, cy, _ = best
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))
 
        if self.debug:
            r_draw = int(r_expected)
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), r_draw, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col}) c={best_circularity:.2f}",
                        (cx + 5, cy - 5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Ball Bright (thr=230)", bright)
            cv2.imshow("Debug: Ball Detection", debug_img)
 
        return (row, col)
