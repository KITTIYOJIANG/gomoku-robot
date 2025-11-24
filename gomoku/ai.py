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


class HeuristicAI:
    """
    有点智商的五子棋 AI：
    1. 先看有没有一步直接获胜的棋；
    2. 再看哪里是必须堵住对手立刻获胜的点；
    3. 否则，在“棋子附近”的候选点里，模拟每一步，选评分最高的那一步。
    评分通过简单模式统计（连续子越多分越高，同时尽量压制对手）。
    """

    # 按连续子数量给的基础分数（只区分1~5连）
    SCORES = {
        1: 10,
        2: 100,
        3: 1000,
        4: 10000,
        5: 1000000,
    }

    def __init__(self, stone: Stone, search_radius: int = 2) -> None:
        self.stone = stone
        # 只在已有棋子附近 search_radius 范围内考虑落点，减少计算量
        self.search_radius = search_radius

    # ---------- 对外主入口 ----------
    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        # 候选点：离现有棋子不远的位置
        candidates = self._get_candidate_moves(board)
        if not candidates:
            return None

        # 1. 如果我有“直接赢”的点，立刻下
        for move in candidates:
            if self._is_winning_move(board, move, self.stone):
                return move

        # 2. 如果对手下一步能赢，优先堵
        opponent = self._opponent(self.stone)
        for move in candidates:
            if self._is_winning_move(board, move, opponent):
                return move

        # 3. 否则，对每个候选点做一次模拟，算启发式评分
        best_score = -10**18
        best_moves: List[Coord] = []

        for move in candidates:
            score = self._evaluate_move(board, move, self.stone)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # 多个同分的话，随机挑一个，避免太机械
        return random.choice(best_moves)

    # ---------- 候选点生成 ----------
    def _get_candidate_moves(self, board: GomokuBoard) -> List[Coord]:
        """只在已有棋子周围一定半径内找空位。棋盘为空时下在中间。"""
        size = board.size
        stones: List[Coord] = [
            (r, c)
            for r in range(size)
            for c in range(size)
            if board.grid[r][c] != Stone.EMPTY
        ]

        # 开局：棋盘无子 → 下在中心
        if not stones:
            center = size // 2
            return [(center, center)]

        min_r = min(r for r, _ in stones)
        max_r = max(r for r, _ in stones)
        min_c = min(c for _, c in stones)
        max_c = max(c for _, c in stones)

        r0 = max(min_r - self.search_radius, 0)
        r1 = min(max_r + self.search_radius, size - 1)
        c0 = max(min_c - self.search_radius, 0)
        c1 = min(max_c + self.search_radius, size - 1)

        candidates: List[Coord] = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if board.grid[r][c] == Stone.EMPTY:
                    candidates.append((r, c))
        return candidates

    # ---------- 一步“是否立刻获胜？” ----------
    def _is_winning_move(self, board: GomokuBoard, move: Coord, stone: Stone) -> bool:
        """在 move 落下 stone，看是否形成五连。"""
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return False

        # 备份现场
        old_stone = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        # 落子模拟
        board.grid[r][c] = stone
        board.last_move = (r, c)
        board.move_count += 1

        winner = board.check_winner((r, c))

        # 回滚
        board.grid[r][c] = old_stone
        board.last_move = old_last
        board.current_player = old_player
        board.move_count = old_count

        return winner == stone

    # ---------- 评估“一步之后的局面” ----------
    def _evaluate_move(self, board: GomokuBoard, move: Coord, player: Stone) -> int:
        """模拟 player 在 move 落子后的全局评分。"""
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return -10**18  # 不应该发生

        # 备份现场
        old_stone = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        # 模拟落子
        board.grid[r][c] = player
        board.last_move = (r, c)
        board.move_count += 1

        score = self.evaluate_board(board, player)

        # 回滚
        board.grid[r][c] = old_stone
        board.last_move = old_last
        board.current_player = old_player
        board.move_count = old_count

        return score

    # ---------- 启发式评分函数 ----------
    def evaluate_board(self, board: GomokuBoard, player: Stone) -> int:
        """
        对当前棋盘做一个大致评分：
        - 对自己连续子越多的窗口加分
        - 对对手连续子越多的窗口减分
        简化处理：只看长度为5的所有窗口（行/列/两条对角线）。
        """
        size = board.size
        grid = board.grid
        me = player
        opp = self._opponent(player)

        total_score = 0
        scores = self.SCORES

        directions = [
            (1, 0),   # 竖
            (0, 1),   # 横
            (1, 1),   # 主对角
            (1, -1),  # 副对角
        ]

        for dr, dc in directions:
            # 遍历所有可以作为5连起点的位置
            for r in range(size):
                for c in range(size):
                    end_r = r + (5 - 1) * dr
                    end_c = c + (5 - 1) * dc
                    if not (0 <= end_r < size and 0 <= end_c < size):
                        continue

                    me_cnt = 0
                    opp_cnt = 0

                    for k in range(5):
                        rr = r + k * dr
                        cc = c + k * dc
                        if grid[rr][cc] == me:
                            me_cnt += 1
                        elif grid[rr][cc] == opp:
                            opp_cnt += 1

                    # 同一窗口里双方都有子 → 互相堵死，不算分
                    if me_cnt > 0 and opp_cnt > 0:
                        continue
                    if me_cnt == 0 and opp_cnt == 0:
                        continue

                    if me_cnt > 0:
                        total_score += scores.get(me_cnt, 0)
                    else:
                        total_score -= scores.get(opp_cnt, 0)

        return total_score

    # ---------- 小工具 ----------
    @staticmethod
    def _opponent(stone: Stone) -> Stone:
        return Stone.BLACK if stone == Stone.WHITE else Stone.WHITE
