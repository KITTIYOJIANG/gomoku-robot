import sys
import cv2

# 1. 在 PyQt 启动前，提前抢占和预热摄像头！
from gomoku import config
print(f"🔌 正在预热视觉引擎 (CAMERA_ID: {config.CAMERA_ID})...")
global_cap = cv2.VideoCapture(config.CAMERA_ID)

if global_cap.isOpened():
    print("✅ 视觉引擎预热成功！")
else:
    print("❌ 视觉引擎预热失败，请检查摄像头是否被其他软件占用。")

# 2. 只有在摄像头搞定后，才导入和启动 PyQt
from PyQt5.QtWidgets import QApplication
from gomoku.gui_qt import MainWindow

def main():
    app = QApplication(sys.argv)
    # 把已经打开的相机句柄 (global_cap) 传给主窗口
    window = MainWindow(cap=global_cap)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()