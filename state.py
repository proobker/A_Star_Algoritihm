from typing import List, Tuple, Optional
from matplotlib.animation import FuncAnimation

class State:
    def __init__(self, speed_slider):
        self.anim: Optional[FuncAnimation] = None
        self.exp_scatter = None
        self.path_line = None
        self.travel_dot = None
        self.expanded_rc: List[Tuple[int,int]] = []
        self.path_rc: List[Tuple[int,int]] = []
        self.phase = 'idle'
        self.exp_index = 0
        self.path_index = 0
        self.running = False
        self.expand_step = int(speed_slider.val)
        self.path_step = max(1, int(speed_slider.val))
