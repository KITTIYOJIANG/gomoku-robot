from __future__ import annotations

import random
from typing import List, Optional, Set

from .core import Coord, GomokuBoard, Stone


class RandomAI:
    """Baseline AI that randomly chooses a legal move."""

    def __init__(self, stone: Stone) -> None:
        self.stone = stone

    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        legal_moves = [
            (r, c)
            for r in range(board.size)
            for c in range(board.size)
            if board.is_valid_move(r, c)
        ]
        return random.choice(legal_moves) if legal_moves else None


class HeuristicAI:
    """Heuristic Gomoku AI with tactical win/block checks and shallow search."""

    SCORES = {
        1: 10,
        2: 80,
        3: 1500,
        4: 20000,
        5: 10000000,
    }

    def __init__(
        self,
        stone: Stone,
        search_radius: int = 2,
        max_search_candidates: int = 20,
    ) -> None:
        self.stone = Stone(stone)
        self.search_radius = search_radius
        self.max_search_candidates = max_search_candidates

    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        candidates = self._get_candidate_moves(board)
        if not candidates:
            return None

        for move in candidates:
            if self._is_winning_move(board, move, self.stone):
                return move

        opponent = self._opponent(self.stone)
        for move in candidates:
            if self._is_winning_move(board, move, opponent):
                return move

        danger_blocks = self._find_open_three_block_moves(board, opponent)
        block_moves = [move for move in candidates if move in danger_blocks]
        if block_moves:
            return self._choose_best_by_heuristic(board, block_moves, self.stone)

        if len(candidates) <= self.max_search_candidates:
            best_score = -float("inf")
            best_moves: List[Coord] = []
            for move in candidates:
                score = self._minimax_after_first_move(board, move, self.stone)
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            return random.choice(best_moves) if best_moves else None

        return self._choose_best_by_heuristic(board, candidates, self.stone)

    def _choose_best_by_heuristic(
        self,
        board: GomokuBoard,
        candidates: List[Coord],
        player: Stone,
    ) -> Optional[Coord]:
        best_score = -float("inf")
        best_moves: List[Coord] = []
        for move in candidates:
            score = self._evaluate_move(board, move, player)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return random.choice(best_moves) if best_moves else None

    def _get_candidate_moves(self, board: GomokuBoard) -> List[Coord]:
        stones = [
            (r, c)
            for r in range(board.size)
            for c in range(board.size)
            if board.grid[r][c] != Stone.EMPTY
        ]

        if not stones:
            center = board.size // 2
            return [(center, center)]

        min_r = max(min(r for r, _ in stones) - self.search_radius, 0)
        max_r = min(max(r for r, _ in stones) + self.search_radius, board.size - 1)
        min_c = max(min(c for _, c in stones) - self.search_radius, 0)
        max_c = min(max(c for _, c in stones) + self.search_radius, board.size - 1)

        return [
            (r, c)
            for r in range(min_r, max_r + 1)
            for c in range(min_c, max_c + 1)
            if board.grid[r][c] == Stone.EMPTY
        ]

    def _minimax_after_first_move(
        self,
        board: GomokuBoard,
        move: Coord,
        player: Stone,
    ) -> int:
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return -10**18

        old_cell = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        board.grid[r][c] = player
        board.last_move = (r, c)
        board.move_count += 1

        if board.check_winner((r, c)) == player:
            self._restore_cell(board, r, c, old_cell, old_last, old_player, old_count)
            return 10**9

        opponent = self._opponent(player)
        opponent_candidates = self._get_candidate_moves(board)
        if not opponent_candidates:
            score = self.evaluate_board(board, player)
            self._restore_cell(board, r, c, old_cell, old_last, old_player, old_count)
            return score

        worst_score = float("inf")
        for orow, ocol in opponent_candidates:
            old_cell2 = board.grid[orow][ocol]
            old_last2 = board.last_move
            old_player2 = board.current_player
            old_count2 = board.move_count

            board.grid[orow][ocol] = opponent
            board.last_move = (orow, ocol)
            board.move_count += 1

            if board.check_winner((orow, ocol)) == opponent:
                score = -10**9
            else:
                score = self.evaluate_board(board, player)

            self._restore_cell(board, orow, ocol, old_cell2, old_last2, old_player2, old_count2)
            worst_score = min(worst_score, score)

        self._restore_cell(board, r, c, old_cell, old_last, old_player, old_count)
        return int(worst_score)

    @staticmethod
    def _restore_cell(
        board: GomokuBoard,
        row: int,
        col: int,
        old_cell: Stone,
        old_last: Optional[Coord],
        old_player: Stone,
        old_count: int,
    ) -> None:
        board.grid[row][col] = old_cell
        board.last_move = old_last
        board.current_player = old_player
        board.move_count = old_count

    def _is_winning_move(self, board: GomokuBoard, move: Coord, stone: Stone) -> bool:
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return False

        old_cell = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        board.grid[r][c] = stone
        board.last_move = (r, c)
        board.move_count += 1
        winner = board.check_winner((r, c))
        self._restore_cell(board, r, c, old_cell, old_last, old_player, old_count)

        return winner == stone

    def _evaluate_move(self, board: GomokuBoard, move: Coord, player: Stone) -> int:
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return -10**18

        old_cell = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        board.grid[r][c] = player
        board.last_move = (r, c)
        board.move_count += 1
        score = self.evaluate_board(board, player)
        self._restore_cell(board, r, c, old_cell, old_last, old_player, old_count)
        return score

    def evaluate_board(self, board: GomokuBoard, player: Stone) -> int:
        total_score = 0
        opponent = self._opponent(player)
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dr, dc in directions:
            for r in range(board.size):
                for c in range(board.size):
                    end_r = r + 4 * dr
                    end_c = c + 4 * dc
                    if not board.is_on_board(end_r, end_c):
                        continue

                    my_count = 0
                    opponent_count = 0
                    for k in range(5):
                        cell = board.grid[r + k * dr][c + k * dc]
                        if cell == player:
                            my_count += 1
                        elif cell == opponent:
                            opponent_count += 1

                    if my_count > 0 and opponent_count > 0:
                        continue
                    if my_count == 0 and opponent_count == 0:
                        continue

                    if my_count > 0:
                        total_score += self.SCORES.get(my_count, 0)
                    else:
                        base = self.SCORES.get(opponent_count, 0)
                        if opponent_count >= 4:
                            total_score -= base * 4
                        elif opponent_count == 3:
                            total_score -= base * 2
                        else:
                            total_score -= base

        return total_score

    def _find_open_three_block_moves(self, board: GomokuBoard, threat_stone: Stone) -> Set[Coord]:
        result: Set[Coord] = set()
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dr, dc in directions:
            for r in range(board.size):
                for c in range(board.size):
                    end_r = r + 4 * dr
                    end_c = c + 4 * dc
                    if not board.is_on_board(end_r, end_c):
                        continue

                    coords = [(r + k * dr, c + k * dc) for k in range(5)]
                    line = [board.grid[rr][cc] for rr, cc in coords]
                    if (
                        line[0] == Stone.EMPTY
                        and line[1] == threat_stone
                        and line[2] == threat_stone
                        and line[3] == threat_stone
                        and line[4] == Stone.EMPTY
                    ):
                        result.add(coords[0])
                        result.add(coords[4])

        return result

    @staticmethod
    def _opponent(stone: Stone) -> Stone:
        return Stone.BLACK if stone == Stone.WHITE else Stone.WHITE
