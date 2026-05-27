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

        實測 HSV：
          球  RGB(110,130,90)  → H≈90, S≈30, V≈130
          底板 RGB(190,170,160) → H≈20, S≈30, V≈190
          牆頂 黑色             → V<120
        策略：用色相 H 分離球（H:75-105）與底板（H:10-35）
        再用輪廓圓形度確認形狀
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        cell_px = min(cell_h, cell_w)

        r_expected = cell_px * (10/15) / 2
        area_min = np.pi * (r_expected * 0.5) ** 2
        area_max = np.pi * (r_expected * 1.4) ** 2

        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)

        # ── Step 1：HSV 色相遮罩，球 H≈90 與底板 H≈20 相差 70 ──────────────
        # S 下限設低（15）因為球飽和度不高，但仍需排除 S≈0 的純黑/白
        ball_mask = cv2.inRange(hsv,
                                np.array([65, 5, 60]),
                                np.array([115, 120, 200]))
        # ────────────────────────────────────────────────────────────────────

        # ── Step 2：形態學，填補球遮罩內的破洞 ──────────────────────────────
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        ball_mask = cv2.morphologyEx(ball_mask, cv2.MORPH_CLOSE, kernel)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 3：輪廓 + 圓形度過濾 ────────────────────────────────────────
        contours, _ = cv2.findContours(ball_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_circularity = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < area_min or area > area_max:
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue

            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < 0.5:
                continue

            if circularity > best_circularity:
                best_circularity = circularity
                M = cv2.moments(cnt)
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                best = (cx, cy)
        # ────────────────────────────────────────────────────────────────────

        if best is None:
            if self.debug:
                cv2.imshow("Debug: Ball HSV Mask", ball_mask)
            return None

        cx, cy = best
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))

        if self.debug:
            r_draw = int(r_expected)
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), r_draw, (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col}) c={best_circularity:.2f}",
                        (cx + 5, cy - 5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Ball HSV Mask", ball_mask)
            cv2.imshow("Debug: Ball Detection", debug_img)

        return (row, col)
