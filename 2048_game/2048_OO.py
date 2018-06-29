# -*- coding:utf-8 -*-

import curses
import random
from itertools import chain

"""
2048游戏：面向对象形式实现
运行方式: python 2048_OO.py，不能使用pycharm运行，因为需要打开终端显示游戏棋盘
"""


class Action(object):
    UP = 'up'
    LEFT = 'left'
    DOWN = 'down'
    RIGHT = 'right'
    RESTART = 'restart'
    EXIT = 'exit'

    # 游戏操作，上 下 左 右 重置 退出
    actions = [UP, LEFT, DOWN, RIGHT, RESTART, EXIT]
    letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
    actions_dict = dict(zip(letter_codes, actions * 2))

    def __init__(self, stdscr):
        self.stdscr = stdscr

    # 获取用户输入
    def get(self):
        char = 'N'
        while char not in self.actions_dict:
            char = self.stdscr.getch()
        return self.actions_dict[char]


class Grid(object):
    def __init__(self, size):
        self.size = size
        self.cells = None
        self.reset()

    def reset(self):
        # 重置游戏，在棋盘中填入最开始的两个数
        self.cells = [[0 for i in range(self.size)] for j in range(self.size)]
        self.add_random_item()
        self.add_random_item()

    def add_random_item(self):
        #  在棋盘上一个空位置上产生一个新的数，2或者4
        empty_cells = [(i, j) for i in range(self.size)
                         for j in range(self.size) if self.cells[i][j] == 0]
        (i, j) = random.choice(empty_cells)
        self.cells[i][j] = 4 if random.randrange(100) > 89 else 2

    # 矩阵转置(顺时针旋转90度)，游戏棋盘用一个矩阵表示
    #  0  2  0  2              0  0  0  0
    #  0  2  0  2    ---->     2  2  2  2
    #  0  2  0  2              0  0  0  0
    #  0  2  0  2              2  2  2  2
    def transpose(self):
        self.cells = [list(row) for row in zip(*self.cells)]

    # 矩阵翻转，每一行逆转
    #  0  2  0  2           2  0  2  0
    #  0  2  0  2  ----->   2  0  2  0
    #  2  0  2  0           0  2  0  2
    #  2  0  2  0           0  2  0  2
    def invert(self):
        self.cells = [row[::-1] for row in self.cells]

    # 向一个方向移动游戏棋盘时，首先将存在数字的格子挤到一块
    # 然后将相邻且数字相同的格子合并，其中一个格子数值翻倍，另外一个格子置为0
    # 最后再次把有数字的格子挤到一块
    # 以一行向左移动为例：4 4 0 2 --> 4 4 2 0 --> 8 0 2 0 --> 8 2 0 0
    @staticmethod
    def move_row_left(row):
        # 一行向左移动
        def tighten(row):
            # 把非零的格子挤到一起
            new_row = [i for i in row if i != 0]
            new_row += [0 for i in range(len(row) - len(new_row))]
            return new_row

        def merge(row):
            # 相邻且数值相同的格子合并
            pair = False
            new_row = []
            for i in range(len(row)):
                if pair:
                    new_row.append(0)
                    pair = False
                else:
                    if i+1 < len(row) and row[i] == row[i+1] and row[i] != 0:
                        pair = True
                        new_row.append(2 * row[i])
                    else:
                        new_row.append(row[i])
            assert len(new_row) == len(row)
            return new_row

        # 先挤到一块再合并再挤到一块
        return tighten(merge(tighten(row)))

    def move_left(self):
        self.cells = [self.move_row_left(row) for row in self.cells]

    def move_right(self):
        self.invert()
        self.move_left()
        self.invert()

    def move_up(self):
        self.transpose()
        self.move_left()
        self.transpose()

    def move_down(self):
        self.transpose()
        self.move_right()
        self.transpose()

    # 判断是否能向一个方向移动
    @staticmethod
    def row_can_move_left(row):
        def change(i):
            if row[i] == 0 and row[i + 1] != 0:  # 0 2 4 8 可以向左移动
                return True
            if row[i] != 0 and row[i + 1] == row[i]:  # 2 2 4 8 可以向左移动
                return True
            return False

        return any(change(i) for i in range(len(row) - 1))

    def can_move_left(self):
        return any(self.row_can_move_left(row) for row in self.cells)

    def can_move_right(self):
        self.invert()
        can = self.can_move_left()
        self.invert()
        return can

    def can_move_up(self):
        self.transpose()
        can = self.can_move_left()
        self.transpose()
        return can

    def can_move_down(self):
        self.transpose()
        can = self.can_move_right()
        self.transpose()
        return can


