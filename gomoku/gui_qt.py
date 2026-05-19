import sys
import copy
import threading
from queue import Queue
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal  # 🌟 引入核心的跨线程信号
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox

from . import config
from .core import GomokuBoard, Stone
from .camera_interface import CameraThread, consume_latest_board_state, update_board_from_camera

try:
    from .ai_logic import get_best_move
except ImportError:
    get_best_move = None

try:
    from .stm32_controller import STM32Controller
except ImportError:
    STM32Controller = None

from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, \
    QComboBox, QFrame, QGraphicsDropShadowEffect


class BoardWidget(QWidget):
    def __init__(self, board: GomokuBoard, main_window=None, parent=None):
        super().__init__(parent)
        self.board = board
        self.main_window = main_window
        self.setMinimumSize(650, 650)
        self.margin = 50
        self.grid_size = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width, height = self.width(), self.height()
        side = min(width, height)
        self.grid_size = (side - 2 * self.margin) / (self.board.size - 1)

        # 1. Render 带有高级质感的木质棋盘背景
        board_rect = QRectF(20, 20, side - 40, side - 40)
        painter.setBrush(QColor(218, 170, 110))  # 温润的实木色
        painter.setPen(QPen(QColor(139, 90, 43), 4))  # 深色实木边框
        painter.drawRoundedRect(board_rect, 15, 15)

        # 2. Render 极细的棋盘网格
        pen = QPen(QColor(50, 50, 50, 180), 1.5)
        painter.setPen(pen)
        for i in range(self.board.size):
            pos = self.margin + i * self.grid_size
            painter.drawLine(int(self.margin), int(pos), int(side - self.margin), int(pos))
            painter.drawLine(int(pos), int(self.margin), int(pos), int(side - self.margin))

        # 3. Render 天元和星位
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.setPen(Qt.NoPen)
        # Assuming 15x15 standard, if 13x13 adjust accordingly
        star_points = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)] if self.board.size == 15 else [(3, 3), (3, 9),
                                                                                                  (6, 6), (9, 3),
                                                                                                  (9, 9)]
        for r, c in star_points:
            cx, cy = self.margin + c * self.grid_size, self.margin + r * self.grid_size
            painter.drawEllipse(QRectF(cx - 5, cy - 5, 10, 10))

        radius = self.grid_size * 0.42

        # 4. Render 3D 拟真棋子 (带有立体高光渐变)
        for r in range(self.board.size):
            for c in range(self.board.size):
                stone = self.board.grid[r][c]
                if stone != Stone.EMPTY:
                    cx, cy = self.margin + c * self.grid_size, self.margin + r * self.grid_size

                    # Apply radial gradient to simulate 3D volume
                    gradient = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius)
                    if stone == Stone.BLACK:
                        gradient.setColorAt(0, QColor(80, 80, 80))
                        gradient.setColorAt(1, QColor(10, 10, 10))
                    else:
                        gradient.setColorAt(0, QColor(255, 255, 255))
                        gradient.setColorAt(0.8, QColor(220, 220, 220))
                        gradient.setColorAt(1, QColor(150, 150, 150))

                    painter.setBrush(QBrush(gradient))
                    painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

                    # Highlight the last move
                    if self.board.last_move == (r, c):
                        painter.setPen(QPen(QColor(255, 50, 50, 200), 3))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(QRectF(cx - radius * 0.5, cy - radius * 0.5, radius, radius))

        # 5. Render 赛博朋克风的“AI 预测虚影”
        if self.main_window and self.main_window.pending_ai_move:
            if self.main_window.blink_state:
                pm = self.main_window.pending_ai_move
                pr, pc, pcolor = pm['row'], pm['col'], pm['color']
                cx, cy = self.margin + pc * self.grid_size, self.margin + pr * self.grid_size

                # Generate high-tech halo effect
                halo_color = QColor(0, 255, 255, 100) if pcolor == Stone.BLACK else QColor(255, 165, 0, 120)
                painter.setBrush(QBrush(halo_color))
                painter.setPen(
                    QPen(QColor(0, 255, 255) if pcolor == Stone.BLACK else QColor(255, 165, 0), 2, Qt.DashLine))
                painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

                # Center target lock
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QRectF(cx - 3, cy - 3, 6, 6))


