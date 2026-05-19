import random
import json
import os
import hashlib

class GomokuAI:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.search_depth = 2  # 思考深度

        # 🧠 强化学习记忆核心
        self.memory_file = "ai_experience.json"
        self.experience_pool = self._load_experience()

    def _load_experience(self):
        """📂 从硬盘读取 AI 的历史进化记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_experience(self):
        """💾 固化新的对弈经验到硬盘"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.experience_pool, f, ensure_ascii=False, indent=2)

    def _get_board_hash(self, board_state):
        """🧬 为当前盘面生成独一无二的 MD5 基因指纹"""
        flat_board = "".join(str(cell) for row in board_state for cell in row)
        return hashlib.md5(flat_board.encode()).hexdigest()

    def check_winner(self, board_state):
        """🏆 金牌裁判：扫描全盘，判断是否有五子连珠"""
        dirs = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] == 0: continue
                color = board_state[r][c]
                for dr, dc in dirs:
                    count = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_state[nr][nc] == color:
                        count += 1
                        nr += dr
                        nc += dc
                    if count >= 5: return color
        return 0

    def process_board(self, board_state):
        """🚀 核心引擎接管区"""
        # 1. 扫描是否有人已经胜利
        winner = self.check_winner(board_state)
        if winner == 1: return 1, "🏆 游戏结束：【黑棋】五子连珠，大获全胜！", None, None
        elif winner == 2: return 2, "🏆 游戏结束：【白棋】五子连珠，大获全胜！", None, None

        # 2. 统计当前黑白子
        black_count = sum(row.count(1) for row in board_state)
        white_count = sum(row.count(2) for row in board_state)

        # ==========================================
        # ⚖️ 宽容版裁判逻辑：允许 1 颗误差，超过 2 颗才拦截
        # ==========================================
        if abs(black_count - white_count) >= 2:
            return -1, f"⚠️ 警告：棋盘严重失衡！黑子({black_count})与白子({white_count})相差达2颗以上，请修正物理棋盘！", None, None

        # 动态分配 AI 的执子颜色（谁少帮谁下，一样多就默认帮黑下）
        if black_count > white_count:
            ai_color = 2  # 黑子多，该下白子了
        elif white_count > black_count:
            ai_color = 1  # 白子多，该下黑子了
        else:
            ai_color = 1  # 数量一样，默认黑子先行

        human_color = 3 - ai_color

        # 3. 空棋盘直接下天元
        if black_count == 0 and white_count == 0:
            center = self.board_size // 2
            return 0, "OK", ai_color, (center, center)

        # ==========================================
        # 🧠 强化学习：突触记忆匹配
        # ==========================================
        state_hash = self._get_board_hash(board_state)
        if state_hash in self.experience_pool:
            r, c = self.experience_pool[state_hash]
            # 校验记忆库里的绝杀点位目前是否仍然为空
            if board_state[r][c] == 0:
                print(f"🌟 [进化系统] 触发残局记忆库！绕过推演引擎，0.001秒调出历史最优解：({r}, {c})")
                return 0, "OK", ai_color, (r, c)

        # 4. 没有记忆，启动深度 Alpha-Beta 剪枝推演
        best_move = self._calculate_best_move_minimax(board_state, ai_color, human_color)

        if best_move:
            # ==========================================
            # 🧠 强化学习：固化新知识到本地硬盘
            # ==========================================
            self.experience_pool[state_hash] = best_move
            self._save_experience()
            print(f"💾 [进化系统] 发现新盘面！深度推演结果 ({best_move[0]}, {best_move[1]}) 已写入 AI 基因库。")

            return 0, "OK", ai_color, best_move
        else:
            return -3, "⚠️ 状态异常：棋盘可能已满，无路可走", None, None

    # ==========================================
    # 🧠 以下为大师级博弈算法核心 (保持不变)
    # ==========================================

    def _get_top_candidates(self, board_state, ai_color, human_color, limit=8):
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board_state[r][c] == 0:
                    has_neighbor = False
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_state[nr][nc] != 0:
                                has_neighbor = True
                                break
                        if has_neighbor: break
                    if has_neighbor:
                        atk = self._evaluate_point(board_state, r, c, ai_color)
                        dfn = self._evaluate_point(board_state, r, c, human_color)
                        score = atk + dfn * 1.2
                        candidates.append((score, r, c))
        candidates.sort(reverse=True, key=lambda x: x[0])
        return [(r, c) for s, r, c in candidates[:limit]]

    def _calculate_best_move_minimax(self, board_state, ai_color, human_color):
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        candidates = self._get_top_candidates(board_state, ai_color, human_color, limit=8)
        if not candidates: return None

        for r, c in candidates:
            board_state[r][c] = ai_color
            score = self._minimax(board_state, self.search_depth - 1, alpha, beta, False, ai_color, human_color)
            board_state[r][c] = 0

            if score > best_score:
                best_score = score
                best_move = (r, c)
            alpha = max(alpha, best_score)

        return best_move if best_move else candidates[0]

    def _minimax(self, board_state, depth, alpha, beta, is_maximizing, ai_color, human_color):
        winner = self.check_winner(board_state)
        if winner == ai_color: return 1000000 + depth
        elif winner == human_color: return -1000000 - depth

        if depth == 0:
            ai_score = sum(self._evaluate_point(board_state, r, c, ai_color) for r in range(self.board_size) for c in range(self.board_size) if board_state[r][c] == 0)
            hu_score = sum(self._evaluate_point(board_state, r, c, human_color) for r in range(self.board_size) for c in range(self.board_size) if board_state[r][c] == 0)
            return ai_score - hu_score * 1.5

        candidates = self._get_top_candidates(board_state, ai_color, human_color, limit=8)

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in candidates:
                board_state[r][c] = ai_color
                eval_score = self._minimax(board_state, depth - 1, alpha, beta, False, ai_color, human_color)
                board_state[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in candidates:
                board_state[r][c] = human_color
                eval_score = self._minimax(board_state, depth - 1, alpha, beta, True, ai_color, human_color)
                board_state[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval

    def _evaluate_point(self, board_state, r, c, color):
        score = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            consecutive, block = 1, 0
            for i in range(1, 5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if board_state[nr][nc] == color: consecutive += 1
                    elif board_state[nr][nc] == 0: break
                    else: block += 1; break
                else: block += 1; break
            for i in range(1, 5):
                nr, nc = r - dr * i, c - dc * i
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if board_state[nr][nc] == color: consecutive += 1
                    elif board_state[nr][nc] == 0: break
                    else: block += 1; break
                else: block += 1; break

            if consecutive >= 5: score += 100000
            elif consecutive == 4:
                if block == 0: score += 10000
                elif block == 1: score += 1000
            elif consecutive == 3:
                if block == 0: score += 1000
                elif block == 1: score += 100
            elif consecutive == 2:
                if block == 0: score += 100
                elif block == 1: score += 10
            elif consecutive == 1:
                if block == 0: score += 10
        return score