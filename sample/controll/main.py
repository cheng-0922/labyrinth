import argparse
import sys
import cv2
import time

from maze import Maze
from maze_extract import MazeGraphExtractor 
from tracker import MarbleTracker
from hardware import MazeController

def get_absolute_directions(maze, path_nodes):
    directions = []
    for i in range(len(path_nodes) - 1):
        current_node = path_nodes[i]
        next_node = path_nodes[i+1]
        
        d = current_node.get_direction(next_node) 
        # 安全型別檢查
        if hasattr(d, 'value'):
            directions.append(d.value)
        else:
            directions.append(int(d)) 
    return directions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maze Auto Solver")
    parser.add_argument("-d", "--debug", action="store_true", help="開啟除錯視窗")
    args = parser.parse_args()

    # 初始化模組
    extractor = MazeGraphExtractor(maze_size=9, wall_threshold=0.25, debug=args.debug)
    controller = MazeController() 

    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        picam2.start()
        print("🎥 相機已啟動。請將迷宮對準鏡頭，按 's' 掃描建圖。")
    except ImportError:
        print("❌ 找不到 picamera2 模組，請確保在 RPi 上執行。")
        sys.exit(1)

    try:
        # === 階段 1：掃描建圖 ===
        my_maze = Maze()
        graph_ready = False

        while not graph_ready:
            raw_frame = picam2.capture_array()
            frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("Setup: Align Maze", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                warped_img, raw_graph = extractor.process(frame)
                if raw_graph is not None:
                    cv2.imshow("Warped Maze", warped_img)
                    my_maze.load_from_graph(raw_graph)
                    graph_ready = True
            elif key == ord('q'):
                sys.exit(0)

        # === 階段 2：BFS 尋路 ===
        start_coord = (4, 0)
        end_coord = (4, 8)
        
        try:
            start_node = my_maze.node_dict[start_coord]
            end_node = my_maze.node_dict[end_coord]
        except KeyError as e:
            print(f"❌ 錯誤：在迷宮地圖中找不到座標 {e}！起終點可能被判定為牆壁。")
            sys.exit(1)
            
        path_nodes = my_maze.BFS_2(start_node, end_node)
        if not path_nodes:
            print("❌ 找不到可達路徑！")
            sys.exit(1)
            
        tilt_commands = get_absolute_directions(my_maze, path_nodes)
        print(f"🗺️ 規劃完成！需要執行 {len(tilt_commands)} 步。")

        # === 階段 3：初始化追蹤器 ===
        cv2.destroyAllWindows()
        tracker = MarbleTracker()
        tracker.capture_background(picam2)

        print("\n🚀 請將【彈珠】放入起點，3 秒後開始自走...")
        time.sleep(3)

        # === 階段 4：走停輪詢與位置驗證 ===
        step_idx = 0
        lost_counter = 0
        MAX_RETRIES = 10
        
        CELL_W = tracker.resolution[0] / extractor.maze_size
        CELL_H = tracker.resolution[1] / extractor.maze_size

        while step_idx < len(tilt_commands):
            target_node = path_nodes[step_idx + 1]
            target_r, target_c = target_node.index 
            
            x, y, debug_frame = tracker.detect(picam2)
            
            if x is not None and y is not None:
                lost_counter = 0 
                current_c = int(x // CELL_W)
                current_r = int(y // CELL_H)
                
                cv2.circle(debug_frame, (x, y), 10, (0, 0, 255), 2)
                cv2.imshow("Auto Solving...", debug_frame)
                cv2.waitKey(1)
                
                print(f"📍 彈珠: ({current_r}, {current_c}) | 目標: ({target_r}, {target_c})")

                # 位置驗證
                if current_r == target_r and current_c == target_c:
                    print("✅ 成功抵達節點！")
                    step_idx += 1
                    if step_idx >= len(tilt_commands):
                        break 
                else:
                    print("🔄 尚未抵達或位置偏移，重新嘗試傾斜...")

                next_tilt = tilt_commands[step_idx]
                controller.tilt_and_stop(next_tilt, tilt_time=0.4)
                
            else:
                lost_counter += 1
                print(f"⚠️ 找不到彈珠！({lost_counter}/{MAX_RETRIES})")
                cv2.imshow("Auto Solving...", debug_frame)
                cv2.waitKey(1)
                
                if lost_counter >= MAX_RETRIES:
                    print("❌ 迷失彈珠超時，系統中止！")
                    sys.exit(1)
                time.sleep(1)

        print("\n🎉 抵達終點！自動通關完成！")
        time.sleep(2)

    except KeyboardInterrupt:
        print("\n程式已手動中斷")
    finally:
        controller.cleanup()
        picam2.stop()
        cv2.destroyAllWindows()