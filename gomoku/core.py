from __future__ import annotations

from enum import IntEnum
from typing import List, Optional, Tuple


BOARD_SIZE = 15
Coord = Tuple[int, int]


class Stone(IntEnum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2


class GomokuBoard:
    """Board state and basic Gomoku rules."""

    def __init__(self, size: int = BOARD_SIZE) -> None:
        self.size = size
        self.grid: List[List[Stone]] = [
            [Stone.EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.current_player: Stone = Stone.BLACK
        self.last_move: Optional[Coord] = None
        self.move_count: int = 0

    def reset(self) -> None:
        self.grid = [[Stone.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = Stone.BLACK
        self.last_move = None
        self.move_count = 0

    def is_on_board(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def is_valid_move(self, row: int, col: int) -> bool:
        return self.is_on_board(row, col) and self.grid[row][col] == Stone.EMPTY

    def place_stone(self, row: int, col: int) -> bool:
        if not self.is_valid_move(row, col):
            return False

        self.grid[row][col] = self.current_player
        self.last_move = (row, col)
        self.move_count += 1
        self.current_player = Stone.BLACK if self.current_player == Stone.WHITE else Stone.WHITE
        return True

    def check_winner(self, coord: Optional[Coord] = None) -> Optional[Stone]:
        if coord is None:
            coord = self.last_move
        if coord is None:
            return None

        row, col = coord
        if not self.is_on_board(row, col):
            return None

        player = self.grid[row][col]
        if player == Stone.EMPTY:
            return None

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1

            r, c = row + dr, col + dc
            while self.is_on_board(r, c) and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc

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

    def __str__(self) -> str:
        header = "   " + " ".join(chr(ord("A") + i) for i in range(self.size))
        lines = [header]
        for r in range(self.size):
            row_cells = []
            for c in range(self.size):
                stone = self.grid[r][c]
                if stone == Stone.EMPTY:
                    ch = "."
                elif stone == Stone.BLACK:
                    ch = "X"
                else:
                    ch = "O"
                row_cells.append(ch)
            lines.append(f"{r + 1:2d} " + " ".join(row_cells))
        return "\n".join(lines)
