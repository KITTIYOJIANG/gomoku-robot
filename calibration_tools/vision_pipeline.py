import cv2
import numpy as np

# ==========================================
# 步骤 1：定义透视变换辅助函数（保持原样）
# ==========================================
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def warp_board(image_path, pts_src, side_length=600):
    """把真实的倾斜照片拉平成标准的正方形"""
    img = cv2.imread(image_path)
    if img is None:
        print("❌ 找不到图片，请检查 my_real_board.jpg 是否在当前目录！")
        return None

    rect = order_points(pts_src)
    pts_dst = np.array([
        [0, 0],
        [side_length - 1, 0],
        [side_length - 1, side_length - 1],
        [0, side_length - 1]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(rect, pts_dst)
    warped_img = cv2.warpPerspective(img, matrix, (side_length, side_length))
    return warped_img

# ==========================================
# 步骤 2：在拉平的图像上找棋子
# ==========================================
def detect_pieces_on_warped(warped_img):
    """在 600x600 的标准上帝视角图中识别黑白子（带调试功能）"""
    output = warped_img.copy()
    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.medianBlur(gray, 3)

    # 【微调1】param2 从 22 降到 18，让稍微不那么完美的圆也能被找出来
    circles = cv2.HoughCircles(
        gray_blurred, cv2.HOUGH_GRADIENT, dp=1,
        minDist=28, param1=50, param2=24,
        minRadius=14, maxRadius=23
    )

    black_pieces = []
    white_pieces = []

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            # 提取圆心区域算平均灰度
            y_min, y_max = max(0, y - 2), min(gray.shape[0], y + 3)
            x_min, x_max = max(0, x - 2), min(gray.shape[1], x + 3)
            mean_gray = np.mean(gray[y_min:y_max, x_min:x_max])

            # 【微调2】白子阈值从 190 大幅放宽到 150（暗一点的白子也能识别）
            if mean_gray < 95:
                black_pieces.append((x, y))
                cv2.circle(output, (x, y), r, (0, 0, 0), 2)  # 画黑框
                cv2.circle(output, (x, y), 2, (0, 255, 0), -1)
            elif mean_gray > 170:
                white_pieces.append((x, y))
                cv2.circle(output, (x, y), r, (255, 255, 255), 2) # 画白框
                cv2.circle(output, (x, y), 2, (0, 0, 255), -1)
            else:
                # 【极其重要】如果找到了圆，但灰度在 95~150 之间，画黄圈并打印！
                print(f"⚠️ 发现嫌疑目标被忽略: 坐标({x},{y}), 灰度={mean_gray:.1f}")
                cv2.circle(output, (x, y), r, (0, 255, 255), 2) # 画黄框

    print(f"🎯 视觉管线报告：找到 {len(black_pieces)} 黑子，{len(white_pieces)} 白子。")
    return output, black_pieces, white_pieces

# ==========================================
# 主程序：全链路串接
# ==========================================
if __name__ == "__main__":
    # ⚠️ 【必改区】把你刚才在画图软件里找到的 4 个顶点坐标填到这里！
    # 顺序无所谓，但必须是刚好卡在 15x15 最外圈网格线交点上的四个点
    my_real_corners = np.array([
        [80, 26],
        [513, 30],
        [517, 456],
        [86, 467],
    ], dtype="float32")

    # 1. 传入真实照片，执行透视拉平 (固定输出 600x600 尺寸)
    warped_board = warp_board("my_real_board.jpg", my_real_corners, side_length=600)

    if warped_board is not None:
        # 2. 在拉平后的照片上找棋子
        final_result_img, blacks, whites = detect_pieces_on_warped(warped_board)

        # 3. 显示最终成果
        cv2.imshow("1. Bird's Eye View (Warped)", warped_board)
        cv2.imshow("2. Pieces Detected", final_result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()