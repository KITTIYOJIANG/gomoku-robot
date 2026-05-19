"""
=============================================================================
【天眼视觉标定工具】 - 纯鼠标操作，拒绝手工测算！
使用方法：
1. 运行本脚本，会弹出摄像头的实时画面。
2. 用鼠标依次点击物理棋盘的四个外角，必须严格按照以下顺序：
   👉 第一点：左上角
   👉 第二点：右上角
   👉 第三点：右下角
   👉 第四点：左下角
3. 点完四个点后，控制台会自动打印出完美格式的 SRC_POINTS 代码，直接复制即可！
=============================================================================
"""

import cv2
import numpy as np

# 🎥 摄像头编号 (如果画面没出来，请把 1 改为 0 试试)
CAMERA_ID = 1

# 用于存储鼠标点击的坐标
clicked_points = []


def mouse_click(event, x, y, flags, param):
    """鼠标点击回调函数"""
    global clicked_points
    # 监听鼠标左键按下
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append([x, y])
            print(f"🎯 记录坐标 {len(clicked_points)}: X={x}, Y={y}")

            # 如果点够了四个，直接在控制台生成完美代码
            if len(clicked_points) == 4:
                print("\n" + "=" * 50)
                print("🎉 标定完成！请复制下面这段代码，替换掉 main.py 里的 SRC_POINTS：\n")
                print(f"SRC_POINTS = np.float32([")
                print(f"    [{clicked_points[0][0]}, {clicked_points[0][1]}],  # 左上角")
                print(f"    [{clicked_points[1][0]}, {clicked_points[1][1]}],  # 右上角")
                print(f"    [{clicked_points[2][0]}, {clicked_points[2][1]}],  # 右下角")
                print(f"    [{clicked_points[3][0]}, {clicked_points[3][1]}]   # 左下角")
                print(f"])")
                print("=" * 50 + "\n")
                print("💡 复制完毕后，您可以直接按 'q' 键关闭本窗口。")


def start_calibration():
    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        print("❌ 错误：打不开摄像头，请检查连接或 CAMERA_ID！")
        return

    # 创建窗口并绑定鼠标事件
    cv2.namedWindow("Click 4 Corners (TL -> TR -> BR -> BL)")
    cv2.setMouseCallback("Click 4 Corners (TL -> TR -> BR -> BL)", mouse_click)

    print("🚀 标定工具已启动！请在弹出的画面上点击棋盘的四个角。")
    print("顺序：1.左上 -> 2.右上 -> 3.右下 -> 4.左下")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 渲染引导提示文字
        cv2.putText(frame, "Click 4 Corners: TL->TR->BR->BL", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # 把已经点的点画在画面上，给客户极其丝滑的视觉反馈
        for i, pt in enumerate(clicked_points):
            # 画个红点
            cv2.circle(frame, tuple(pt), 5, (0, 0, 255), -1)
            # 标个序号
            cv2.putText(frame, str(i + 1), (pt[0] + 10, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 把点连成线，让客户确认有没有点歪
            if i > 0:
                cv2.line(frame, tuple(clicked_points[i - 1]), tuple(pt), (255, 0, 0), 2)
            if len(clicked_points) == 4:
                cv2.line(frame, tuple(clicked_points[3]), tuple(clicked_points[0]), (255, 0, 0), 2)

        cv2.imshow("Click 4 Corners (TL -> TR -> BR -> BL)", frame)

        # 按 'q' 或 'ESC' 退出
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_calibration()