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
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    def _extract_graph(self, img):
        """
        直接掃描網格邊界，判斷相鄰通道是否連通
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        k_size = self.blur_kernel | 1 
        blurred = cv2.GaussianBlur(gray, (k_size, k_size), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        cell_h = h / self.maze_size
        cell_w = w / self.maze_size
        
        # 初始化 64 個節點 (所有格子預設皆為獨立通道)
        adj_list = { (r, c): [] for r in range(self.maze_size) for c in range(self.maze_size) }
        
        # 設定「邊界檢查器」的寬度與內縮
        # 內縮是為了避開十字路口的交叉點，我們只檢查「通道正中央」的牆壁段落
        inset_y = int(cell_h * 0.2)
        inset_x = int(cell_w * 0.2)
        wall_thickness_x = max(int(cell_w * 0.15), 2)
        wall_thickness_y = max(int(cell_h * 0.15), 2)

        # 準備 Debug 視覺化圖
        debug_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR) if self.debug else None

        # 1. 檢查左右相鄰的格子 (垂直的牆壁)
        for r in range(self.maze_size):
            for c in range(self.maze_size - 1): # 只需要檢查到倒數第二格
                wall_x = int((c + 1) * cell_w)  # 兩格交界的 X 座標
                
                # 框出交界處的掃描範圍 (ROI)
                y1 = int(r * cell_h) + inset_y
                y2 = int((r + 1) * cell_h) - inset_y
                x1 = wall_x - wall_thickness_x
                x2 = wall_x + wall_thickness_x
                
                roi = thresh[y1:y2, x1:x2]
                white_area = cv2.countNonZero(roi)
                area = max((y2 - y1) * (x2 - x1), 1)

                # 如果這個狹長的交界區沒有什麼黑線 (小於門檻)，代表通道是相連的！
                if (white_area / area) < self.wall_threshold:
                    adj_list[(r, c)].append((r, c + 1))
                    adj_list[(r, c + 1)].append((r, c))
                    if self.debug: 
                        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), -1) # 綠色代表相通
                else:
                    if self.debug: 
                        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 0, 255), -1) # 紅色代表被牆阻擋

        # 2. 檢查上下相鄰的格子 (水平的牆壁)
        for r in range(self.maze_size - 1):
            for c in range(self.maze_size):
                wall_y = int((r + 1) * cell_h) # 兩格交界的 Y 座標
                
                x1 = int(c * cell_w) + inset_x
                x2 = int((c + 1) * cell_w) - inset_x
                y1 = wall_y - wall_thickness_y
                y2 = wall_y + wall_thickness_y
                
                roi = thresh[y1:y2, x1:x2]
                white_area = cv2.countNonZero(roi)
                area = max((y2 - y1) * (x2 - x1), 1)

                if (white_area / area) < self.wall_threshold:
                    adj_list[(r, c)].append((r + 1, c))
                    adj_list[(r + 1, c)].append((r, c))
                    if self.debug: 
                        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), -1)
                else:
                    if self.debug: 
                        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 0, 255), -1)

        if self.debug:
            cv2.imshow("Debug: Edge Scanning", debug_img)

        return adj_list