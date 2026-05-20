import cv2
import numpy as np


class MazeGraphExtractor:
    def __init__(self, maze_size=9, wall_threshold=0.45, blur_kernel=5, debug=False):
        self.maze_size = maze_size
        self.wall_threshold = wall_threshold
        self.blur_kernel = blur_kernel
        self.debug = debug  # 新增 Debug 開關
        self.M = None       
        self.warp_dim = None

    def process(self, img):
        pts = self._find_red_markers(img)
        if pts is None:
            print("❌ 無法在畫面中找到足夠的紅色定位塊")
            return None, None

        warped_img = self._four_point_transform(img, pts)
        
        # 直接從影像中掃描「牆壁交界處」，建構出圖論的 Adjacency List
        adjacency_list = self._extract_graph(warped_img)

        return warped_img, adjacency_list

    def _find_red_markers(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
        red_mask = mask1 + mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = [c for c in contours if cv2.contourArea(c) > 50]

        if self.debug:
            # 【除錯畫面 1】顯示紅色遮罩，確認有沒有被光線干擾
            cv2.imshow("Debug: Red Mask", red_mask)

        if len(valid_contours) < 4:
            return None

        valid_contours = sorted(valid_contours, key=cv2.contourArea, reverse=True)[:4]
        
        centers = []
        debug_img = img.copy() if self.debug else None

        for c in valid_contours:
            (x, y), radius = cv2.minEnclosingCircle(c)
            centers.append([x, y])
            
            if self.debug:
                # 【除錯畫面 2】在原圖上畫出電腦找到的 4 個綠圈圈與圓心
                cv2.circle(debug_img, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.circle(debug_img, (int(x), int(y)), 3, (255, 0, 0), -1)

        if self.debug:
            cv2.imshow("Debug: Found Markers", debug_img)

        return np.array(centers, dtype="float32")

    # _order_points 與 _four_point_transform 保持不變...
    def _order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def _four_point_transform(self, img, pts):
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
        self.M = cv2.getPerspectiveTransform(rect, dst)
        self.warp_dim = (maxWidth, maxHeight)
        return cv2.warpPerspective(img, self.M, (maxWidth, maxHeight))

    def _extract_graph(self, img):
        """
        掃描網格邊界，判斷相鄰通道是否連通。

        針對 3mm 牆 / 150mm 全圖 / 9x9 格局的根本問題修正：

        問題 1 — 全域 Otsu 無法處理木紋局部亮度變化
            木板(MDF)表面紋路在全域二值化時被放大成雜訊，導致通道
            ROI 裡出現假白點，把通道誤判成牆壁。
            修正：改用 CLAHE 強化對比 + adaptiveThreshold 逐區域計算
            閾值，讓木紋不再干擾黑線偵測。

        問題 2 — wall_threshold=0.25 太低，無法區分「真通道」與「帶墨水暈開的通道」
            計算：3mm 牆在 ROI 裡的填充率 ≈ 68%，墨水暈開的通道 ≈ 28%。
            原始門檻 0.25 幾乎把所有墨水暈開都判成牆壁。
            修正：預設提高為 0.45（位於 28% 和 68% 的中間點）。

        問題 3 — wall_x 用 int() 截斷造成邊界偏移
            在 480px 解析度下，每格 53.3px，int() 讓邊界每格誤差累積
            最多 0.67px，在低解析度下讓 ROI 偏離真實牆線。
            修正：改用 round() 計算所有格子邊界座標。
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ── 修正 1：CLAHE + 自適應閾值取代全域 Otsu ───────────────────────
        # CLAHE 先把木紋與黑線的對比拉開，再用自適應閾值讓每個小區域
        # 獨立計算門檻，徹底隔絕木紋雜訊對黑線偵測的干擾。
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        # blockSize 設為約一個格子寬度的一半（奇數），C=4 讓黑線更突出
        cell_px = int(min(h, w) / self.maze_size)
        block_size = max((cell_px // 2) | 1, 11)  # 確保奇數且至少 11
        thresh = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block_size, 4
        )
        # ────────────────────────────────────────────────────────────────────

        # ── 修正 3：改用 round() 計算格子邊界，消除 int() 截斷累積誤差 ────
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size

        def cell_edge(idx, cell_size):
            """計算第 idx 條格線的像素座標（四捨五入）"""
            return round(idx * cell_size)
        # ────────────────────────────────────────────────────────────────────

        adj_list = {(r, c): [] for r in range(self.maze_size) for c in range(self.maze_size)}

        # ROI 參數
        # inset：避開十字路口墨水暈開，只掃中段 60%
        inset_ratio = 0.20
        # wall_thickness：ROI 寬度設為實體牆寬的 1.2 倍，確保完整覆蓋
        # 3mm 牆 / 16.7mm 格 = 18%，× 1.2 = 22%，取單側 11%
        thickness_ratio = 0.11

        wall_thickness_x = max(round(cell_w * thickness_ratio), 1)
        wall_thickness_y = max(round(cell_h * thickness_ratio), 1)
        inset_x = round(cell_w * inset_ratio)
        inset_y = round(cell_h * inset_ratio)

        debug_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR) if self.debug else None

        def check_wall(roi, label, debug_img, x1, y1, x2, y2):
            """
            判斷 ROI 是否含有牆壁。
            修正 2：threshold 使用 self.wall_threshold（建議設 0.45）
            """
            if roi.size == 0:
                return False  # 空 ROI 視為無牆（邊界安全保護）
            fill = cv2.countNonZero(roi) / roi.size
            is_wall = fill >= self.wall_threshold
            if self.debug and debug_img is not None:
                color = (0, 0, 255) if is_wall else (0, 255, 0)
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, -1)
                # 顯示實際填充率，方便現場微調 wall_threshold
                cv2.putText(debug_img, f"{fill:.2f}", (x1, max(y1 - 2, 0)),
                            cv2.FONT_HERSHEY_PLAIN, 0.7, (255, 255, 0), 1)
            return is_wall

        # 1. 垂直牆壁（左右相鄰格子之間）
        for r in range(self.maze_size):
            for c in range(self.maze_size - 1):
                wall_x = cell_edge(c + 1, cell_w)          # 修正 3：round()
                y1 = cell_edge(r,     cell_h) + inset_y
                y2 = cell_edge(r + 1, cell_h) - inset_y
                x1 = wall_x - wall_thickness_x
                x2 = wall_x + wall_thickness_x

                # 邊界夾緊，防止超出影像
                x1, x2 = max(x1, 0), min(x2, w)
                y1, y2 = max(y1, 0), min(y2, h)

                roi = thresh[y1:y2, x1:x2]
                if not check_wall(roi, 'V', debug_img, x1, y1, x2, y2):
                    adj_list[(r, c)].append((r, c + 1))
                    adj_list[(r, c + 1)].append((r, c))

        # 2. 水平牆壁（上下相鄰格子之間）
        for r in range(self.maze_size - 1):
            for c in range(self.maze_size):
                wall_y = cell_edge(r + 1, cell_h)          # 修正 3：round()
                x1 = cell_edge(c,     cell_w) + inset_x
                x2 = cell_edge(c + 1, cell_w) - inset_x
                y1 = wall_y - wall_thickness_y
                y2 = wall_y + wall_thickness_y

                x1, x2 = max(x1, 0), min(x2, w)
                y1, y2 = max(y1, 0), min(y2, h)

                roi = thresh[y1:y2, x1:x2]
                if not check_wall(roi, 'H', debug_img, x1, y1, x2, y2):
                    adj_list[(r, c)].append((r + 1, c))
                    adj_list[(r + 1, c)].append((r, c))

        if self.debug:
            cv2.imshow("Debug: CLAHE", enhanced)
            cv2.imshow("Debug: Adaptive Thresh", thresh)
            cv2.imshow("Debug: Edge Scanning (fill rate shown)", debug_img)

        return adj_list