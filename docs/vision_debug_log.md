# Vision Debug Log / 视觉调试记录

This document records real debugging observations from the Gomoku robot vision pipeline. The purpose is to make the project reproducible and to show how vision errors are diagnosed and fixed.

本文档记录五子棋机器人视觉识别模块中的真实调试过程。目的不是只展示“跑通结果”，而是记录误检现象、原因分析、修复方法和后续问题，让项目更可复现、更像真实机器人视觉工程。

## Test Image / 测试图片

- Image path / 图片路径：`calibration_tools/my_real_board.jpg`
- Board type / 棋盘类型：15x15 Gomoku board
- Manual corners / 手动棋盘四角：

```text
80,26;513,30;517,456;86,467
```

Run command / 运行命令：

```bash
python -m vision.vision_demo --image .\calibration_tools\my_real_board.jpg --corners "80,26;513,30;517,456;86,467"
```

## Issue 1: Board Star Points Detected as Black Stones

## 问题 1：棋盘星位被误识别成黑棋

### Observation / 现象

In the first version of `vision_demo`, the output board matrix contained black stones at:

第一版 `vision_demo` 输出的 15x15 棋盘矩阵中，黑棋 `1` 出现在以下位置：

```text
(3,3), (3,11), (7,7), (11,3), (11,11)
```

These positions match the standard star points and center point of a 15x15 Gomoku board.

这些位置正好对应 15x15 五子棋盘的四个星位和天元位置。

### Cause / 原因

The first detector used only local brightness difference:

最初的检测器主要依赖局部亮度差：

```text
if center_mean < background_mean - black_threshold:
    classify as black stone
```

This works for dark stones, but board star points are also small dark circles. Therefore, small printed star points can be classified as black stones.

这种方法对黑棋有效，但棋盘星位本身也是黑色小圆点，所以会被误判为黑棋。

### Fix / 修复方法

The detector now uses both:

现在检测器同时使用：

1. Local brightness difference / 局部亮度差
2. Dark or bright pixel area ratio inside the ROI / ROI 内暗色或亮色像素面积比例

A point is classified as a black stone only if the dark region is large enough:

只有当 ROI 内暗色区域占比足够大时，才判定为黑棋：

```text
dark_ratio = pixels_darker_than_background / total_roi_pixels

if center_mean < background_mean - black_threshold
   and dark_ratio >= black_area_ratio:
       classify as black stone
```

This filters out small star points because their dark area is much smaller than a real stone.

这样可以过滤掉面积较小的星位，因为星位的暗色区域远小于真实棋子。

### Result / 结果

After adding area-ratio filtering:

加入面积比例过滤后：

- The four corner star points were no longer classified as black stones.
- The center position `(7,7)` was still classified as black.

- 四个角上的星位不再被识别成黑棋。
- 中心位置 `(7,7)` 仍然被识别成黑棋。

After checking the test image, the center position does contain a real black stone near the center, so this result is reasonable.

查看测试图片后发现，中心附近确实有一颗真实黑棋，因此 `(7,7)` 输出为黑棋是合理的。

## Issue 2: White Stone Detection Is Still Weak

## 问题 2：白棋识别仍然不够稳定

### Observation / 现象

The test image contains a white stone near the center, but the current output matrix does not reliably classify it as `2`.

测试图片中中心附近有一颗白棋，但当前输出矩阵没有稳定地将其识别为 `2`。

### Possible Causes / 可能原因

- White stones may be close to the board color under certain lighting.
- Reflection on white stones can make the local brightness distribution unstable.
- A pure grayscale threshold may not distinguish white stones from a bright board background.

- 白棋在某些光照条件下和棋盘底色接近。
- 白棋反光会导致局部亮度分布不稳定。
- 单纯灰度阈值不一定能区分白棋和偏亮的棋盘背景。

### Next Fix Plan / 后续修复计划

Potential improvements:

可尝试的改进：

1. Use HSV color features instead of grayscale only.
2. Add circularity or blob-area detection.
3. Use adaptive thresholding around each grid point.
4. Collect multiple board images and tune thresholds on a small benchmark set.
5. Later upgrade to a learning-based detector such as YOLO if classical vision is not robust enough.

1. 使用 HSV 颜色特征，而不是只使用灰度。
2. 增加圆形度或连通域面积检测。
3. 在每个棋盘交点附近使用自适应阈值。
4. 收集多张棋盘图片，建立小型测试集并调参。
5. 如果传统视觉方法不够鲁棒，后续可升级为 YOLO 等学习型检测器。

## Engineering Lesson / 工程经验

The important lesson is that a working demo is not enough. A real vision system must record:

这个问题说明，视觉项目不能只展示“能跑的 demo”。真实视觉系统需要记录：

- false positives / 误检
- false negatives / 漏检
- lighting conditions / 光照条件
- threshold choices / 阈值选择
- why a fix works / 为什么修复有效
- what still fails / 仍然失败的情况

This debugging process is useful for project reports, graduate applications, and technical interviews.

这类调试过程对项目报告、研究生申请和技术面试都很有价值。

## Interview Explanation / 面试讲法

English:

> In the first version, I used local brightness thresholds to detect stones. During testing, I found that the printed star points on the board were falsely detected as black stones. I analyzed the ROI statistics and added an area-ratio filter, so a point is classified as a stone only when the dark region occupies enough pixels. This removed the star-point false positives while preserving real black stone detection. The remaining issue is white stone detection, which I plan to improve using HSV features and adaptive local thresholds.

中文：

> 第一版视觉检测主要使用局部亮度阈值来判断黑白棋。测试时我发现棋盘上的星位会被误识别成黑棋，因为星位本身也是黑色小圆点。后来我分析了 ROI 内的像素统计，增加了暗色区域面积比例过滤，只有当暗色像素占比达到一定阈值时才判定为黑棋。这样过滤掉了星位误检，同时保留了真实黑棋检测。当前剩余问题是白棋识别还不够稳定，下一步会尝试 HSV 特征和局部自适应阈值。
