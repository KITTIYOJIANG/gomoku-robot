from __future__ import annotations
from enum import IntEnum
from typing import List, Optional, Tuple

BOARD_SIZE = 15  # 标准 15x15 五子棋

Coord = Tuple[int, int]


class Stone(IntEnum):
    EMPTY = 0
    BLACK = 1  # 黑棋先手
    WHITE = 2  # 白棋后手


class GomokuBoard:
    """棋盘状态 + 规则判断"""

    def __init__(self, size: int = BOARD_SIZE) -> None:
        self.size = size
        self.grid: List[List[Stone]] = [
            [Stone.EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.current_player: Stone = Stone.BLACK
        self.last_move: Optional[Coord] = None
        self.move_count: int = 0

    # -------- 基本工具函数 --------
    def is_on_board(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def is_valid_move(self, row: int, col: int) -> bool:
        if not self.is_on_board(row, col):
            return False
        return self.grid[row][col] == Stone.EMPTY

    # -------- 落子 & 轮换 --------
    def place_stone(self, row: int, col: int) -> bool:
        """
        在 (row, col) 为当前玩家落子。
        返回 True 表示成功，False 表示非法落子。
        """
        if not self.is_valid_move(row, col):
            return False

        self.grid[row][col] = self.current_player
        self.last_move = (row, col)
        self.move_count += 1

        # 轮到另一方
        self.current_player = (
            Stone.BLACK if self.current_player == Stone.WHITE else Stone.WHITE
        )
        return True

    # -------- 胜负判断 --------
    def check_winner(self, coord: Optional[Coord] = None) -> Optional[Stone]:
        """
        判断当前棋盘是否有人获胜。
        默认基于最后一步 coord（如果 None 就用 self.last_move）。

        返回：
            Stone.BLACK / Stone.WHITE 获胜；或者 None（未分胜负）
        """
        if coord is None:
            coord = self.last_move
        if coord is None:
            return None

        row, col = coord
        player = self.grid[row][col]
        if player == Stone.EMPTY:
            return None

        # 4 个方向：水平、垂直、主对角线、副对角线
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1

            # 正方向
            r, c = row + dr, col + dc
            while self.is_on_board(r, c) and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc

            # 反方向
            r, c = row - dr, col - dc
            while self.is_on_board(r, c) and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= 5:
                return player

        return None

    def is_full(self) -> bool:
        return self.move_count >= self.size * self.size

    # -------- 打印 / 可视化（命令行用） --------
    def __str__(self) -> str:
        """
        把棋盘转成字符串：用于命令行显示。
        列用 A-O，行用 1-15。
        """
        # 列标题
        header = "   " + " ".join(chr(ord("A") + i) for i in range(self.size))

        lines = [header]
        for r in range(self.size):
            # 行号右对齐
            row_label = f"{r+1:2d}"
            row_cells = []
            for c in range(self.size):
                stone = self.grid[r][c]
                if stone == Stone.EMPTY:
                    ch = "."
                elif stone == Stone.BLACK:
                    ch = "●"  # 如果你的终端不支持，可以改成 'X'
                else:
                    ch = "○"  # 或改成 'O'
                row_cells.append(ch)
            lines.append(f"{row_label} " + " ".join(row_cells))
        return "\n".join(lines)
