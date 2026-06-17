import cv2
import numpy as np


class BallDetector:

    def __init__(self, maze_size=9, debug=False, show_windows=True):
        self.maze_size = maze_size
        self.debug = debug
        self.show_windows = show_windows
        self.ref_gray = None
    params={
        "redl" : 10,
        "redh" : 170,
        "redsaturate1" : 100,
        "redsaturate2" : 255,
        "redvibrant1" : 50,
        "redvibrant2" : 255,
        "circularity" : 0.8,
    }
    param_alias = {
        "rl" : "redl",
        "rh" : "redh",
        "rs1" : "redsaturate1",
        "rs2" : "redsaturate2",
        "rv1" : "redvibrant1",
        "rv2" : "redvibrant2",
        "cir" : "circularity",
    }
    def get_params(self):
        print(self.params)

    def set_params(self, cmd: str):
        """
        支援：
        - w=0.45
        - w 0.45
        - wall=0.45 inset=0.3
        - d (切換 debug 模式)
        """
        cmd = cmd.strip()
        
        # 處理單獨的 debug 切換指令
        if cmd == "d":
            self.debug = not self.debug
            print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
            return

        # 把 "=" 統一換成空格，統一格式，例如 "w=0.45 i 0.3" -> "w 0.45 i 0.3"
        normalized_cmd = cmd.replace("=", " ")
        tokens = normalized_cmd.split()

        # 兩兩一組進行解析 (key, value)
        for i in range(0, len(tokens) - 1, 2):
            k = tokens[i]
            v_str = tokens[i+1]

            key = self.param_alias.get(k, k)

            if key not in self.params:
                print(f"Unknown param: {key}")
                continue

            try:
                if '.' in v_str:
                    v = float(v_str)
                else:
                    v = int(v_str)
                self.params[key] = v
                print(f"[{key}] -> {v}")
            except ValueError:
                print(f"Invalid value for {key}: {v_str}")

    def set_reference(self, warped_img):
        """存入空迷宮參考影像（背景相減模式用）"""
        self.ref_gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
        print("✅ 背景參考已設定")

    def find_ball(self, warped_img):
        """
        HSV 紅色遮罩找球，回傳 (row, col)，找不到回傳 None。
        假設迷宮中只有球是紅色，直接取遮罩重心。
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
 
        # ── Step 1：紅色 HSV 遮罩（兩段合併）────────────────────────────────
        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0,self.params["redsaturate1"], self.params["redvibrant1"]]), np.array([self.params["redl"],  self.params["redsaturate2"], self.params["redvibrant2"]]))
        mask2 = cv2.inRange(hsv, np.array([self.params["redh"], self.params["redsaturate1"], self.params["redvibrant1"]]), np.array([180, self.params["redsaturate2"], self.params["redvibrant2"]]))
        red_mask = cv2.bitwise_or(mask1, mask2)
        # ────────────────────────────────────────────────────────────────────
 
        # ── Step 2：取遮罩重心 ────────────────────────────────────────────────
        M = cv2.moments(red_mask)
        if M["m00"] == 0:
            if self.debug and self.show_windows:
                cv2.imshow("Debug: Red Mask", red_mask)
            return None
 
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        # ────────────────────────────────────────────────────────────────────
 
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))
 
        if self.debug and self.show_windows:
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), 5, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col})",
                        (cx + 5, cy - 5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Red Mask", red_mask)
            cv2.imshow("Debug: Ball Detection", debug_img)
 
        return (row, col)
    def get_ball_pixel_position(self, warped_img):
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
 
        # ── Step 1：紅色 HSV 遮罩（兩段合併）────────────────────────────────
        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0,   100, 50]), np.array([10,  255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 100, 50]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(mask1, mask2)
        # ────────────────────────────────────────────────────────────────────
 
        # ── Step 2：取遮罩重心 ────────────────────────────────────────────────
        M = cv2.moments(red_mask)
        if M["m00"] == 0:
            if self.debug and self.show_windows:
                cv2.imshow("Debug: Red Mask", red_mask)
            return None
 
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        return (cx,cy)
    def find_ball_round(self, warped_img):
        """
        HSV 紅色遮罩找球，回傳 (row, col)，找不到回傳 None。

        紅色在 HSV 分佈於兩段：H:0-10 和 H:170-180，需合併。
        """
        h, w = warped_img.shape[:2]
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        cell_px = min(cell_h, cell_w)

        r_expected = cell_px * (10 / 15) / 2
        # area_min = np.pi * (r_expected * 0.5) ** 2
        area_min = 0
        area_max = np.pi * (r_expected * 1.5) ** 2

        # ── Step 1：紅色 HSV 遮罩（兩段合併）────────────────────────────────
        hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0,self.params["redsaturate"], self.params["redvibrant"]]), np.array([self.params["redl"],  255, 255]))
        mask2 = cv2.inRange(hsv, np.array([self.params["redh"], self.params["redsaturate"], self.params["redvibrant"]]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(mask1, mask2)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 2：形態學，填補球輪廓破洞 ───────────────────────────────────
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN,  kernel)
        # ────────────────────────────────────────────────────────────────────

        # ── Step 3：凸包 + 面積 + 圓形度過濾 ────────────────────────────────
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_circularity = 0

        for cnt in contours:
            hull = cv2.convexHull(cnt)
            area = cv2.contourArea(hull)
            if area < area_min or area > area_max:
                continue

            perimeter = cv2.arcLength(hull, True)
            if perimeter == 0:
                continue

            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < self.params["circularity"]:
                continue

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
            if self.debug and self.show_windows:
                cv2.imshow("Debug: Red Mask", red_mask)
            return None

        cx, cy = best
        row = max(0, min(int(cy / cell_h), self.maze_size - 1))
        col = max(0, min(int(cx / cell_w), self.maze_size - 1))

        if self.debug and self.show_windows:
            debug_img = warped_img.copy()
            cv2.circle(debug_img, (cx, cy), int(r_expected), (0, 255, 0), 2)
            cv2.circle(debug_img, (cx, cy), 3, (0, 255, 0), -1)
            cv2.putText(debug_img, f"({row},{col}) c={best_circularity:.2f}",
                        (cx + 5, cy - 5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.imshow("Debug: Red Mask", red_mask)
            cv2.imshow("Debug: Ball Detection", debug_img)

        return (row, col)
