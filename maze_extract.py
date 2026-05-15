import cv2
import numpy as np

class MazeGraphExtractor:
    def __init__(self, maze_size=8, wall_threshold=0.25, blur_kernel=5, inset_ratio=0.04):
        """
        初始化迷宮圖論擷取器
        :param maze_size: 迷宮的網格尺寸 (預設 8x8)
        :param wall_threshold: 網格內黑線佔比多少視為牆壁 (預設 25%)
        :param blur_kernel: 高斯模糊的強度 (預設 5，避免過度模糊吃掉細牆)
        :param inset_ratio: 網格內縮比例，用來避開外圍的殘留定位點 (預設 4%)
        """
        self.maze_size = maze_size
        self.wall_threshold = wall_threshold
        self.blur_kernel = blur_kernel
        self.inset_ratio = inset_ratio

    def process(self, img):
        # 1. 尋找四個紅色頂點
        pts = self._find_red_markers(img)
        if pts is None:
            print("❌ 無法在畫面中找到足夠的紅色定位塊")
            return None, None

        # 2. 進行透視投影轉換 (拉平影像)
        warped_img = self._four_point_transform(img, pts)

        # 3. 擷取迷宮 2D 陣列 (加入邊緣內縮處理)
        maze_grid = self._extract_grid(warped_img)

        # 4. 將 2D 陣列轉換為 Graph (Adjacency List)
        adjacency_list = self._build_adjacency_list(maze_grid)

        return warped_img, adjacency_list

    def _find_red_markers(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lower_red_1 = np.array([0, 70, 50])
        upper_red_1 = np.array([10, 255, 255])
        lower_red_2 = np.array([170, 70, 50])
        upper_red_2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        red_mask = mask1 + mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # [修復風險 1] 加入最小面積過濾，避免迷宮內的紅色小雜訊干擾
        valid_contours = [c for c in contours if cv2.contourArea(c) > 50]

        if len(valid_contours) < 4:
            return None

        # 取面積最大的 4 個
        valid_contours = sorted(valid_contours, key=cv2.contourArea, reverse=True)[:4]

        centers = []
        for c in valid_contours:
            # [修復風險 3] 改用最小包覆圓 (Min Enclosing Circle) 取代 Moments 算質心
            # 這樣就算紅塊被手指稍微遮擋變成 L 型，抓到的中心點依然會是準確的幾何中心
            (x, y), radius = cv2.minEnclosingCircle(c)
            centers.append([x, y])
        
        return np.array(centers, dtype="float32")

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

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        
        return warped

    def _extract_grid(self, img):
        h, w = img.shape[:2]

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        k_size = self.blur_kernel | 1 
        blurred = cv2.GaussianBlur(gray, (k_size, k_size), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # --- 採用自我校準的邏輯 (Self-calibrating padding) ---
        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        
        # 設定半個網格的寬/高作為安全邊界 (Safe margin)
        pad_y = int(cell_h * 0.5)
        pad_x = int(cell_w * 0.5)

        # 將邊緣殘留的定位點直接塗黑 (0，代表無牆壁的通道)
        # 這樣不改變整體圖像尺寸，完美保留均勻的網格座標系
        thresh[0:pad_y, :] = 0          # 頂部邊緣
        thresh[h-pad_y:h, :] = 0        # 底部邊緣
        thresh[:, 0:pad_x] = 0          # 左側邊緣
        thresh[:, w-pad_x:w] = 0        # 右側邊緣

        maze_grid = np.zeros((self.maze_size, self.maze_size), dtype=int)

        for row in range(self.maze_size):
            for col in range(self.maze_size):
                y1, y2 = int(row * cell_h), int((row + 1) * cell_h)
                x1, x2 = int(col * cell_w), int((col + 1) * cell_w)
                
                cell_roi = thresh[y1:y2, x1:x2]
                white_area = cv2.countNonZero(cell_roi)
                cell_area = max((y2 - y1) * (x2 - x1), 1)

                if (white_area / cell_area) > self.wall_threshold:
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