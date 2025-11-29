from __future__ import annotations

from typing import Optional, Callable, Tuple

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QComboBox,
)

from .core import GomokuBoard, Stone
from .ai import HeuristicAI
from .record import GameRecorder, GameRecord
from pathlib import Path

Coord = Tuple[int, int]


class BoardWidget(QWidget):
    """
    棋盘绘制区域：
    - 负责画网格和棋子
    - 负责响应鼠标点击，把 (row, col) 回调给主窗口
    """

    def __init__(self, board: GomokuBoard, on_human_move: Callable[[int, int], None], parent=None):
        super().__init__(parent)
        self.board = board
        self.on_human_move = on_human_move
        self._game_over = False

        # 给个合适的最小尺寸
        self.setMinimumSize(500, 500)

    def set_game_over(self, over: bool) -> None:
        self._game_over = over
        self.update()

    # ---- 绘制 ----
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        size = self.board.size
        w = self.width()
        h = self.height()
        margin = 40

        # 有效棋盘边长（像素，整数）
        effective = min(w - 2 * margin, h - 2 * margin)
        if effective <= 0:
            return

        cell = effective / (size - 1)  # 每一格的像素宽度（float 没问题）
        left = int((w - effective) / 2)
        top = int((h - effective) / 2)
        right = left + int((size - 1) * cell)
        bottom = top + int((size - 1) * cell)

        # 画网格 —— 传 int 给 drawLine
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        for i in range(size):
            x = int(left + i * cell)
            painter.drawLine(x, top, x, bottom)
            y = int(top + i * cell)
            painter.drawLine(left, y, right, y)

        # 画棋子
        for r in range(size):
            for c in range(size):
                stone = self.board.grid[r][c]
                if stone == Stone.EMPTY:
                    continue
                cx = left + c * cell
                cy = top + r * cell
                radius = cell * 0.4
                if stone == Stone.BLACK:
                    painter.setBrush(QBrush(Qt.black))
                else:
                    painter.setBrush(QBrush(Qt.white))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawEllipse(QPointF(cx, cy), radius, radius)

    # ---- 鼠标点击 → 转成棋盘坐标 ----
    def mousePressEvent(self, event) -> None:
        if self._game_over:
            return
        if event.button() != Qt.LeftButton:
            return

        size = self.board.size
        w = self.width()
        h = self.height()
        margin = 40
        effective = min(w - 2 * margin, h - 2 * margin)
        if effective <= 0:
            return
        cell = effective / (size - 1)
        left = (w - effective) / 2
        top = (h - effective) / 2

        x = event.x()
        y = event.y()

        col_f = (x - left) / cell
        row_f = (y - top) / cell
        c = int(round(col_f))
        r = int(round(row_f))

        if not (0 <= r < size and 0 <= c < size):
            return

        # 距离最近交点太远就不算
        target_x = left + c * cell
        target_y = top + r * cell
        dx = x - target_x
        dy = y - target_y
        dist_sq = dx * dx + dy * dy
        if dist_sq > (cell * 0.5) ** 2:
            return

        if self.on_human_move:
            self.on_human_move(r, c)

