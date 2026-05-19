import cv2


def start_camera(camera_id=2):
    # 1. 打开摄像头
    # 提示：如果是笔记本电脑，自带摄像头通常是 0。
    # 如果你插上 USB 摄像头后运行看到的是自己的脸，请把下面的 0 改成 1 或 2！
    cap = cv2.VideoCapture(camera_id)

    # 可选：尝试强制设置摄像头分辨率（如果你买的是 720p 或 1080p）
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print(f"❌ 无法打开摄像头 {camera_id}！请检查 USB 接口，或者尝试更改 camera_id。")
        return

    print("✅ 摄像头已成功启动！")
    print("-----------------------------------------")
    print("👉 调整你的支架，让棋盘尽量居中且填满画面。")
    print("👉 按 's' 键：保存当前画面（用于透视变换标定）")
    print("👉 按 'q' 键：关闭相机并退出程序")
    print("-----------------------------------------")

    while True:
        # 2. 逐帧读取画面
        ret, frame = cap.read()
        if not ret:
            print("❌ 无法接收画面，摄像头可能被拔出。")
            break

        # 3. 显示画面
        cv2.imshow("Gomoku Live View", frame)

        # 4. 键盘监听
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("退出监控。")
            break
        elif key == ord('s'):
            # 按 s 键保存当前这一帧
            filename = "my_real_board.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 咔嚓！画面已成功保存为: {filename}")
            print("快去用 Windows 画图工具打开它，找棋盘四个角的坐标吧！")

    # 5. 释放资源
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # 如果笔记本自带摄像头，外接 USB 摄像头通常是 1
    start_camera(camera_id=2)