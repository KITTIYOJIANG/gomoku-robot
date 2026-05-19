"""
=============================================================================
项目名称：智能五子棋 - 高精度视觉与 AI 博弈中枢 (豪华商业版)
包含模块：天眼视觉防抖过滤 + PyQt5 赛博朋克控制台 + AI 决策接入
=============================================================================
"""

import sys
import copy
import threading
import time
from queue import Queue, Empty

import cv2
import numpy as np
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox, QFrame, QGraphicsDropShadowEffect

# 尝试导入咱们手搓的 AI 大脑
try:
    from ai_engine import GomokuAI
except ImportError:
    print("❌ 找不到 ai_engine.py！请确保它和 main.py 放在一起。")
    sys.exit()

# ==========================================
# ⚙️ 全局配置区
# ==========================================
CAMERA_ID = 1               # 🎥 摄像头编号 (0为自带，1为外接)
BOARD_SIZE = 15             # 🏁 棋盘规格
BOARD_PIXELS = 600          # 🖥️ 视觉拉平后的正方形像素大小

# 📐 物理棋盘四角标定坐标
SRC_POINTS = np.float32([
    [85, 27],  # 左上角
    [516, 29],  # 右上角
    [511, 460],  # 右下角
    [84, 469]   # 左下角
])

# ==========================================
# 🧱 核心数据结构
# ==========================================
class Stone:
    EMPTY = 0
    BLACK = 1
    WHITE = 2

