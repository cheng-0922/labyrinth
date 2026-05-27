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
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        cell_px = min(cell_h, cell_w)

        r_expected = cell_px * (10 / 15) / 2
        # 稍微放寬面積範圍，避免球體破碎時被過濾掉
        area_min = np.pi * (r_expected * 0.4) ** 2
        area_max = np.pi * (r_expected * 1.6) ** 2

        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)

        # ── Step 1：雙重 Mask (基礎身形 + 高光防偽) ───────────────────────────
        # 1. 抓取鋼珠本體的 Mask（放寬 V 範圍，也會抓到一些暗色牆壁）
        ball_mask = cv2.inRange(hsv,
                                np.array([0,  0,  40]),
                                np.array([180, 40, 180]))
        
        # 2. 抓取金屬高光的 Mask（只抓極亮的點，用來過濾純黑牆壁）
        light_mask = cv2.inRange(hsv,
                                 np.array([0,  0,  190]), 
                                 np.array([180, 40, 255]))
        # ────────────────────────────────────────────────────────────────────

        # ── Step 2：CLOSE 先把鄰近碎片黏合，再找輪廓 ─────────────────────────
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        ball_mask = cv2.morphologyEx(ball_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(ball_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 3：形狀過濾 + 高光驗證 ───────────────────────────────────────
        best = None
        best_circularity = 0

        for cnt in contours:
            # 1. 取得邊界框與長寬比過濾 (秒殺細長形狀的牆頂與牆角)
            x, y, w_box, h_box = cv2.boundingRect(cnt)
            aspect_ratio = float(w_box) / h_box
            if aspect_ratio < 0.6 or aspect_ratio > 1.6:
                continue

            # 2. 凸包面積過濾
            hull = cv2.convexHull(cnt)
            area = cv2.contourArea(hull)
            if area < area_min or area > area_max:
                continue

            # 3. 金屬高光驗證 (秒殺大面積的純黑陰影/牆壁)
            # 在這個輪廓的範圍內，如果連1個極亮的高光像素都沒有，就判定為假 (牆壁)
            roi_light = light_mask[y:y+h_box, x:x+w_box]
            if cv2.countNonZero(roi_light) < 1:
                continue

            # 4. 圓形度過濾 (稍微調低標準到 0.5，因為高光和長寬比已經幫忙擋掉雜訊了)
            perimeter = cv2.arcLength(hull, True)
            if perimeter == 0:
                continue

            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < 0.5:
                continue

            # 更新最佳候選
            if circularity > best_circularity:
                best_circularity = circularity
                M = cv2.moments(hull)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                best = (cx, cy)
        # ────────────────────────────────────────────────────────────────────

        if best is None:
            if self.debug:
                cv2.imshow("Debug: Ball Mask", ball_mask)
                # 新增高光 Debug，方便你觀察現場燈光夠不夠亮
                cv2.imshow("Debug: Light Mask", light_mask) 
            return None

        cx, cy = best
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))

        if self.debug:
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), int(r_expected), (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col}) c={best_circularity:.2f}",
                        (cx + 5, cy - 5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Ball Mask", ball_mask)
            cv2.imshow("Debug: Light Mask", light_mask)
            cv2.imshow("Debug: Ball Detection", debug_img)

        return (row, col)
