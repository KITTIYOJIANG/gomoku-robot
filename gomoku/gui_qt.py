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
)

from .core import GomokuBoard, Stone
from .ai import HeuristicAI
from .record import GameRecorder


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
        self.ai = HeuristicAI(Stone.WHITE)
        self.recorder = GameRecorder(board_size=self.board.size, first_player=Stone.BLACK)
        self.game_over = False

        # --- UI 组件 ---
        self.board_widget = BoardWidget(self.board, self.handle_human_move)
        self.status_label = QLabel("轮到你：黑棋 (●)")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.new_game_button = QPushButton("新局")
        self.new_game_button.clicked.connect(self.new_game)

        # 布局
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.addWidget(self.board_widget, stretch=1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.status_label)
        hbox.addStretch()
        hbox.addWidget(self.new_game_button)
        vbox.addLayout(hbox)

        self.setCentralWidget(central)

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

        self.board = GomokuBoard()
        self.ai = HeuristicAI(Stone.WHITE)
        self.recorder = GameRecorder(board_size=self.board.size, first_player=Stone.BLACK)
        self.game_over = False

        self.board_widget.board = self.board
        self.board_widget.set_game_over(False)
        self.status_label.setText("轮到你：黑棋 (●)")
        self.board_widget.update()

    # ---- 人类落子回调 ----
    def handle_human_move(self, row: int, col: int) -> None:
        if self.game_over:
            return
        if self.board.current_player != Stone.BLACK:
            return
        if not self.board.is_valid_move(row, col):
            return

        # 人类下子
        self.board.place_stone(row, col)
        self.recorder.add_move(Stone.BLACK, (row, col))
        self.board_widget.update()

        winner = self.board.check_winner()
        if winner is not None or self.board.is_full():
            self.finish_game(winner)
            return

        self.status_label.setText("轮到 AI：白棋 (○)")
        QApplication.processEvents()  # 让 UI 刷新一下状态

        # AI 回合
        ai_move = self.ai.select_move(self.board)
        if ai_move is None:
            self.finish_game(None)
            return

        self.board.place_stone(*ai_move)
        self.recorder.add_move(Stone.WHITE, ai_move)
        self.board_widget.update()

        winner = self.board.check_winner()
        if winner is not None or self.board.is_full():
            self.finish_game(winner)
            return

        self.status_label.setText("轮到你：黑棋 (●)")

    # ---- 对局结束 ----
    def finish_game(self, winner: Optional[Stone]) -> None:
        self.game_over = True
        self.board_widget.set_game_over(True)
        self.recorder.set_winner(winner)

        if winner == Stone.BLACK:
            msg = "你赢了！（黑方胜）"
        elif winner == Stone.WHITE:
            msg = "AI 获胜（白方胜）"
        else:
            msg = "平局。"

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