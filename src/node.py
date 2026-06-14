from enum import IntEnum


# You can get the enumeration based on integer value, or make comparison
# ex: d = Direction(1), then d would be Direction.NORTH
# ex: print(Direction.SOUTH == 1) should return False
class Direction(IntEnum):
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4


# Construct class Node and its member functions
# You may add more member functions to meet your needs
class Node:
    def __init__(self, index=None):
        self.index = index
        # store successor as (Node, direction to node, distance)
        self.successors = []

    def get_index(self):
        return self.index

    def get_successors(self):
        return self.successors

    def set_successor(self, successor, direction, length=1):
        self.successors.append((successor, Direction(direction), int(length)))
        # print(f"For Node {self.index}, a successor {self.successors[-1]} is set.")
        return

    def get_direction(self, node):
        # TODO : if node is adjacent to the present node, return the direction of node from the present node
        # For example, if the direction of node from the present node is EAST, then return Direction.EAST = 4
        # However, if node is not adjacent to the present node, print error message and return 0
        for s in self.successors:
            # print(s)
            if(node.index==s[0].index):
                return Direction(s[1])
        
        # print(f"Not a successor of {self.index}")
        return 0

    def is_successor(self, node):
        for succ in self.successors:
            if succ[0] == node:
                return True
        return False

    def is_t_junction(self):
        """
        判斷是否為 T 字型路口（3 個出口）
        T 字型路口：4 邊中有 3 邊是出口，1 邊是牆壁
        """
        return len(self.successors) == 3

    def is_corner(self):
        """
        判斷是否為轉角（2 個出口）
        """
        return len(self.successors) == 2

    def is_cross(self):
        """
        判斷是否為十字型路口（4 個出口）
        """
        return len(self.successors) == 4

    def get_exit_count(self):
        """
        取得出口數量
        """
        return len(self.successors)

    def printparam(self):
        for s in self.successors:
            print(f"node.index:{self.index}| successor: {s[0].index},direction = {Direction(s[1])},d={s[2]}")

    def turn_on(self, prev, next):
        if prev.get_direction(self) != self.get_direction(next):
            return True
        return False