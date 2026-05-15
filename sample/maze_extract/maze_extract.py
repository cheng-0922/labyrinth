import cv2
import numpy as np


class MazeGraphExtractor:
    def __init__(self, maze_size=9, wall_threshold=0.25, blur_kernel=5, debug=False):
        self.maze_size = maze_size
        self.wall_threshold = wall_threshold
        self.blur_kernel = blur_kernel
        self.debug = debug  # 新增 Debug 開關

    def process(self, img):
        pts = self._find_red_markers(img)
        if pts is None:
            print("❌ 無法在畫面中找到足夠的紅色定位塊")
            return None, None

        warped_img = self._four_point_transform(img, pts)
        maze_grid = self._extract_grid(warped_img)
        adjacency_list = self._build_adjacency_list(maze_grid)

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
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    def _extract_grid(self, img):
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        k_size = self.blur_kernel | 1 
        blurred = cv2.GaussianBlur(gray, (k_size, k_size), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        cell_h, cell_w = h / self.maze_size, w / self.maze_size
        pad_y, pad_x = int(cell_h * 0.5), int(cell_w * 0.5)

        thresh[0:pad_y, :] = 0
        thresh[h-pad_y:h, :] = 0
        thresh[:, 0:pad_x] = 0
        thresh[:, w-pad_x:w] = 0

        if self.debug:
            # 【除錯畫面 3】顯示拉平並消除邊緣紅塊後的黑白迷宮
            # 為了讓網格更清楚，我們在上面畫出紅色格線
            grid_preview = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            for i in range(1, self.maze_size):
                cv2.line(grid_preview, (0, int(i*cell_h)), (w, int(i*cell_h)), (0, 0, 255), 1)
                cv2.line(grid_preview, (int(i*cell_w), 0), (int(i*cell_w), h), (0, 0, 255), 1)
            cv2.imshow("Debug: Grid Threshold", grid_preview)

        maze_grid = np.zeros((self.maze_size, self.maze_size), dtype=int)
        for row in range(self.maze_size):
            for col in range(self.maze_size):
                y1, y2 = int(row * cell_h), int((row + 1) * cell_h)
                x1, x2 = int(col * cell_w), int((col + 1) * cell_w)
                
                cell_roi = thresh[y1:y2, x1:x2]
                white_area = cv2.countNonZero(cell_roi)
                cell_area = max((y2 - y1) * (x2 - x1), 1)

                # ==========================================
                # 🌟 【邊緣補償邏輯】：修復被切半的外牆
                # ==========================================
                # 如果是位在迷宮「最外圈」的網格 (row或col為0，或等於最大值)
                if row == 0 or row == self.maze_size - 1 or col == 0 or col == self.maze_size - 1:
                    # 把它偵測到的牆壁面積乘以 2，用數學還原真實的牆壁厚度
                    effective_area = white_area * 2.0
                else:
                    effective_area = white_area

                # 使用補償後的面積來判定是否超過門檻
                if (effective_area / cell_area) > self.wall_threshold:
                    maze_grid[row][col] = 1 
                else:
                    maze_grid[row][col] = 0
        return maze_grid

    def _build_adjacency_list(self, grid):
        adj_list = {}
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for r in range(self.maze_size):
            for c in range(self.maze_size):
                if grid[r][c] == 0:
                    node = (r, c)
                    adj_list[node] = []
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.maze_size and 0 <= nc < self.maze_size:
                            if grid[nr][nc] == 0:
                                adj_list[node].append((nr, nc))
        return adj_list