class Screen(object):
    help_string1 = '(W)Up (S)Down (A)Left (D)Right'
    help_string2 = '    (R)Restart (Q)Exit'
    over_string = '     GAME OVER'
    win_string = '     YOU WIN!'

    def __init__(self, screen=None, grid=None, score=0, best_score=0,
                 over=False, win=False):
        self.grid = grid
        self.score = score
        self.over = over
        self.win = win
        self.screen = screen
        self.counter = 0

    def cast(self, string):
        self.screen.addstr(string + '\n')

    def draw_row(self, row):
        # {: ^5}  :后面的空格表示使用空格填充 ^表示居中对齐 5表示总长度为5，左对齐使用< 右对齐使用>
        # '{: ^5}'.format(23) 输出 ' 23  '
        self.cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

    def draw(self):
        self.screen.clear()
        self.cast('SCORE: ' + str(self.score))
        for row in self.grid.cells:
            self.cast('+------' * self.grid.size + '+')
            self.draw_row(row)
        self.cast('+------' * self.grid.size + '+')

        if self.win:
            self.cast(self.win_string)
        else:
            if self.over:
                self.cast(self.over_string)
            else:
                self.cast(self.help_string1)
        self.cast(self.help_string2)


class GameManager(object):
    def __init__(self, size=4, win_num=2048):
        self.size = size
        self.win_num = win_num
        self.reset()

    def __call__(self, stdscr):
        curses.use_default_colors()
        self.stdscr = stdscr
        self.action = Action(stdscr)
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()

    def reset(self):
        self.state = 'init'
        self.win = False
        self.over = False
        self.score = 0
        self.grid = Grid(self.size)
        self.grid.reset()

    @property
    def screen(self):
        return Screen(screen=self.stdscr, score=self.score, grid=self.grid,
                      win=self.win, over=self.over)

    def can_move(self, direction):
        return getattr(self.grid, 'can_move_' + direction)

    def move(self, direction):
        if self.can_move(direction):
            getattr(self.grid, 'move_' + direction)()
            self.grid.add_random_item()
            return True
        else:
            return False

    @property
    def is_win(self):
        # 判断胜利：棋盘中存在数值大于等于目标分的格子
        self.win = max(chain(*self.grid.cells)) >= self.win_num
        return self.win

    @property
    def is_over(self):
        # 判断失败：棋盘不能向任何方向移动
        self.over = not any(self.can_move(move) for move in self.action.actions)
        return self.over

    def state_init(self):
        self.reset()
        return 'game'

    def state_game(self):
        self.screen.draw()
        action = self.action.get()
        if action == Action.RESTART:
            return 'init'
        if action == Action.EXIT:
            return 'exit'
        if self.move(action):
            if self.is_win:
                return 'win'
            if self.is_over:
                return 'over'
        return 'game'

    def _restart_or_exit(self):
        self.screen.draw()
        return 'init' if self.action.get() == Action.RESTART else 'exit'

    def state_win(self):
        return self._restart_or_exit()

    def state_over(self):
        return self._restart_or_exit()


if __name__ == '__main__':
    curses.wrapper(GameManager())