class ReplayWindow(QMainWindow):
    """
    棋谱回放窗口：
    - 只显示棋盘，不允许落子
    - 通过“上一步 / 下一步 / 重置”按钮控制回放进度
    """

    def __init__(self, record: GameRecord, parent=None):
        super().__init__(parent)
        self.record = record
        self.board = GomokuBoard(size=record.board_size)
        self.current_step = 0  # 已经展示到第几手（0 表示空棋盘）

        self.setWindowTitle("棋谱回放")
        self.resize(600, 650)

        # 棋盘：on_human_move 传 None，禁用点击落子
        self.board_widget = BoardWidget(self.board, on_human_move=None)

        self.info_label = QLabel(self._build_info_text())
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.prev_button = QPushButton("上一步")
        self.next_button = QPushButton("下一步")
        self.reset_button = QPushButton("重置")

        self.prev_button.clicked.connect(self.step_back)
        self.next_button.clicked.connect(self.step_forward)
        self.reset_button.clicked.connect(self.reset)

        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.addWidget(self.board_widget, stretch=1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.info_label)
        hbox.addStretch()
        hbox.addWidget(self.prev_button)
        hbox.addWidget(self.next_button)
        hbox.addWidget(self.reset_button)
        vbox.addLayout(hbox)

        self.setCentralWidget(central)

        self._refresh_board()

    def _build_info_text(self) -> str:
        total = len(self.record.moves)
        winner = self.record.winner
        if winner == int(Stone.BLACK):
            win_text = "黑胜"
        elif winner == int(Stone.WHITE):
            win_text = "白胜"
        else:
            win_text = "平局/未标记"
        return f"步数：{self.current_step}/{total}    结果：{win_text}"

    def _refresh_board(self) -> None:
        # 清空棋盘
        self.board = GomokuBoard(size=self.record.board_size)
        self.board_widget.board = self.board
        self.board.move_count = 0
        self.board.last_move = None

        # 应用前 current_step 手
        for i in range(self.current_step):
            mv = self.record.moves[i]
            stone = Stone(mv.player)
            self.board.grid[mv.row][mv.col] = stone
            self.board.move_count += 1
            self.board.last_move = (mv.row, mv.col)

        self.board_widget.update()
        self.info_label.setText(self._build_info_text())

    def step_forward(self) -> None:
        if self.current_step < len(self.record.moves):
            self.current_step += 1
            self._refresh_board()

    def step_back(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh_board()

    def reset(self) -> None:
        self.current_step = 0
        self._refresh_board()

class MainWindow(QMainWindow):
    """
    上位机主窗口：
    - 左侧棋盘
    - 下方状态栏 + “新局”按钮
    - 内部用 GomokuBoard + HeuristicAI + GameRecorder 驱动
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("棋眼 Pro - 五子棋上位机 (PyQt)")
        self.resize(700, 750)

        # --- 核心对象 ---
        self.board = GomokuBoard()
        # 默认：你执黑，AI 执白
        self.human_stone = Stone.BLACK
        self.ai_stone = Stone.WHITE
        self.ai = HeuristicAI(self.ai_stone)
        self.recorder = GameRecorder(board_size=self.board.size, first_player=Stone.BLACK)
        self.game_over = False

        # --- UI 组件 ---
        self.board_widget = BoardWidget(self.board, self.handle_human_move)

        self.status_label = QLabel("轮到你：黑棋 (●)")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 角色选择：你执黑 / 你执白
        self.role_combo = QComboBox()
        self.role_combo.addItems(["你执黑 (AI 执白)", "你执白 (AI 执黑)"])
        # 修改时只影响“下一局”，不打断当前对局，所以不用立刻改逻辑

        # 难度选择
        self.level_combo = QComboBox()
        self.level_combo.addItems(["简单", "中等", "困难"])

        self.new_game_button = QPushButton("新局")
        self.new_game_button.clicked.connect(self.new_game)

        self.replay_button = QPushButton("回放棋谱")
        self.replay_button.clicked.connect(self.open_replay)

        # 布局
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.addWidget(self.board_widget, stretch=1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.status_label)
        hbox.addStretch()
        hbox.addWidget(QLabel("角色:"))
        hbox.addWidget(self.role_combo)
        hbox.addWidget(QLabel("难度:"))
        hbox.addWidget(self.level_combo)
        hbox.addWidget(self.replay_button)
        hbox.addWidget(self.new_game_button)
        vbox.addLayout(hbox)

        self.setCentralWidget(central)

    def _create_ai_for_level(self, stone: Stone) -> HeuristicAI:
        """
        根据难度下拉框，创建对应配置的 AI。
        简单：只看一手，范围小
        中等：默认参数
        困难：范围更大，更多两层搜索
        """
        idx = self.level_combo.currentIndex()
        if idx == 0:  # 简单
            return HeuristicAI(stone, search_radius=1, max_search_candidates=0)
        elif idx == 1:  # 中等
            return HeuristicAI(stone, search_radius=2, max_search_candidates=20)
        else:  # 困难
            return HeuristicAI(stone, search_radius=3, max_search_candidates=40)

    def _status_text_for(self, stone: Stone, is_human: bool) -> str:
        who = "你" if is_human else "AI"
        if stone == Stone.BLACK:
            color = "黑棋 (●)"
        else:
            color = "白棋 (○)"
        return f"轮到{who}：{color}"
    # ---- 新局 ----
    def new_game(self) -> None:
        if not self.game_over:
            reply = QMessageBox.question(
                self,
                "开始新局？",
                "当前对局尚未结束，确定要开始新局吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # 重置棋盘
        self.board = GomokuBoard()

        # 根据下拉框决定谁执黑
        role_index = self.role_combo.currentIndex()
        if role_index == 0:
            # 你执黑
            self.human_stone = Stone.BLACK
            self.ai_stone = Stone.WHITE
        else:
            # 你执白
            self.human_stone = Stone.WHITE
            self.ai_stone = Stone.BLACK

        # 五子棋规则：黑棋先手
        self.board.current_player = Stone.BLACK
        first_player = Stone.BLACK

        # 按难度创建 AI
        self.ai = self._create_ai_for_level(self.ai_stone)
        self.recorder = GameRecorder(board_size=self.board.size, first_player=first_player)
        self.game_over = False

        self.board_widget.board = self.board
        self.board_widget.set_game_over(False)
        self.board_widget.update()

        # 如果 AI 执黑，则 AI 先手
        if self.ai_stone == Stone.BLACK:
            self.status_label.setText("AI 先手中...")
            QApplication.processEvents()
            self._ai_move_once()
        else:
            # 你执黑，轮到你
            self.status_label.setText(self._status_text_for(self.human_stone, is_human=True))
    def open_replay(self) -> None:
        """
        选择一个 records/*.json 棋谱文件，并打开回放窗口。
        """
        records_dir = Path.cwd() / "records"
        if not records_dir.exists():
            QMessageBox.information(self, "没有棋谱", "当前目录下还没有 records/ 目录，请先完成一局并保存棋谱。")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择棋谱文件",
            str(records_dir),
            "Gomoku Records (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            record = GameRecorder.load(Path(file_path))
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载棋谱文件：\n{e}")
            return

        replay_win = ReplayWindow(record, parent=self)
        replay_win.show()

    def _ai_move_once(self) -> None:
        if self.game_over:
            return
        if self.board.current_player != self.ai_stone:
            return

        ai_move = self.ai.select_move(self.board)
        if ai_move is None:
            # AI 无棋可下
            self.finish_game(None)
            return

        self.board.place_stone(*ai_move)
        self.recorder.add_move(self.ai_stone, ai_move)
        self.board_widget.update()

        winner = self.board.check_winner()
        if winner is not None or self.board.is_full():
            self.finish_game(winner)
            return

        # 轮到人类
        self.status_label.setText(self._status_text_for(self.human_stone, is_human=True))

    # ---- 人类落子回调 ----
    def handle_human_move(self, row: int, col: int) -> None:
        if self.game_over:
            return
        # 只在轮到人的时候响应点击
        if self.board.current_player != self.human_stone:
            return
        if not self.board.is_valid_move(row, col):
            return

        # 人类下子
        self.board.place_stone(row, col)
        self.recorder.add_move(self.human_stone, (row, col))
        self.board_widget.update()

        winner = self.board.check_winner()
        if winner is not None or self.board.is_full():
            self.finish_game(winner)
            return

        # AI 回合
        self.status_label.setText(self._status_text_for(self.ai_stone, is_human=False))
        QApplication.processEvents()

        self._ai_move_once()


    # ---- 对局结束 ----
    def finish_game(self, winner: Optional[Stone]) -> None:
        self.game_over = True
        self.board_widget.set_game_over(True)
        self.recorder.set_winner(winner)

        if winner is None:
            msg = "平局。"
        elif winner == self.human_stone:
            msg = f"你赢了！（{'黑' if winner == Stone.BLACK else '白'}方胜）"
        elif winner == self.ai_stone:
            msg = f"AI 获胜（{'黑' if winner == Stone.BLACK else '白'}方胜）"
        else:
            # 理论上不会出现
            msg = "对局结束。"

        reply = QMessageBox.question(
            self,
            "对局结束",
            msg + "\n\n是否保存棋谱到 records/ 目录？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            path = self.recorder.save_to_default(prefix="gui_human_vs_ai")
            QMessageBox.information(self, "保存成功", f"棋谱已保存到：\n{path}")
        else:
            QMessageBox.information(self, "对局结束", msg)

def main() -> None:
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()