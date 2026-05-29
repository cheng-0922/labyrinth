import csv
import logging
import math
from enum import IntEnum
from typing import List

import numpy as np
#import pandas

from node import Direction, Node 
from collections import deque

log = logging.getLogger(__name__)

class Action(IntEnum):
    ADVANCE = 1
    U_TURN = 2
    TURN_RIGHT = 3
    TURN_LEFT = 4
    HALT = 5

class Maze:
    def __init__(self):
        # 初始化為空，等待讀取檔案或載入 Graph
        self.nodes = []
        self.node_dict = dict()  # key: index (或座標), value: Node 物件

    def open(self, filepath: str):
        self.raw_data = pandas.read_csv(filepath).values
        self.nodes = []
        self.node_dict = dict()  
        
        for node_i in self.raw_data:
            new_n = Node(node_i[0])
            self.nodes.append(new_n)
            self.node_dict[node_i[0]] = new_n

        for node_i in self.raw_data:
            n = self.node_dict[node_i[0]]
            for i in [1,2,3,4]:
                if not pandas.isna(node_i[i]):
                    n.set_successor(self.node_dict[node_i[i]], i, node_i[i+4])

    def load_from_graph(self, adj_list: dict):
        """
        【新增】從 CV 萃取出來的 Tuple Adjacency List 載入迷宮
        """
        self.nodes = []
        self.node_dict = dict()

        # ==========================================
        # 階段 1: 把所有的 (r, c) 座標轉換成 Node 物件
        # ==========================================
        for coords in adj_list.keys():
            # 這裡直接用 tuple (r, c) 當作 Node 的 index
            # 如果你的 Node 不接受 tuple，可以用 f"{coords[0]}_{coords[1]}" 轉成字串
            new_n = Node(coords)
            self.nodes.append(new_n)
            self.node_dict[coords] = new_n

        # ==========================================
        # 階段 2: 判斷方位，並將 Node 互相連接
        # ==========================================
        for coords, neighbors in adj_list.items():
            current_node = self.node_dict[coords]
            r, c = coords

            for n_coords in neighbors:
                nr, nc = n_coords
                neighbor_node = self.node_dict[n_coords]

                # 透過座標的變化量 (dr, dc) 來推斷相對方向
                # 請依據你 node.py 中 Direction 的定義調整對應的數字
                # 假設: 1=北(North), 2=南(South), 3=西(West), 4=東(East)
                if nr < r:
                    direction = 1  # Row 減少，代表往「上 (北)」
                elif nr > r:
                    direction = 2  # Row 增加，代表往「下 (南)」
                elif nc < c:
                    direction = 3  # Col 減少，代表往「左 (西)」
                elif nc > c:
                    direction = 4  # Col 增加，代表往「右 (東)」
                else:
                    continue

                # 設定相鄰節點 (格狀迷宮預設距離長度為 1)
                # 若你使用的是 Enum，可能要寫成 Direction.NORTH 等
                current_node.set_successor(neighbor_node, direction, 1)
                
        print(f"✅ 成功將 {len(self.nodes)} 個網格節點轉換為 OOP Node 物件並建立連線！")


    def get_start_point(self):
        start_index =int( input("enter start point") )
        return self.node_dict[start_index]

    def get_node_dict(self):
        return self.node_dict

    def BFS(self, node: Node):
        visited=[]
        parent=dict()
        # use Node as key to store in visitd,parent 
        if node not in self.nodes:
            return None

        queue = deque([node])
        visited.append(node)
        # nodes[start_node]['visited'] = True

        while queue:
            u = queue.popleft()
            for i in u.get_successors():
                v = i[0]
                if v in self.nodes and v not in visited: #and not nodes[v]['visited']
                    visited.append(v)
                    parent[v]=u
                    queue.append(v)
    
    

    def BFS_2(self, node_from: Node, node_to: Node):
        # TODO : similar to BFS but with fixed start point and end point
        # Tips : return a sequence of nodes of the shortest path
        visited=[]
        parent=dict()
        # use Node as key to store in visitd,parent 
        if node_from not in self.nodes:
            return None

        queue = deque([node_from])
        visited.append(node_from)
        # nodes[start_node]['visited'] = True

        while queue:
            u = queue.popleft()
            for i in u.get_successors():
                v = i[0]
                if v in self.nodes and v not in visited: #and not nodes[v]['visited']
                    visited.append(v)
                    parent[v]=u
                    queue.append(v)

        path=[]
        v=node_to

        while(v in self.nodes):
            path.append(v)
            if v==node_from: break
            v=parent[v]
        path = path[::-1]

        return path
    

    def getAction(self, car_dir, node_from: Node, node_to: Node):
        # TODO : get the car action
        # Tips : return an action and the next direction of the car if the node_to is the Successor of node_to
        # If not, print error message and return 0
        future_dir= node_from.get_direction(node_to)
        if future_dir==0:
            return None
        
        
        if ( car_dir==1 and future_dir==2 ) or (car_dir==3 and future_dir ==4) or \
            ( car_dir==2 and future_dir==1) or ( car_dir==4 and future_dir==3 ):
            return Action(2)
        elif ( car_dir==1 and future_dir==3) or ( car_dir==2 and future_dir==4 ) or \
            ( car_dir==3 and future_dir==2 ) or ( car_dir==4 and future_dir==1 ):
            return Action(4)
        elif ( car_dir==1 and future_dir==4 ) or ( car_dir==2 and future_dir==3 ) or\
            ( car_dir==3 and future_dir==1 ) or ( car_dir==4 and future_dir==2 ):
            return Action(3)
        elif car_dir==future_dir:
            return Action(1)
        else:
            return 0
        

    def getActions(self, nodes: List[Node]):
        # TODO : given a sequence of nodes, return the corresponding action sequence
        # Tips : iterate through the nodes and use getAction() in each iteration
        acts=[]
        curr_dir=0
        
        for i in range(1,len(nodes)):
            target_node = nodes[i]
            prev_node = nodes[i-1]

            if i==1:
                acts.append(Action(1))
            else:
                acts.append(self.getAction(curr_dir,prev_node,target_node))
            curr_dir = prev_node.get_direction(target_node)

        return acts

    def actions_to_str(self, actions):
        # cmds should be a string sequence like "fbrl....", use it as the input of BFS checklist #1
        cmd = "wsdax"
        cmds = ""
        for action in actions:
            cmds += cmd[action - 1]
        # log.info(cmds)
        cmds += 'sx'
        return cmds


    def strategy_i(self, node: Node, max_step):
        result = [node]
        current = node
        
        list_treasure = [n for n in self.nodes if len(n.get_successors()) == 1]
        visited_treasure = set()
        visited_treasure.add(node)
        total_score = 0
        
        while len(visited_treasure) < len(list_treasure):
            best_target = None
            best_cp = -1.0
            best_sub_path = []
            
            for target in list_treasure:
                if target == current or target in visited_treasure:
                    continue
                
                path = self.BFS_2(current, target)
                if not path: continue
                
                steps = len(path) - 1
                if steps <= max_step:
                    score = self.point(node, target) * 10
                    cp = score / steps if steps > 0 else 0
                    if cp > best_cp:
                        best_cp = cp
                        best_target = target
                        best_sub_path = path
            
            if not best_target:
                shortest_dist = float('inf')
                for target in list_treasure:
                    if target == current or target in visited_treasure:
                        continue
                    
                    path = self.BFS_2(current, target)
                    if not path: continue
                    
                    steps = len(path) - 1
                    if steps < shortest_dist:
                        shortest_dist = steps
                        best_target = target
                        best_sub_path = path
            
            if not best_target:
                break
                
            result.extend(best_sub_path[1:])
            total_score += self.point(current, best_target)*10
            current = best_target
            visited_treasure.add(best_target)
     
        return result
    def strategy(self, node:Node):
        best = float('inf')
        for i in range(20):
            path = self.strategy_i(node, i)   # Node list
            actions = self.getActions(path)   # Action list
            lens = sum(1 for a in self.actions_to_str(actions) if a == 'a' or a == 'd')
            if (lens<best):
                result = path
                best = lens


        # print(f"Total score: {total_score}")        
        return result
    def strategy3(self, node:Node):
        best = float('inf')
        for i in range(20):
            path= self.strategy_i(node, i) 
            lens = len(path)

            if (lens<best):
                result = path
                best = lens
   
        return result


    def strategy_2(self, node_from: Node, node_to: Node):
        return self.BFS_2(node_from, node_to)
    
    def point(self, start: Node, node: Node):
        nodelist = self.BFS_2(start, node)
        ns = 0
        ew = 0
        node_prev = nodelist[0]
        for node in nodelist:
            i = node.get_direction(node_prev)
            match(i):
                case 1 : ns+=1
                case 2 : ns-=1
                case 3 : ew+=1
                case 4 : ew-=1
                case _ : pass
            node_prev = node
        return abs(ns)+abs(ew)
        
    
    def testBFS(self, node_from:int):
        return self.BFS(self.node_dict[node_from])

    def testBFS2(self, node_from:int, node_to):
        return self.BFS_2(self.node_dict[node_from],self.node_dict[node_to])
    

FILE_MAZE="data/big_maze_114.csv"
def checkstates(m:Maze, start:int,  file = FILE_MAZE):
    m = Maze(file)
    nodelist=m.strategy(m.node_dict[start])
    acts = m.getActions(nodelist)
    print(f"min length:{len(acts)}")
    print(sum([1 for i in m.actions_to_str(acts) if i == 'w']))

    print(f'route:{m.actions_to_str(acts)}')
    for node in nodelist:
        print(f'node {int(node.get_index())}')

def get_dict(m:Maze, start:int):
    point_dict = dict()
    route_dict = dict()
    avg_dict = dict()
    for dist in m.nodes:
        if dist.get_index() == start: continue
        if len(dist.get_successors())==1 :
            nl = m.BFS_2(m.node_dict[start], dist)
            route_dict[int(dist.get_index())]= len(nl)-1
            point_dict[int(dist.get_index())]= m.point(m.node_dict[start],dist)
            avg_dict [int(dist.get_index())]=  (m.point(m.node_dict[start],dist)) /(len(nl)-1) 
    print(point_dict)
    print(route_dict)
    print(avg_dict)
