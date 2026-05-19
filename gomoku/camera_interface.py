import time
import threading
from queue import Queue, Empty
import numpy as np
import cv2

from .core import GomokuBoard, Stone
from . import config


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


class CameraThread(threading.Thread):
    def __init__(self, output_queue: Queue, interval: float = 0.5, cap=None):
        super().__init__(daemon=True)
        self.output_queue = output_queue
        self.interval = interval
        self._stop_flag = threading.Event()
        self.cap = cap

        self.history_frames = []
        self.history_size = 5

        # 🌟 核心升级 1：Introduce Padding (边缘留白)
        self.padding = 40  # 往外扩 40 像素的安全区
        self.img_size = config.BOARD_PIXELS + 2 * self.padding  # expand 后的总画布大小

        rect = order_points(config.MY_REAL_CORNERS)

        # 🌟 核心升级 2：Modify 目标映射点 (全部向内 offset padding 的距离)
        pts_dst = np.array([
            [self.padding, self.padding],
            [self.padding + config.BOARD_PIXELS - 1, self.padding],
            [self.padding + config.BOARD_PIXELS - 1, self.padding + config.BOARD_PIXELS - 1],
            [self.padding, self.padding + config.BOARD_PIXELS - 1]
        ], dtype="float32")
        self.transform_matrix = cv2.getPerspectiveTransform(rect, pts_dst)

        self.editing_param = None
        self.input_string = ""

    def stop(self) -> None:
        self._stop_flag.set()

    def run(self) -> None:
        print("🎬 [CameraThread] 🌟 局部自适应定点算法已启动...")

        window_name = "Real-time Vision Monitor"
        cv2.namedWindow(window_name)

        def nothing(x):
            pass

        # 🌟 参数蜕变：现在调节的是“对比度差值”，而不是绝对灰度！
        # 默认只需要比周围木板暗 20 个灰度即为黑，亮 20 个灰度即为白
        cv2.createTrackbar('BlkDiff', window_name, config.BLK_DIFF, 100, nothing)
        cv2.createTrackbar('WhtDiff', window_name, config.WHT_DIFF, 100, nothing)
        cv2.createTrackbar('ROI_Size', window_name, 12, 30, nothing)

        param_keys = {
            ord('1'): 'BlkDiff',
            ord('2'): 'WhtDiff',
            ord('3'): 'ROI_Size'
        }

        while not self._stop_flag.is_set():
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    blk_d = cv2.getTrackbarPos('BlkDiff', window_name)
                    wht_d = cv2.getTrackbarPos('WhtDiff', window_name)
                    roi_size = max(2, cv2.getTrackbarPos('ROI_Size', window_name))

                    raw_board_state, debug_img = self.process_image(frame, blk_d, wht_d, roi_size)

                    if self.editing_param is not None:
                        text = f"Editing [{self.editing_param}]: {self.input_string}_"
                        cv2.putText(debug_img, text, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        cv2.putText(debug_img, "Press 1~3 to type difference values", (15, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

                    cv2.imshow(window_name, debug_img)

                    key = cv2.waitKey(1) & 0xFF
                    if self.editing_param is None:
                        if key in param_keys:
                            self.editing_param = param_keys[key]
                            self.input_string = ""
                    else:
                        if ord('0') <= key <= ord('9'):
                            self.input_string += chr(key)
                        elif key == 8:
                            self.input_string = self.input_string[:-1]
                        elif key in (10, 13):
                            if self.input_string:
                                cv2.setTrackbarPos(self.editing_param, window_name, int(self.input_string))
                            self.editing_param = None
                        elif key == 27:
                            self.editing_param = None

                    stable_board_state = self.get_stable_board(raw_board_state)
                    self.output_queue.put(stable_board_state)

            time.sleep(self.interval / 2.0)

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🔌 [CameraThread] 摄像头已安全释放。")

    def get_stable_board(self, raw_matrix):
        self.history_frames.append(raw_matrix)
        if len(self.history_frames) > self.history_size:
            self.history_frames.pop(0)

        size = config.BOARD_SIZE
        stable_matrix = [[0] * size for _ in range(size)]
        for r in range(size):
            for c in range(size):
                states = [frame[r][c] for frame in self.history_frames]
                if states.count(1) >= 3:
                    stable_matrix[r][c] = 1
                elif states.count(2) >= 3:
                    stable_matrix[r][c] = 2
                else:
                    stable_matrix[r][c] = 0
        return stable_matrix

    def process_image(self, frame, blk_diff, wht_diff, roi_size):
        size = config.BOARD_SIZE
        board_matrix = [[0] * size for _ in range(size)]

        # 🌟 核心升级 3：apply 像素无限拉伸复制 (borderMode)，彻底消除黑边干扰！
        warped_img = cv2.warpPerspective(
            frame,
            self.transform_matrix,
            (self.img_size, self.img_size),  # 使用 expand 后的大画布
            borderMode=cv2.BORDER_REPLICATE
        )
        debug_img = warped_img.copy()

        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        bg_size = int(config.CELL_SIZE * 0.9)

        for r in range(size):
            for c in range(size):
                # 🌟 核心升级 4：所有的中心坐标 calculate 都要加上 padding 偏移量！
                center_x = self.padding + int(c * config.CELL_SIZE)
                center_y = self.padding + int(r * config.CELL_SIZE)

                # Double check 边界，防止 overflow
                center_x = min(self.img_size - 1, center_x)
                center_y = min(self.img_size - 1, center_y)

                cv2.circle(debug_img, (center_x, center_y), 2, (0, 0, 255), -1)

                # 1. 切出目标 ROI (提取棋子本身亮度)
                x_min = max(0, center_x - roi_size)
                x_max = min(self.img_size - 1, center_x + roi_size)
                y_min = max(0, center_y - roi_size)
                y_max = min(self.img_size - 1, center_y + roi_size)
                roi = gray_blurred[y_min:y_max, x_min:x_max]
                mean_gray = np.mean(roi)

                # 2. 切出 background ROI (提取局部真实光照基准)
                bx_min = max(0, center_x - bg_size)
                bx_max = min(self.img_size - 1, center_x + bg_size)
                by_min = max(0, center_y - bg_size)
                by_max = min(self.img_size - 1, center_y + bg_size)
                bg_roi = gray_blurred[by_min:by_max, bx_min:bx_max]
                bg_mean = np.mean(bg_roi)

                # 3. 智能差分 logic
                stone_type = 0
                if mean_gray < (bg_mean - blk_diff):
                    stone_type = 1
                    cv2.circle(debug_img, (center_x, center_y), roi_size, (0, 0, 0), 2)
                elif mean_gray > (bg_mean + wht_diff):
                    stone_type = 2
                    cv2.circle(debug_img, (center_x, center_y), roi_size, (255, 255, 255), 2)

                board_matrix[r][c] = stone_type

        return board_matrix, debug_img

def consume_latest_board_state(q: Queue):
    latest = None
    try:
        while True:
            latest = q.get_nowait()
    except Empty:
        pass
    return latest


def update_board_from_camera(board: GomokuBoard, board_state) -> None:
    board.move_count = 0
    board.last_move = None
    for r in range(board.size):
        for c in range(board.size):
            v = board_state[r][c]
            stone = Stone.EMPTY
            if v == 1:
                stone = Stone.BLACK
            elif v == 2:
                stone = Stone.WHITE

            board.grid[r][c] = stone
