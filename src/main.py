import argparse
import sys
import cv2
import serial
import time
import threading
import numpy as np
import queue
from maze import Maze
from node import Node
from maze_extract import MazeGraphExtractor 
from ball_detector import BallDetector
from ser import ArduinoSerial
from control import PredictiveController
class Timer:
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        print(f"執行耗時: {self.elapsed_time:.6f} 秒")

PORT = "/dev/ttyACM0"   # Arduino USB 預設；若找不到改成 /dev/ttyACM1
BAUD = 9600
END_POINT = (8,8)
cmd_queue = queue.Queue()
params = {
    "size" : 9,
    "wall_threshold" : 0.333,
    "endpoint" : END_POINT,

    "kp": 0.15,
    "ki": 0.05,
    "kd": 0.03,
    "slowstep":3,
    "highstep" :8,
    "compensate" :1,
    "lookahead" : 0.25,
    "delayPID" : 0.1,
}
param_alias = {
    "w" : "wall_threshold" ,
    "ss" : "slowstep",
    "hs" : "highstep",
    "c" : "compensate",
    "l" : "lookahead",
    "dt" : "delayPID",
    "end" : "endpoint"
}
def set_params(cmd: str):
        """
        支援：
        - w=0.45
        - w 0.45
        - wall=0.45 inset=0.3
        - d (切換 debug 模式)
        """
        cmd = cmd.strip()
        
        # 把 "=" 統一換成空格，統一格式，例如 "w=0.45 i 0.3" -> "w 0.45 i 0.3"
        normalized_cmd = cmd.replace("=", " ")
        tokens = normalized_cmd.split()

        for i in range(0, len(tokens) - 1, 2):
            k = tokens[i]
            v_str = tokens[i+1]

            key = param_alias.get(k, k)

            if key not in params:
                print(f"Unknown param: {key}")
                continue

            try:
                v = float(v_str)
                params[key] = v
                print(f"[{key}] -> {v}")
            except ValueError:
                print(f"Invalid value for {key}: {v_str}")

def cmd_input_loop():
    while True:
        cmd = input(">> ")
        if cmd:
            cmd_queue.put(cmd)

def handle_cmd(cmd, shared, extractor):
    if shared["state"] == 0:
        if cmd ==':':
            shared["state"] = 1
            print("state 0 change to state 1")
        elif cmd =='/':
            shared["state"] = 2
            print("state 0 change to state 2")
    elif shared["state"] == 1:
        if cmd =='q':
            shared["state"] = 0
            print("state 1 change to state 0")
        elif cmd =='2' :
            shared["state"] = 2
            print("state 1 change to state 2")
        elif cmd == '?':
            print(extractor.params)
        else : extractor.set_params(cmd)
    elif shared["state"] == 2:
        if cmd == 'q':
            shared["state"] = 0
            print("state 2 change to state 0")
        elif cmd == '1':
            shared["state"] = 1
            print("state 2 change to state 1")
        elif cmd == '?':
            print(params)
        else : set_params(cmd)
    return cmd

