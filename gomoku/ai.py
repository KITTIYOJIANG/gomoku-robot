from __future__ import annotations
import random
from typing import List, Optional, Tuple, Set

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
    有点智商 + 两步搜索 的五子棋 AI：

    优先级：
    1. 我方一步直接赢 → 直接下。
    2. 对手一步直接赢 → 必须先堵。
    3. 对手“活三”（○○○ 两头空） → 尽量先去堵在端点。
    4. 其余情况，再用两层搜索（我走一步 + 对手走一步），
       用启发式评分来选在“对手最强反击下我最不亏”的那一步。
    """

    # 按连续子数量给的基础分数
    # 注意我们会对“对手的 3、4 连”额外放大危险权重
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
        """
        :param stone: 这个 AI 使用哪种棋（黑或白）
        :param search_radius: 候选点在已有棋子周围的搜索半径
        :param max_search_candidates: 候选点数量超过这个值时，不做两步搜索，只用一层启发式
        """
        self.stone = stone
        self.search_radius = search_radius
        self.max_search_candidates = max_search_candidates

    # ---------- 对外主入口 ----------
    def select_move(self, board: GomokuBoard) -> Optional[Coord]:
        candidates = self._get_candidate_moves(board)
        if not candidates:
            return None

        # 1. 如果我有“立刻赢”的点，直接下
        for move in candidates:
            if self._is_winning_move(board, move, self.stone):
                return move

        opponent = self._opponent(self.stone)

        # 2. 如果对手下一步能赢，优先堵
        for move in candidates:
            if self._is_winning_move(board, move, opponent):
                return move

        # 3. 如果对手有活三，优先在活三端点堵
        danger_blocks = self._find_open_three_block_moves(board, opponent)
        block_moves = [m for m in candidates if m in danger_blocks]
        if block_moves:
            # 在所有可以堵活三的候选点里，选启发式评分最高的一个
            best_score = -float("inf")
            best_list: List[Coord] = []
            for move in block_moves:
                score = self._evaluate_move(board, move, self.stone)
                if score > best_score:
                    best_score = score
                    best_list = [move]
                elif score == best_score:
                    best_list.append(move)
            return random.choice(best_list)

        # 4. 其余情况：根据候选点数量，决定是否做两步搜索
        if len(candidates) <= self.max_search_candidates:
            # 用简单 minimax（两层：我走一步 + 对手走一步）
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
        else:
            # 候选点太多就退回单步启发式（避免太卡）
            best_score = -float("inf")
            best_moves: List[Coord] = []

            for move in candidates:
                score = self._evaluate_move(board, move, self.stone)
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)

            return random.choice(best_moves) if best_moves else None

    # ---------- 两层搜索：我下一步 + 对手下一步 ----------
    def _minimax_after_first_move(
        self,
        board: GomokuBoard,
        move: Coord,
        player: Stone,
    ) -> int:
        """
        简化版 minimax：
        - 先模拟 player 在 move 落子；
        - 然后假设对手在所有候选点中选“对我最不利”的那步；
        - 返回这种最坏情况下的评分（从 player 的视角）。
        """
        r, c = move
        if board.grid[r][c] != Stone.EMPTY:
            return -10**18  # 理论上不应该发生

        # 备份现场
        old_cell = board.grid[r][c]
        old_last = board.last_move
        old_player = board.current_player
        old_count = board.move_count

        # 模拟我方落子
        board.grid[r][c] = player
        board.last_move = (r, c)
        board.move_count += 1

        # 如果这一步直接赢了，给一个极大分数
        if board.check_winner((r, c)) == player:
            score = 10**9
            # 回滚
            board.grid[r][c] = old_cell
            board.last_move = old_last
            board.current_player = old_player
            board.move_count = old_count
            return score

        opp = self._opponent(player)
        opp_candidates = self._get_candidate_moves(board)

        # 对手无子可下，就直接按当前局面打分
        if not opp_candidates:
            score = self.evaluate_board(board, player)
            # 回滚
            board.grid[r][c] = old_cell
            board.last_move = old_last
            board.current_player = old_player
            board.move_count = old_count
            return score

        # 对手会选“对我最糟糕”的那一步 → 我方的 worst_score
        worst_score = float("inf")

        for orow, ocol in opp_candidates:
            if board.grid[orow][ocol] != Stone.EMPTY:
                continue

            # 备份对手这一步之前的状态
            old_cell2 = board.grid[orow][ocol]
            old_last2 = board.last_move
            old_player2 = board.current_player
            old_count2 = board.move_count

            # 模拟对手落子
            board.grid[orow][ocol] = opp
            board.last_move = (orow, ocol)
            board.move_count += 1

            # 如果对手直接赢了，这是我方极差局面
            if board.check_winner((orow, ocol)) == opp:
                move_score = -10**9
            else:
                # 否则，用启发式评估当前局面（从 player 视角）
                move_score = self.evaluate_board(board, player)

            # 回滚对手这一步
            board.grid[orow][ocol] = old_cell2
            board.last_move = old_last2
            board.current_player = old_player2
            board.move_count = old_count2

            if move_score < worst_score:
                worst_score = move_score

        # 回滚我方这一步
        board.grid[r][c] = old_cell
        board.last_move = old_last
        board.current_player = old_player
        board.move_count = old_count

        return worst_score

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

    # ---------- 单步评估“一步之后的局面” ----------
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
        - 对对手连续子越多的窗口减分（对手 3/4 连权重更大）
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
                        # 防守更重要：对手 3 连 / 4 连权重放大
                        base = scores.get(opp_cnt, 0)
                        if opp_cnt >= 4:
                            total_score -= base * 4
                        elif opp_cnt == 3:
                            total_score -= base * 2
                        else:
                            total_score -= base

        return total_score

    # ---------- 寻找“对手活三”的堵点 ----------
    def _find_open_three_block_moves(self, board: GomokuBoard, threat_stone: Stone) -> Set[Coord]:
        """
        找出所有需要优先堵掉的“活三”端点。

        活三模式指长度为5的窗口里形如：
            . threat threat threat .
        两端都是空，中间是对手三连。
        返回值是所有“端点坐标”的集合。
        """
        size = board.size
        grid = board.grid
        result: Set[Coord] = set()

        directions = [
            (1, 0),   # 竖
            (0, 1),   # 横
            (1, 1),   # 主对角
            (1, -1),  # 副对角
        ]

        for dr, dc in directions:
            for r in range(size):
                for c in range(size):
                    end_r = r + 4 * dr
                    end_c = c + 4 * dc
                    if not (0 <= end_r < size and 0 <= end_c < size):
                        continue

                    coords: List[Coord] = []
                    line: List[Stone] = []
                    for k in range(5):
                        rr = r + k * dr
                        cc = c + k * dc
                        coords.append((rr, cc))
                        line.append(grid[rr][cc])

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

    # ---------- 小工具 ----------
    @staticmethod
    def _opponent(stone: Stone) -> Stone:
        return Stone.BLACK if stone == Stone.WHITE else Stone.WHITE