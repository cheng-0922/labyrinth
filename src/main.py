
import argparse
import sys
import cv2
import serial
import time
import threading
import numpy as np
from maze import Maze
from node import Node
from maze_extract import MazeGraphExtractor 
from ball_detector import BallDetector
from ser import ArduinoSerial
class Timer:
    def __enter__(self):
        # 當進入 with 區塊時，記錄開始時間
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 當離開 with 區塊時，計算並印出花費時間
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        print(f"執行耗時: {self.elapsed_time:.6f} 秒")

PORT = "/dev/ttyACM0"   # Arduino USB 預設；若找不到改成 /dev/ttyACM1
BAUD = 9600

def cmd_loop(state,extractor,arduino):
    while True:
        cmd = input(">> ")
        if state == 0:
            if cmd ==':':
                state = 0
            #start auto
            else : arduino.send(cmd)
        if state == 1:
            if cmd =='q':
                state = 0
            else : extractor.set_params(cmd)

def send_time(arduino, direction: int, delay_time: int):

    try:        
        arduino.send_line(str(direction))
        arduino.send_line(str(delay_time))
        
        print(f" 已發送控制訊號 - 方向: {direction}, 延遲: {delay_time} ms")
        
    except Exception as e:
        print(f" 傳送角度控制訊號失敗: {e}")


