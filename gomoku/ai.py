from __future__ import annotations
import random
from typing import List, Optional, Tuple

from .core import GomokuBoard, Stone, Coord


class RandomAI:
    """最简单版：随机选择一个合法落点"""

    def __init__(self, stone: Stone) -> None:
        self.stone = stone

    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        legal_moves: List[Coord] = [
            (r, c)
            for r in range(board.size)
            for c in range(board.size)
            if board.is_valid_move(r, c)
        ]
        if not legal_moves:
            return None
        return random.choice(legal_moves)


# 下面是为以后“进阶 AI”预留的骨架：
class HeuristicAI:
    """
    预留：基于评分函数 + 搜索的 AI 骨架。
    现在先让它调用 RandomAI，后面你可以逐步替换 select_move 里的逻辑。
    """

    def __init__(self, stone: Stone, max_depth: int = 2) -> None:
        self.stone = stone
        self.max_depth = max_depth
        self._fallback = RandomAI(stone)

    def evaluate_board(self, board: GomokuBoard, player: Stone) -> int:
        """
        评分函数（TODO：你后面在这里实现“活三、活四、冲四”等模式评分）
        现在先返回 0，当成占位。
        """
        return 0

    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        """
        目前先直接用 RandomAI，
        后面你可以改成：搜索 + 调用 evaluate_board。
        """
        return self._fallback.select_move(board)
