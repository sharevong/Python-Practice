# -*- coding:utf-8 -*-

import curses
from random import randrange, choice
from collections import defaultdict

"""
2048游戏
运行方式: python 2048.py，不能使用pycharm运行，因为需要打开终端显示游戏棋盘
"""


# 游戏操作，上 下 左 右 重置 退出
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
actions_dict = dict(zip(letter_codes, actions * 2))


# 获取用户输入
def get_user_action(keyboard):
    char = 'N'
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]


# 矩阵转置(顺时针旋转90度)，游戏棋盘用一个矩阵表示
#  0  2  0  2              0  0  0  0
#  0  2  0  2    ---->     2  2  2  2
#  0  2  0  2              0  0  0  0
#  0  2  0  2              2  2  2  2
def transpose(field):
    return [list(row) for row in zip(*field)]


# 矩阵翻转，每一行逆转
#  0  2  0  2           2  0  2  0
#  0  2  0  2  ----->   2  0  2  0
#  2  0  2  0           0  2  0  2
#  2  0  2  0           0  2  0  2
def invert(field):
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.field = list()   #  表示游戏棋盘
        self.height = height  #  高度
        self.width = width    #  宽度
        self.win_value = win  #  赢时需要达到的数值
        self.score = 0        #  本轮游戏分数，每发生一次合并，分数加上合并之和
        self.highscore = 0    #  游戏最高分
        self.reset()

    def reset(self):
        # 重置游戏，在棋盘中填入最开始的两个数
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def spawn(self):
        #  在棋盘上一个空位置上产生一个新的数，2或者4
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.width)
                         for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    def move_is_possible(self, direction):
        # 判断是否能向一个方向移动
        def row_is_left_movable(row):
            def change(i):
                if row[i] == 0 and row[i+1] != 0:  # 0 2 4 8 可以向左移动
                    return True
                if row[i] != 0 and row[i+1] == row[i]:  # 2 2 4 8 可以向左移动
                    return True
                return False
            return any(change(i) for i in range(len(row)-1))

        # 通过棋盘的转置和翻转，将左方向应用到四个方向
        check = dict()
        check['Left'] = lambda field: any(row_is_left_movable(row) for row in field)
        check['Right'] = lambda field: check['Left'](invert(field))
        check['Up'] = lambda field: check['Left'](transpose(field))
        check['Down'] = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

    def move(self, direction):
        # 向一个方向移动游戏棋盘时，首先将存在数字的格子挤到一块
        # 然后将相邻且数字相同的格子合并，其中一个格子数值翻倍，另外一个格子置为0
        # 最后再次把有数字的格子挤到一块
        # 以一行向左移动为例：4 4 0 2 --> 4 4 2 0 --> 8 0 2 0 --> 8 2 0 0
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
                            self.score += 2 * row[i]
                            new_row.append(2 * row[i])
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row

            # 先挤到一块再合并再挤到一块
            return tighten(merge(tighten(row)))

        # 通过棋盘的转置和翻转，将向左方向的移动应用到其他方向
        moves = dict()
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()  # 移动完成后，在棋盘上生成一个新的数
                return True
            else:
                return False

    def is_win(self):
        # 判断胜利：棋盘中存在数值大于等于目标分的格子
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        # 判断失败：棋盘不能向任何方向移动
        return not any(self.move_is_possible(move) for move in actions)

    def draw(self, screen):
        # 绘制游戏界面
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '    (R)Restart (Q)Exit'
        gameover_string = '     GAME OVER'
        win_string = '      YOU WIN!'

        def cast(string):
            screen.addstr(string + '\n')

        def draw_hor_separator():
            line = '+' + ('+------' * self.width + '+')[1:]
            cast(line)

        def draw_row(row):
            # {: ^5}  :后面的空格表示使用空格填充 ^表示居中对齐 5表示总长度为5，左对齐使用< 右对齐使用>
            # '{: ^5}'.format(23) 输出 ' 23  '
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))
        for row in self.field:
            draw_hor_separator()
            draw_row(row)
        draw_hor_separator()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


def main(stdscr):
    def init():
        # 重置游戏棋盘
        game_field.reset()
        return 'Game'

    def not_game(state):
        # 绘制GameOver 或者 Win的界面
        game_field.draw(stdscr)
        # 读取用户输入，判断重启或者结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda: state)  # 无输入时，保持当前状态
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]

    def game():
        # 绘制游戏界面
        game_field.draw(stdscr)
        action = get_user_action(stdscr)
        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    game_field = GameField(win=32)

    state_actions = {
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }
    curses.use_default_colors()

    state = 'Init'
    while state != 'Exit':
        state = state_actions[state]()


curses.wrapper(main)