if __name__ == "__main__":
    # --- 1. 設定啟動參數 ---
    parser = argparse.ArgumentParser(description="Maze Scanner")
    parser.add_argument("-i", "--image", type=str, help="指定靜態圖片的路徑 (若無則啟動相機)")
    parser.add_argument("-d", "--debug", action="store_true", help="開啟除錯視窗")
    args = parser.parse_args()

    # ---  ---
    extractor = MazeGraphExtractor(maze_size=9, wall_threshold=0.333, debug=args.debug)
    ball = BallDetector(maze_size = 9, debug=args.debug)
    arduino = ArduinoSerial(PORT, BAUD)
    state = 1
    threading.Thread(target=cmd_loop, args=(state,extractor,arduino,), daemon=True).start()

    # --- 2. 靜態圖片模式 ---
    if args.image:
        print(f"📷 正在讀取圖片: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print("❌ 錯誤：找不到或無法讀取圖片。")
            sys.exit(1)

        # 處理圖片
        warped_img, raw_graph = extractor.process(frame)
        
        if raw_graph is not None:
            cv2.imshow("Original Image", frame)
            cv2.imshow("Final Warped Maze", warped_img)
            print("✅ 迷宮解析完成！(按任意鍵關閉)")
            if raw_graph is not None:
                # 2.  Maze 
                my_maze = Maze()
                
                # 3. 把 tuple 放入 load_from_graph 函式
                my_maze.load_from_graph(raw_graph)

                # 測試一下轉換結果：印出起點 所有
                for i in my_maze.nodes:
                    i.printparam()
                
                start = (0,4)
                end = (8,4)
                nodelist = my_maze.BFS_2(my_maze.node_dict[start],my_maze.node_dict[end] )
                for i in nodelist:
                    print(i.get_index())
                path=[]
                for i in nodelist:
                    if i.get_index() != end:
                        path.append(my_maze.getDirection(my_maze.node_dict[nodelist[nodelist.index(i)].get_index()], my_maze.node_dict[nodelist[nodelist.index(i)+1].get_index()]))
                print([int(x) for x in path])
                
            cv2.waitKey(0) # 靜態圖模式下，無限期等待使用者按鍵
        cv2.destroyAllWindows()

    # --- 3. 實體相機模式 ---
    else:
        try:
            # 只有在相機模式才引入 picamera2，避免在一般電腦上報錯
            from picamera2 import Picamera2
            picam2 = Picamera2()
            picam2.start()
            print("🎥 相機已啟動。(按 's' 解析，按 'q' 離開)")
        except ImportError:
            print("❌ 錯誤：找不到 picamera2 模組。若是使用一般電腦，請加上 -i 參數指定圖片測試。")
            sys.exit(1)
            print(f"開啟 {PORT} @ {BAUD} baud ...")
        
        try:
            
            while True:
                # serial communication
                msg = arduino.read()
                if msg:
                    print("Arduino:", msg)
                # update camera
                raw_frame = picam2.capture_array()
                frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
                cv2.imshow("Camera Preview", frame)
                key = cv2.waitKey(1) & 0xFF
                warped_img = None
                
                if key == ord('r'):
                    arduino.send("r")
                elif key == ord('j'):
                    arduino.send("j")
                elif key == ord('q'):
                    arduino.send("q")
                elif key == ord('s'):
            
                    m = Maze()
                    warped_img, graph = extractor.process(frame)
                    if graph is None:
                        continue
                    m.load_from_graph(graph)
                    
                    arduino.send('s') 
                    time.sleep(0.1) 
                    
                    end = (8, 8)
                    step_delay = 800 
                    
                    while True:
                        raw_frame = picam2.capture_array()
                        frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
                        cv2.imshow("Camera Preview", frame)
                        cv2.waitKey(1)
                        
                        warped_img, _ = extractor.process(frame)
                        if warped_img is None:
                            continue
                            
                        now = ball.find_ball(warped_img)
                        
                        if now == end:
                            print(f"🏁 Goal reached: {end}")
                            break
                            
                        try:
                            path_nodes = m.BFS_2(m.node_dict[now], m.node_dict[end])
                            if not path_nodes or len(path_nodes) < 2:
                                time.sleep(0.2)
                                continue
                                
                            next_dir = m.getDirection(path_nodes[0], path_nodes[1])
                            send_time(arduino, next_dir - 1, step_delay)
                            
                            time.sleep(step_delay / 1000.0)
                            
                        except KeyError:
                            time.sleep(0.2)
                            
                    arduino.send('q')


                elif key == ord('p'):
                    m = Maze()
                    warped_img, graph = extractor.process(frame)
                    if graph is not None:
                        m.load_from_graph(graph)
                        arduino.send('p')
                        time.sleep(0.1)
                        
                        end = (8, 8)
                        kp, ki, kd = 1.5, 0.05, 0.3
                        prev_err_x, prev_err_y = 0.0, 0.0
                        integral_x, integral_y = 0.0, 0.0
                        
                        while True:
                            raw_frame = picam2.capture_array()
                            
                            pts = extractor._find_green_markers(raw_frame)
                            pts = np.array(pts, dtype=np.float32)
                            if pts is None:
                                print("無法在畫面中找到足夠的綠色定位塊")
                            else:
                                warped_img = extractor._four_point_transform(raw_frame, pts)
                            
                            now = ball.find_ball(warped_img)
                            if now is None:
                                continue
                            
                            if now == end:
                                print("🏁 已抵達終點！")
                                break
                                
                            try:
                                path_nodes = m.BFS_2(m.node_dict[now], m.node_dict[end])
                                if not path_nodes or len(path_nodes) < 2:
                                    time.sleep(0.05)
                                    continue

                                target_coord = path_nodes[1].get_index()
                                h, w = warped_img.shape[:2]
                                cell_w, cell_h = w / 9.0, h / 9.0
                                
                                target_px_x = (target_coord[1] + 0.5) * cell_w
                                target_px_y = (target_coord[0] + 0.5) * cell_h
                                
                                ball_px = ball.get_ball_pixel_position(warped_img)
                                if ball_px is None:
                                    continue
                                ball_px_x, ball_px_y = ball_px
                                
                                err_x = target_px_x - ball_px_x
                                err_y = target_px_y - ball_px_y
                                
                                integral_x = np.clip(integral_x + err_x, -50, 50)
                                integral_y = np.clip(integral_y + err_y, -50, 50)
                                
                                deriv_x = err_x - prev_err_x
                                deriv_y = err_y - prev_err_y
                                
                                output_x = kp * err_x + ki * integral_x + kd * deriv_x
                                output_y = kp * err_y + ki * integral_y + kd * deriv_y
                                
                                prev_err_x = err_x
                                prev_err_y = err_y
                                
                                angle_x = int(np.clip(output_x, -15, 15))
                                angle_y = int(np.clip(output_y, -15, 15))
                                
                                cmd_str = f"X{angle_x:+d}Y{angle_y:+d}"
                                arduino.send_line(cmd_str)
                                
                                time.sleep(0.1) # 稍微降低延遲以提高 PID 反應速度
                                
                            except KeyError:
                                time.sleep(0.05)

                                
                        arduino.send('q')
                elif key == ord('t'):
                    arduino.send("t")
                elif key == ord('m'):
                    with Timer():
                        print("\n🔍 掃描中...")
                        warped_img, graph = extractor.process(frame)
                        if graph is not None:
                            cv2.imshow("Final Warped Maze", warped_img)
                elif key == ord('f'):
                    with Timer():
                        print("\n🔍 掃描球的位置...")
                        warped_img, _ = extractor.process(frame)
                        if warped_img is None:
                            print("❌ 無法校正影像，請確認定位點可見")
                        else:
                            pos = ball.find_ball(warped_img)
                            print(f"球的位置：{pos}")       



                
                if key == 27 :
                    break
        finally:
            picam2.stop()
            cv2.destroyAllWindows()
            print("相機已安全關閉")