class GomokuBoard:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.grid = [[Stone.EMPTY for _ in range(size)] for _ in range(size)]
        self.last_move = None

    def reset(self):
        self.grid = [[Stone.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.last_move = None

# ==========================================
# 👁️ 独立线程：天眼视觉系统 (带防抖处理)
# ==========================================
class CameraThread(threading.Thread):
    def __init__(self, output_queue: Queue, cap):
        super().__init__(daemon=True)
        self.output_queue = output_queue
        self.cap = cap
        self._stop_flag = threading.Event()

        self.padding = 35
        self.cell_size = (BOARD_PIXELS - 2 * self.padding) / (BOARD_SIZE - 1)

        self.dst_points = np.float32([
            [self.padding, self.padding],
            [BOARD_PIXELS - self.padding, self.padding],
            [BOARD_PIXELS - self.padding, BOARD_PIXELS - self.padding],
            [self.padding, BOARD_PIXELS - self.padding]
        ])
        self.matrix = cv2.getPerspectiveTransform(SRC_POINTS, self.dst_points)

        # 🌟 帧缓冲池与防抖阈值
        self.history_frames = []
        self.history_size = 8

    def stop(self):
        self._stop_flag.set()

    def get_stable_board(self, raw_matrix):
        """🛡️ 时间序列防抖：只有连续多帧稳定的棋子才会被确认"""
        self.history_frames.append(raw_matrix)
        if len(self.history_frames) > self.history_size:
            self.history_frames.pop(0)

        # 还没攒够缓冲帧数时，先不输出稳定画面
        if len(self.history_frames) < self.history_size:
            return [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

        stable_matrix = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                states = [frame[r][c] for frame in self.history_frames]
                # 只有当 8 帧里面至少 6 帧稳定，才算真正落子，完美过滤手部遮挡
                if states.count(1) >= 6:
                    stable_matrix[r][c] = 1
                elif states.count(2) >= 6:
                    stable_matrix[r][c] = 2
                else:
                    stable_matrix[r][c] = 0
        return stable_matrix

    def run(self):
        print("🎬 [天眼引擎] 视觉识别线程已启动...")
        window_name = "God's Eye - Vision Monitor"
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

        cv2.createTrackbar('Blk_Diff', window_name, 56, 100, lambda x: None)
        cv2.createTrackbar('Wht_Diff', window_name, 6, 100, lambda x: None)
        cv2.createTrackbar('ROI_Size', window_name, 12, 30, lambda x: None)

        while not self._stop_flag.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            blk_d = cv2.getTrackbarPos('Blk_Diff', window_name)
            wht_d = cv2.getTrackbarPos('Wht_Diff', window_name)
            roi_s = max(2, cv2.getTrackbarPos('ROI_Size', window_name))

            # ✨ 替换成这行新代码（开启边缘像素无限拉伸复制）：
            warped = cv2.warpPerspective(frame, self.matrix, (BOARD_PIXELS, BOARD_PIXELS),
                                         borderMode=cv2.BORDER_REPLICATE)
            board_state = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
            gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            render_img = warped.copy()
            ring_radius = roi_s + 10

            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    cx = int(self.padding + col * self.cell_size)
                    cy = int(self.padding + row * self.cell_size)

                    center_mask = np.zeros_like(gray_blurred)
                    cv2.circle(center_mask, (cx, cy), roi_s, 255, -1)
                    center_mean = cv2.mean(gray_blurred, mask=center_mask)[0]

                    ring_mask = np.zeros_like(gray_blurred)
                    cv2.circle(ring_mask, (cx, cy), ring_radius, 255, -1)
                    cv2.circle(ring_mask, (cx, cy), roi_s + 2, 0, -1)
                    ring_mean = cv2.mean(gray_blurred, mask=ring_mask)[0]

                    if center_mean < ring_mean - blk_d:
                        board_state[row][col] = 1
                        cv2.circle(render_img, (cx, cy), roi_s, (255, 0, 0), -1)
                    elif center_mean > ring_mean + wht_d:
                        board_state[row][col] = 2
                        cv2.circle(render_img, (cx, cy), roi_s, (0, 255, 0), -1)
                        cv2.circle(render_img, (cx, cy), roi_s + 4, (0, 0, 255), 2)
                    else:
                        cv2.drawMarker(render_img, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 10, 1)

            cv2.putText(render_img, f"PARAM: Blk(-{blk_d}) Wht(+{wht_d}) ROI({roi_s})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow(window_name, render_img)
            cv2.waitKey(30)

            # 🌟 输出给上位机前，先经过严格的防抖过滤！
            stable_state = self.get_stable_board(board_state)
            self.output_queue.put(stable_state)

        cv2.destroyWindow(window_name)

# ==========================================
# 🎨 PyQt5 界面组件：拟真棋盘渲染
# ==========================================
class BoardWidget(QWidget):
    def __init__(self, board: GomokuBoard, main_window=None, parent=None):
        super().__init__(parent)
        self.board = board
        self.main_window = main_window
        self.setMinimumSize(600, 600)
        self.margin = 50
        self.grid_size = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height())
        self.grid_size = (side - 2 * self.margin) / (self.board.size - 1)

        board_rect = QRectF(20, 20, side - 40, side - 40)
        painter.setBrush(QColor(218, 170, 110))
        painter.setPen(QPen(QColor(139, 90, 43), 4))
        painter.drawRoundedRect(board_rect, 15, 15)

        painter.setPen(QPen(QColor(50, 50, 50, 180), 1.5))
        for i in range(self.board.size):
            pos = self.margin + i * self.grid_size
            painter.drawLine(int(self.margin), int(pos), int(side - self.margin), int(pos))
            painter.drawLine(int(pos), int(self.margin), int(pos), int(side - self.margin))

        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.setPen(Qt.NoPen)
        for r, c in [(3, 3), (3, 9), (6, 6), (9, 3), (9, 9)] if self.board.size == 13 else [(3,3), (3,11), (7,7), (11,3), (11,11)]:
            cx, cy = self.margin + c * self.grid_size, self.margin + r * self.grid_size
            painter.drawEllipse(QRectF(cx - 5, cy - 5, 10, 10))

        radius = self.grid_size * 0.42

        for r in range(self.board.size):
            for c in range(self.board.size):
                stone = self.board.grid[r][c]
                if stone != Stone.EMPTY:
                    cx, cy = self.margin + c * self.grid_size, self.margin + r * self.grid_size
                    gradient = QRadialGradient(cx - radius*0.3, cy - radius*0.3, radius)
                    if stone == Stone.BLACK:
                        gradient.setColorAt(0, QColor(80, 80, 80))
                        gradient.setColorAt(1, QColor(10, 10, 10))
                    else:
                        gradient.setColorAt(0, QColor(255, 255, 255))
                        gradient.setColorAt(0.8, QColor(220, 220, 220))
                        gradient.setColorAt(1, QColor(150, 150, 150))
                    painter.setBrush(QBrush(gradient))
                    painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        if self.main_window and self.main_window.pending_ai_move and self.main_window.blink_state:
            pm = self.main_window.pending_ai_move
            pr, pc, pcolor = pm['row'], pm['col'], pm['color']
            cx, cy = self.margin + pc * self.grid_size, self.margin + pr * self.grid_size

            halo_color = QColor(0, 255, 255, 100) if pcolor == Stone.BLACK else QColor(255, 165, 0, 120)
            painter.setBrush(QBrush(halo_color))
            painter.setPen(QPen(QColor(0, 255, 255) if pcolor == Stone.BLACK else QColor(255, 165, 0), 2, Qt.DashLine))
            painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(cx - 3, cy - 3, 6, 6))

# ==========================================
# 🚀 PyQt5 界面组件：主控中枢窗口
# ==========================================
class MainWindow(QMainWindow):
    ai_move_ready_signal = pyqtSignal(int, int, object)
    ai_move_failed_signal = pyqtSignal(str)

    # 🎯 这里就是你刚才报错的地方，必须确保有 (self, cap)
    def __init__(self, cap):
        super().__init__()
        self.setWindowTitle("🤖 天机手：智能五子棋对弈中枢")
        self.resize(1000, 700)

        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: #E0E0E0; font-family: 'Microsoft YaHei'; }
            QFrame#controlPanel { background-color: #2D2D30; border-radius: 15px; }
            QPushButton { background-color: #007ACC; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #0098FF; }
            QPushButton:pressed { background-color: #005C99; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
            QPushButton#clearBtn { background-color: #D24545; }
            QPushButton#clearBtn:hover { background-color: #E65A5A; }
            QComboBox { background-color: #3E3E42; color: white; border: 1px solid #555555; border-radius: 6px; padding: 5px 15px; }
        """)

        self.board = GomokuBoard(size=BOARD_SIZE)
        self.brain = GomokuAI(board_size=BOARD_SIZE)

        self.pending_ai_move = None
        self.blink_state = True
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)

        self.ai_move_ready_signal.connect(self.set_pending_move)
        self.ai_move_failed_signal.connect(self.handle_ai_failed)

        self.init_ui()

        self.camera_queue = Queue()
        self.camera_thread = CameraThread(self.camera_queue, cap=cap)
        self.camera_thread.start()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.poll_camera_queue)
        self.update_timer.start(100)

        self.ai_is_thinking = False

    def toggle_blink(self):
        self.blink_state = not self.blink_state
        self.board_widget.update()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.board_widget = BoardWidget(self.board, main_window=self)

        right_panel = QFrame()
        right_panel.setObjectName("controlPanel")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 0)
        right_panel.setGraphicsEffect(shadow)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(25, 30, 25, 30)
        right_layout.setSpacing(25)

        title_label = QLabel("🚀 天眼智控中枢")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00E5FF; margin-bottom: 10px;")

        self.status_label = QLabel("🟢 状态：系统就绪，等待开局")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #00E5FF;")

        self.btn_ai_move = QPushButton("🤖 请求 AI 决策")
        self.btn_ai_move.setStyleSheet("font-size: 16px; min-height: 50px;")
        self.btn_ai_move.clicked.connect(self.trigger_ai_move)

        self.btn_clear = QPushButton("🔄 清空物理棋盘缓存")
        self.btn_clear.setObjectName("clearBtn")
        self.btn_clear.setStyleSheet("font-size: 16px; min-height: 50px;")
        self.btn_clear.clicked.connect(self.reset_game)

        right_layout.addWidget(title_label)
        right_layout.addWidget(self.status_label)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.btn_ai_move)
        right_layout.addStretch()
        right_layout.addWidget(self.btn_clear)

        main_layout.addWidget(self.board_widget, stretch=5)
        main_layout.addWidget(right_panel, stretch=3)

    def poll_camera_queue(self):
        latest_state = None
        try:
            while True:
                latest_state = self.camera_queue.get_nowait()
        except Empty:
            pass

        if latest_state is not None:
            for r in range(self.board.size):
                for c in range(self.board.size):
                    v = latest_state[r][c]
                    if v == 1: self.board.grid[r][c] = Stone.BLACK
                    elif v == 2: self.board.grid[r][c] = Stone.WHITE
                    else: self.board.grid[r][c] = Stone.EMPTY

            if self.pending_ai_move:
                r, c, expected_color = self.pending_ai_move['row'], self.pending_ai_move['col'], self.pending_ai_move['color']
                if self.board.grid[r][c] == expected_color:
                    self.pending_ai_move = None
                    self.blink_timer.stop()
                    self.btn_ai_move.setEnabled(True)
                    self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #00E5FF;")
                    self.status_label.setText("🟢 状态：视觉已确认落子，等待下一步...")

            self.board_widget.update()

    def trigger_ai_move(self):
        if self.ai_is_thinking:
            return
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #FF1493;")
        self.status_label.setText("🧠 状态：算力引擎已介入，推演中...")
        self.ai_is_thinking = True
        self.btn_ai_move.setEnabled(False)
        threading.Thread(target=self._ai_worker_thread, daemon=True).start()

    def _ai_worker_thread(self):
        try:
            state_matrix = [[0] * self.board.size for _ in range(self.board.size)]
            for r in range(self.board.size):
                for c in range(self.board.size):
                    if self.board.grid[r][c] == Stone.BLACK:
                        state_matrix[r][c] = 1
                    elif self.board.grid[r][c] == Stone.WHITE:
                        state_matrix[r][c] = 2

            # 这里调用刚才在 ai_engine.py 写好的全能大脑
            status_code, msg, ai_color, best_move = self.brain.process_board(state_matrix)

            if status_code == 0:
                best_r, best_c = best_move
                self.ai_move_ready_signal.emit(best_r, best_c, ai_color)
            else:
                self.ai_move_failed_signal.emit(msg)

        except Exception as e:
            print(f"❌ 后台执行线程发生严重错误: {e}")
            self.ai_move_failed_signal.emit(f"❌ 系统底层逻辑错误: {str(e)}")

    def set_pending_move(self, r, c, color):
        self.ai_is_thinking = False
        self.pending_ai_move = {'row': r, 'col': c, 'color': color}
        color_name = "黑子" if color == Stone.BLACK else "白子"
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #32CD32;")
        self.status_label.setText(f"🎯 坐标锁定！请在光晕处部署物理 {color_name}")
        self.btn_ai_move.setText(f"⏳ 等待部署完成...")
        self.blink_timer.start(500)
        self.board_widget.update()

    def handle_ai_failed(self, error_msg):
        self.ai_is_thinking = False
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #D24545;")
        self.status_label.setText(error_msg)
        self.btn_ai_move.setEnabled(True)
        self.btn_ai_move.setText("🤖 重新请求 AI 决策")

    def reset_game(self):
        self.board.reset()
        self.pending_ai_move = None
        self.blink_timer.stop()
        self.ai_is_thinking = False
        self.btn_ai_move.setEnabled(True)
        self.btn_ai_move.setText("🤖 请求 AI 决策")
        self.board_widget.update()
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #00E5FF;")
        self.status_label.setText("🟢 状态：内存已清空，系统重置完毕")

    def closeEvent(self, event):
        self.update_timer.stop()
        if getattr(self, "camera_thread", None): self.camera_thread.stop()
        super().closeEvent(event)

# ==========================================
# 🚀 启动入口
# ==========================================
if __name__ == "__main__":
    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        print(f"❌ 错误：无法打开摄像头 {CAMERA_ID}。")
        sys.exit()

    app = QApplication(sys.argv)
    window = MainWindow(cap)
    window.show()
    sys.exit(app.exec_())