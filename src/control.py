import numpy as np
import cv2
import time
from collections import deque

class BallStateEstimator:
    """
    狀態估估器：估算球的即時位置與速度 (vx, vy)，並補償系統與相機延遲。
    如果偵測掉幀，使用上一次的狀態進行慣性外推。
    """
    def __init__(self, buffer_len=5, friction=0.98):
        self.obs_buffer = deque(maxlen=buffer_len)
        self.friction = friction
        self.x, self.y = 0.0, 0.0
        self.vx, self.vy = 0.0, 0.0
        self.last_time = time.perf_counter()

    def update(self, obs_pos, timestamp):
        """
        更新觀測值並估算最新狀態。
        obs_pos: (cx, cy) 像素座標，若無偵測到則傳入 None
        timestamp: 當前時間點 (秒)
        """
        dt = timestamp - self.last_time
        self.last_time = timestamp
        
        # 邊界保護，避免極端 dt
        if dt <= 0:
            dt = 0.001

        if obs_pos is None:
            # 掉幀補償：依照摩擦力與速度進行預測外推
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vx *= self.friction
            self.vy *= self.friction
            return self.x, self.y, self.vx, self.vy

        self.obs_buffer.append((obs_pos[0], obs_pos[1], timestamp))
        
        if len(self.obs_buffer) < 2:
            self.x, self.y = obs_pos
            self.vx, self.vy = 0.0, 0.0
        else:
            # 計算速度
            x_prev, y_prev, t_prev = self.obs_buffer[-2]
            x_curr, y_curr, t_curr = self.obs_buffer[-1]
            raw_dt = t_curr - t_prev
            
            if raw_dt > 0:
                raw_vx = (x_curr - x_prev) / raw_dt
                raw_vy = (y_curr - y_prev) / raw_dt
                
                # 一階低通濾波 (Alpha Filter)，濾除高頻視覺雜訊
                alpha = 0.5
                self.vx = alpha * raw_vx + (1 - alpha) * self.vx
                self.vy = alpha * raw_vy + (1 - alpha) * self.vy
                
            self.x, self.y = x_curr, y_curr
            
        return self.x, self.y, self.vx, self.vy


class PredictiveController:
    """
    預測型控制器：結合最小閉環 PID、軌跡預測、安全邊距膨脹與錯誤路徑防範。
    """
    def __init__(self, kp=0.15, ki=0.0, kd=0.03, max_tilt=15, accel_gain=120.0, friction=0.95):
        # PID 參數
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_tilt = max_tilt
        
        # 物理模擬參數
        self.accel_gain = accel_gain  # 傾角轉換為加速度的比例常數 (pixels/s^2)
        self.friction = friction      # 物理模擬中的摩擦阻尼
        
        # 狀態估測器
        self.estimator = BallStateEstimator(friction=self.friction)
        
        # PID 積分項快取
        self.integral_x = 0.0
        self.integral_y = 0.0
        
    def reset(self):
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.estimator = BallStateEstimator(friction=self.friction)

    
    def get_control_command(self, ball_px, timestamp, path_nodes, warped_img, thresh_img, debug_draw=False):
        """
        取得最終的控制指令。
        """
        # 1. 狀態更新
        state_x, state_y, vx, vy = self.estimator.update(ball_px, timestamp)
        
        if len(path_nodes) < 2:
            return "X+00Y+00", None
            
        # 2. 計算網格與目標點
        h, w = warped_img.shape[:2]
        cell_w, cell_h = w / 9.0, h / 9.0
        
        # 決定當前球位於哪個網格
        current_cell = (max(0, min(int(state_y / cell_h), 8)), max(0, min(int(state_x / cell_w), 8)))
        
        # --- 3. 路徑前瞻 (Lookahead Waypoint) 修正 ---
        # 不要永遠只看 next_cell，如果還有下下一格，進行插值以實現「提早入彎」
        if len(path_nodes) >= 3:
            cell_next = path_nodes[1].get_index()
            cell_future = path_nodes[2].get_index()
            # 結合下一格與下下一格：40% 權重給下一格中心，60% 給下下一格中心 (實現提早過彎切線)
            target_col = 0.4 * cell_next[1] + 0.6 * cell_future[1]
            target_row = 0.4 * cell_next[0] + 0.6 * cell_future[0]
        else:
            cell_next = path_nodes[1].get_index()
            target_col = cell_next[1]
            target_row = cell_next[0]
            
        # 目標點像素位置
        target_px_x = (target_col + 0.5) * cell_w
        target_px_y = (target_row + 0.5) * cell_h
        

        err_x = target_px_x - state_x
        err_y = target_px_y - state_y
        
        self.integral_x = np.clip(self.integral_x + err_x, -50, 50)
        self.integral_y = np.clip(self.integral_y + err_y, -50, 50)
        
        # 直接使用狀態估測速度為微分項，減少微分高頻噪聲
        deriv_x = -vx
        deriv_y = -vy
        
        output_x = self.kp * err_x + self.ki * self.integral_x + self.kd * deriv_x
        output_y = self.kp * err_y + self.ki * self.integral_y + self.kd * deriv_y
        
        nominal_angle_x = -int(np.clip(output_x, -self.max_tilt, self.max_tilt))
        nominal_angle_y = int(np.clip(output_y, -self.max_tilt, self.max_tilt))
        
        final_angle_x = nominal_angle_x
        final_angle_y = nominal_angle_y
        
        # 6. Commit Rule 與煞車避險
        # 計算前進速度與煞車距離
        speed = np.sqrt(vx**2 + vy**2)
        # 煞車加速度估計 (最大傾角時)
        a_max = self.accel_gain * self.max_tilt
        # 保守估計：煞車距離乘以 2.0，補償相機、馬達與滾動延遲
        braking_distance = ((speed ** 2) / (2 * a_max)) * 2.0 if a_max > 0 else 0
        
        # 計算球到目標 waypoint 的像素距離
        dist_to_target = np.sqrt((target_px_x - state_x)**2 + (target_px_y - state_y)**2)

        
        # 6. 執行煞車條件覆蓋
        if dist_to_target < braking_distance + cell_w * 0.2 and speed > 5:
            final_angle_x = int(np.clip((vx / speed) * self.max_tilt, -self.max_tilt, self.max_tilt))
            final_angle_y = -int(np.clip((vy / speed) * self.max_tilt, -self.max_tilt, self.max_tilt))

        # 輸出格式化指令，確保正負號顯示
        cmd_str = f"X{final_angle_x:+d}Y{final_angle_y:+d}"

        # 7. 除錯資訊 (移除已刪除的 simulate_trajectory 方法呼叫)
        debug_info = None
        if debug_draw:
            debug_info = {
                "state": (state_x, state_y, vx, vy),
                "target": (target_px_x, target_px_y),
                "braking_triggered": (dist_to_target < braking_distance + cell_w * 0.2 and speed > 5)
            }
        return cmd_str, debug_info