if __name__ == "__main__":
    # --- 1. 設定啟動參數 ---
    parser = argparse.ArgumentParser(description="Maze Scanner")
    parser.add_argument("-i", "--image", type=str, help="指定靜態圖片的路徑 (若無則啟動相機)")
    parser.add_argument("-d", "--debug", action="store_true", help="開啟除錯視窗")
    parser.add_argument("-t", "--text", action="store_true", help="無視窗模式")
    args = parser.parse_args()

    # --- Initialize Class ---
    extractor = MazeGraphExtractor(maze_size=params["size"], wall_threshold=params["wall_threshold"], debug=args.debug)
    ball = BallDetector(maze_size = params["size"], debug=args.debug)
    shared = {"state": 0,"cmd": None}
    threading.Thread(target=cmd_input_loop, daemon=True).start()

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
            if not args.text: cv2.imshow("Original Image", frame)
            if not args.text: cv2.imshow("Final Warped Maze", warped_img)
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
        m = Maze()
        has_graph = False
        def mode(name, cmd):
            if shared["state"] == 0 and cmd == name:
                return True
            return False
        
        try:
            # 只有在相機模式才引入 picamera2，避免在一般電腦上報錯
            from picamera2 import Picamera2
            picam2 = Picamera2()
            picam2.start()
            print("🎥 相機已啟動。(按 's' 解析，按 'q' 離開)")
            arduino = ArduinoSerial(PORT, BAUD)
        except ImportError:
            print("❌ 錯誤：找不到 picamera2 模組。若是使用一般電腦，請加上 -i 參數指定圖片測試。")
            sys.exit(1)
            print(f"開啟 {PORT} @ {BAUD} baud ...")
        
        try:
            while True:
                # 1. 讀取序列埠
                msg = arduino.read()
                if msg:
                    print("Arduino:", msg)
                
                # 2. 更新相機與視窗
                raw_frame = picam2.capture_array()
                frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
                if not args.text: cv2.imshow("Camera Preview", frame)
                warped_img = None

                key = cv2.waitKey(1) & 0xFF
                if key == 27: # ESC Stop Camera  
                    break
                
                # 3. 處理終端機指令 (非阻塞)
                cmd = None
                while not cmd_queue.empty():
                    cmd = handle_cmd(cmd_queue.get(), shared, extractor)

                # 4. 模式控制 (結合鍵盤與終端機觸發)
                if key == ord("r") or cmd == 'r':
                    arduino.send("r")
                elif key == ord("j") or cmd == 'j':
                    arduino.send("j")
                elif key == ord("q") or cmd == 'q':
                    arduino.send("q")

                elif key == ord('m') or cmd == 'm':
                    with Timer():
                        warped_img, graph = extractor.process(frame)
                        print("\n🔍 掃描中...")
                        if graph is not None:
                            m.load_from_graph(graph)
                            if not args.text: cv2.imshow("Final Warped Maze", warped_img)
                            has_graph = True
                            print("Graph Loaded!")
                                        
                elif key == ord('p') or cmd == 'p':
                    if has_graph:
                        arduino.send('p')
                        time.sleep(0.1)
                        
                        end = params["endpoint"]
                        kp, ki, kd = params["kp"], params["ki"], params["kd"] 
                        prev_err_x, prev_err_y = 0.0, 0.0
                        integral_x, integral_y = 0.0, 0.0
                        
                        while True:
                            key = cv2.waitKey(1) & 0xFF
                            
                            # 檢查終端機是否發送中斷指令 (解決文字模式無法退出的問題)
                            if not cmd_queue.empty():
                                sub_cmd = cmd_queue.get()
                                if sub_cmd == 'q':
                                    break
                                    
                            if key == ord('q'):
                                break
                                
                            raw_frame = picam2.capture_array()
                            frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
                            warped_img = extractor.wrap(frame)
                            
                            if warped_img is None:
                                time.sleep(0.01) 
                                continue
                            
                            now = ball.find_ball(warped_img)
                            if now is None:
                                continue
                            
                            if now == end:
                                print("已抵達終點！")
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
                                
                                turn_ahead_x, turn_ahead_y = 0, 0
                                if len(path_nodes) >= 3:
                                    next_node = path_nodes[1]
                                    curr_dir_r = path_nodes[1].get_index()[0] - path_nodes[0].get_index()[0]
                                    curr_dir_c = path_nodes[1].get_index()[1] - path_nodes[0].get_index()[1]
                                    next_dir_r = path_nodes[2].get_index()[0] - path_nodes[1].get_index()[0]
                                    next_dir_c = path_nodes[2].get_index()[1] - path_nodes[1].get_index()[1]
                                    
                                    turn_ahead_x = next_dir_c * params["lookahead"] * cell_w
                                    turn_ahead_y = next_dir_r * params["lookahead"]  * cell_h

                                target_px_x += turn_ahead_x
                                target_px_y += turn_ahead_y
                                
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
                                
                                i= 1 
                                slow = False
                                while i < len(path_nodes)-1:
                                    if path_nodes[i].turn_on(path_nodes[i-1], path_nodes[i+1]):
                                        if path_nodes[i].is_t_junction() or path_nodes[i].is_cross():
                                            slow = True
                                        break
                                    i +=1
                                if slow:
                                    step = params["slowstep"]
                                else:
                                    step = params["highstep"]
                                    
                                if abs(output_x**2+output_y**2) < params["compensate"]:
                                    i = params["compensate"]
                                    if abs(output_x) > abs(output_y):
                                        output_x = i if output_x > 0 else -i
                                        output_y = 0
                                    else:
                                        output_y = i if output_y > 0 else -i
                                        output_x = 0

                                angle_x = +int(np.clip(output_x, -step, step))
                                angle_y = -int(np.clip(output_y, -step, step))
                                
                                cmd_str = f"X{angle_x:+d}Y{angle_y:+d}"
                                arduino.send_line(cmd_str)
                                if args.debug == True:
                                    print(f"output: ({output_x:.1f}, {output_y:.1f}), error: ({err_x:.1f}, {err_y:.1f}),I:({integral_x:.1f},{integral_x:.1f}) d:({deriv_x:.1f}, {deriv_y:.1f}), cmd:{cmd_str}")
                                time.sleep(params["delayPID"])
                                
                            except KeyError:
                                time.sleep(0.1)
  
                        arduino.send('q')

                elif key == ord('o') or cmd == 'o':
                    arduino.send('p')
                    angle_x = 5
                    angle_y = 5
                    cmd_str = f"X{angle_x:+d}Y{angle_y:+d}"
                    arduino.send_line(cmd_str)
                    
                elif key == ord('t') or cmd == 't':
                    arduino.send("t")
                
                elif key == ord('f') or cmd == 'f':
                    with Timer():
                        print("\n 掃描球的位置...")
                        warped_img, _ = extractor.process(frame)
                        if warped_img is None:
                            print(" 無法校正影像，請確認定位點可見")
                        else:
                            pos = ball.find_ball(warped_img)
                            print(f"球的位置：{pos}")
                
        finally:
            picam2.stop()
            cv2.destroyAllWindows()
            print("相機已安全關閉")
