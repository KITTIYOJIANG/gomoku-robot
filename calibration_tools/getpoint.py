import cv2
import numpy as np

# 全局变量，用于存储点击的坐标
clicked_points = []


def mouse_callback(event, x, y, flags, param):
    """
    鼠标事件回调函数
    """
    global clicked_points, img_display

    # 监听鼠标左键按下事件
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append([x, y])
            print(f"📍 记录点 {len(clicked_points)}: 坐标 (X={x}, Y={y})")

            # 在点击的位置画一个红色的实心圆，半径为5
            cv2.circle(img_display, (x, y), 5, (0, 0, 255), -1)
            # 在旁边标注文字，显示坐标
            cv2.putText(img_display, f"{len(clicked_points)}:({x},{y})", (x + 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # 如果凑齐了4个点，画出多边形连线方便确认
            if len(clicked_points) == 4:
                pts = np.array(clicked_points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img_display, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                print("\n✅ 4个顶点已全部获取！请在图像窗口按【任意键】退出...")

            # 刷新图像显示
            cv2.imshow("Click 4 Corners", img_display)


def get_board_corners(image_path):
    """
    打开图片并让用户点击4个角点
    """
    global img_display, clicked_points
    clicked_points = []  # 初始化清空

    # 读取图片
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"❌ 找不到图片 {image_path}，请检查路径！")
        return None

    img_display = original_img.copy()

    # 创建一个可以调整大小的窗口（防止高分辨率相机拍的图太大撑爆屏幕）
    cv2.namedWindow("Click 4 Corners", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Click 4 Corners", 800, 600)

    # 绑定鼠标回调函数
    cv2.setMouseCallback("Click 4 Corners", mouse_callback)

    print("=========================================")
    print("🖱️ 请在弹出的窗口中，依次点击棋盘的4个角点！")
    print("顺序无所谓（程序会自动排序），点错请按 'q' 键退出重来。")
    print("=========================================")

    cv2.imshow("Click 4 Corners", img_display)

    # 无限循环等待，直到按键或点满4个点后按键退出
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 检查是否真的点够了4个点
    if len(clicked_points) == 4:
        # 直接转化为 float32 的 numpy 数组，完美对接你的透视变换函数！
        return np.array(clicked_points, dtype="float32")
    else:
        print("⚠️ 未完成4个点的拾取。")
        return None


# ==========================================
# 测试运行
# ==========================================
if __name__ == "__main__":
    # 这里换成你用相机刚拍下来的真实棋盘照片
    image_file = "my_real_board.jpg"

    corners = get_board_corners(image_file)

    if corners is not None:
        print("\n🎉 成功获取坐标矩阵！你可以直接把下面这行代码复制到你的主程序中：\n")
        print("my_real_corners = np.array([")
        for pt in corners:
            print(f"    [{int(pt[0])}, {int(pt[1])}],")
        print("], dtype=\"float32\")")