class MainWindow(QMainWindow):
    ai_move_ready_signal = pyqtSignal(int, int, object)
    ai_move_failed_signal = pyqtSignal()

    def __init__(self, cap=None):
        super().__init__()
        self.setWindowTitle("🤖 天机手：智能五子棋对弈中枢")
        self.resize(1050, 700)

        # 🌟 Global QSS Injection (Dark Theme)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', 'Microsoft YaHei'; }
            QFrame#controlPanel { 
                background-color: #2D2D30; 
                border-radius: 15px; 
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0098FF; }
            QPushButton:pressed { background-color: #005C99; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
            QPushButton#clearBtn { background-color: #D24545; }
            QPushButton#clearBtn:hover { background-color: #E65A5A; }

            QComboBox {
                background-color: #3E3E42;
                color: white;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px 15px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2D2D30;
                color: white;
                selection-background-color: #007ACC;
            }
        """)

        self.board = GomokuBoard(size=config.BOARD_SIZE)
        self.stm32_controller = STM32Controller(config.SERIAL_PORT, config.SERIAL_BAUDRATE) if STM32Controller else None

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
        main_layout.setSpacing(25)

        self.board_widget = BoardWidget(self.board, main_window=self)

        # Build the Control Panel container
        right_panel = QFrame()
        right_panel.setObjectName("controlPanel")

        # Apply drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 0)
        right_panel.setGraphicsEffect(shadow)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(25, 30, 25, 30)
        right_layout.setSpacing(25)

        # Panel Title
        title_label = QLabel("🚀 天眼智控中枢")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00E5FF; margin-bottom: 10px;")

        # Status Display
        self.status_label = QLabel("🟢 状态：系统就绪，等待开局")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 15px; background-color: #1E1E1E; border-radius: 8px; border-left: 4px solid #00E5FF;")

        # Mode Selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["👤🤖 人机对战 (AI执白)", "👤👤 人人对战 (充当裁判)", "🤖🤖 双机对战 (AI左右互搏)"])
        self.mode_combo.setStyleSheet("font-size: 15px; min-height: 40px;")
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)

        # Action Buttons
        self.btn_ai_move = QPushButton("🤖 请求 AI 决策")
        self.btn_ai_move.setStyleSheet("font-size: 16px; min-height: 50px;")
        self.btn_ai_move.clicked.connect(self.trigger_ai_move)

        self.btn_clear = QPushButton("🔄 格式化物理棋盘")
        self.btn_clear.setObjectName("clearBtn")
        self.btn_clear.setStyleSheet("font-size: 16px; min-height: 50px;")
        self.btn_clear.clicked.connect(self.reset_game)

        # Assemble layout
        right_layout.addWidget(title_label)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(QLabel("Operating Mode:", styleSheet="color: #AAAAAA; font-size: 14px;"))
        right_layout.addWidget(self.mode_combo)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.btn_ai_move)
        right_layout.addStretch()
        right_layout.addWidget(self.btn_clear)

        main_layout.addWidget(self.board_widget, stretch=5)
        main_layout.addWidget(right_panel, stretch=3)

    def on_mode_changed(self, index):
        if index == 1:
            self.btn_ai_move.setEnabled(False)
            self.btn_ai_move.setText("🚫 AI 已禁用")
            self.status_label.setText("状态：人人对战模式")
        else:
            self.btn_ai_move.setEnabled(True)
            self.btn_ai_move.setText("🤖 让 AI 下一步")
            self.status_label.setText("状态：等待落子...")

    def poll_camera_queue(self):
        latest_state = consume_latest_board_state(self.camera_queue)
        if latest_state is not None:
            update_board_from_camera(self.board, latest_state)

            # 🌟 视觉校验：摄像头确认玩家摆对了实体棋子！
            if self.pending_ai_move:
                r = self.pending_ai_move['row']
                c = self.pending_ai_move['col']
                expected_color = self.pending_ai_move['color']

                if self.board.grid[r][c] == expected_color:
                    print(f"✅ 视觉确认：成功放置 {('黑棋' if expected_color == Stone.BLACK else '白棋')} ！")
                    self.pending_ai_move = None
                    self.blink_timer.stop()
                    self.btn_ai_move.setEnabled(True)
                    self.btn_ai_move.setText("🤖 让 AI 下一步")
                    self.status_label.setText("状态：等待落子...")

                    # 🌟 彩蛋：双机对战(模式2) 的全自动连发逻辑！
                    if self.mode_combo.currentIndex() == 2:
                        self.status_label.setText("🔥 自动触发下一手...")
                        # 等你手缩回去 1.5 秒后，自动命令 AI 继续下！
                        QTimer.singleShot(1500, self.trigger_ai_move)

            self.board_widget.update()

    def trigger_ai_move(self):
        if self.ai_is_thinking or get_best_move is None:
            return

        self.status_label.setText("🧠 状态：AI 正在思考...")
        self.ai_is_thinking = True
        self.btn_ai_move.setEnabled(False)

        # 启动纯后台计算线程
        threading.Thread(target=self._ai_worker_thread, daemon=True).start()

    def _ai_worker_thread(self):
        try:
            board_copy = copy.deepcopy(self.board)

            black_count = 0
            white_count = 0
            for r in range(board_copy.size):
                for c in range(board_copy.size):
                    if board_copy.grid[r][c] == Stone.BLACK:
                        black_count += 1
                    elif board_copy.grid[r][c] == Stone.WHITE:
                        white_count += 1

            ai_color = Stone.BLACK if black_count == white_count else Stone.WHITE
            color_name = "黑棋" if ai_color == Stone.BLACK else "白棋"
            print(f"🤖 [AI 引擎] 当前判定 AI 执 {color_name}...")

            best_r, best_c = get_best_move(board_copy, ai_color)

            if best_r is not None and best_c is not None:
                # 强制转换为原生 int，防止 numpy 类型引发绘图错误
                best_r, best_c = int(best_r), int(best_c)

                if self.stm32_controller:
                    self.stm32_controller.execute_move(best_r, best_c)
                else:
                    print(f"🎯 [指令下发] 请把 {color_name} 放在：行 {best_r}, 列 {best_c}")

                # 🌟 发射安全信号给主线程
                self.ai_move_ready_signal.emit(best_r, best_c, ai_color)
            else:
                self.ai_move_failed_signal.emit()

        except Exception as e:
            print(f"❌ 后台执行线程发生严重错误: {e}")
            self.ai_move_failed_signal.emit()

    # 🌟 信号接收者 1：成功算出落子
    def set_pending_move(self, r, c, color):
        self.ai_is_thinking = False
        self.pending_ai_move = {'row': r, 'col': c, 'color': color}
        color_name = "黑子" if color == Stone.BLACK else "白子"
        self.status_label.setText(f"👉 请在红圈处放置实体 {color_name}")
        self.btn_ai_move.setText(f"⏳ 等待放置...")
        self.blink_timer.start(500)
        self.board_widget.update()  # 强制立刻刷新 UI 画出虚影

    # 🌟 信号接收者 2：计算失败（比如棋盘满了）
    def handle_ai_failed(self):
        self.ai_is_thinking = False
        self.status_label.setText("状态：等待落子...")
        self.btn_ai_move.setEnabled(True)

    def reset_game(self):
        self.board.reset()
        self.pending_ai_move = None
        self.blink_timer.stop()
        self.ai_is_thinking = False
        self.btn_ai_move.setEnabled(True)
        self.btn_ai_move.setText("🤖 让 AI 下一步")
        self.board_widget.update()
        self.status_label.setText("状态：已重置，等待开局")

    def closeEvent(self, event):
        self.update_timer.stop()
        if getattr(self, "camera_thread", None): self.camera_thread.stop()
        if getattr(self, "stm32_controller", None): self.stm32_controller.close()
        super().closeEvent(event)