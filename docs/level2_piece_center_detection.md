# 第 2 关：棋子检测框与中心坐标输出

## 目标

在已经能识别黑白棋的基础上，完成比赛第 2 关展示能力：

- 打开普通 USB 摄像头；
- 实时识别黑棋和白棋；
- 对每个棋子画检测框；
- 在棋子中心画小圆点；
- 在画面和终端输出棋子类型与像素中心坐标；
- 支持多个黑棋、多个白棋；
- 按 `q` 退出。

## 当前硬件记录

- 摄像头类型：普通 USB 摄像头。
- 当前可用摄像头 ID：`2`。
- 不使用 iVCam。

## 2026-06-02 现场测试问题

用户现场测试 `piece_center_detect.py` 时发现：

- 白棋没有被检测出来；
- 棋盘黑色网格线/星位被误识别成黑棋；
- 当前 USB 摄像头在 `camera-id=2`。

第二次现场测试发现：

- 多个黑棋贴近或堆积在一起时，黑棋也可能完全检测不到。

问题原因判断：

- 第一版脚本主要依赖 HSV 全局阈值。
- 黑棋检测使用低亮度阈值时，容易把棋盘线、星位也当成黑棋。
- 白棋与浅色棋盘背景亮度接近，使用全局白色阈值时容易和棋盘背景粘连，导致白棋轮廓无法单独分离。
- 黑棋互相贴近时，Hough 圆的边缘不完整，且每个棋子的背景环会被旁边黑棋污染，导致圆检测和局部亮度差分类同时失败。

## 修复策略

第二版脚本改为默认使用圆形候选检测：

1. 用 Hough 圆检测先找“像棋子一样的圆形候选”；
2. 对每个圆形候选计算中心区域和周围背景的局部亮度差；
3. 中心明显更暗则判定为黑棋；
4. 中心比周围更亮、且饱和度较低则判定为白棋；
5. 黑棋分类不只看平均亮度，还看暗像素比例和较暗分位数，避免高光影响；
6. 增加黑棋暗斑补救检测，用距离变换从贴近的黑棋团中找多个中心；
7. 保留 HSV 轮廓检测作为 `--method contour` fallback；
8. 默认摄像头 ID 改为 `2`；
9. 增加 `--roi x,y,w,h`，用于排除棋盘旁边的棋盒或其他干扰物。

## 推荐运行命令

默认 USB 摄像头：

```powershell
python .\piece_center_detect.py --print-every 10
```

推荐现场调参模式：

```powershell
python .\piece_center_detect.py --tune --no-labels --print-every 10
```

调参窗口中建议优先拖这些滑条：

- 满屏误检：先提高 `HoughParam2`，再提高 `MinRadius` 或打开 `UseROI` 限定棋盘区域。
- 棋盘线/星位误检成黑棋：提高 `BlackDiff`、降低 `BlackP20Max`、提高 `BlackDarkRatio`，或提高 `BlackBlobDist`。
- 白棋漏检：降低 `WhiteDiff`，再降低 `WhiteVMin`。
- 背景误检成白棋：提高 `WhiteDiff`，提高 `WhiteVMin`，降低 `WhiteSMax`。
- 多个黑棋贴在一起漏检：降低 `BlackBlobDist`，适当提高 `BlackBlobVMax`。

调好后，在预览窗口按 `p`，终端会打印当前可复用命令。

显式指定 USB 摄像头：

```powershell
python .\piece_center_detect.py --camera-id 2 --print-every 10
```

如果画面右侧棋盒被误识别，限制检测区域：

```powershell
python .\piece_center_detect.py --camera-id 2 --roi 70,40,590,580 --print-every 10
```

如果白棋仍然漏检，降低白棋局部亮度差要求：

```powershell
python .\piece_center_detect.py --camera-id 2 --white-diff 3 --white-v-min 120 --print-every 10
```

如果误检背景为白棋，提高白棋条件：

```powershell
python .\piece_center_detect.py --camera-id 2 --white-diff 10 --white-v-min 155 --white-s-max 90 --print-every 10
```

如果棋盘线或星位仍被误检为黑棋，提高最小半径或黑棋局部亮度差：

```powershell
python .\piece_center_detect.py --camera-id 2 --min-radius 14 --black-diff 28 --print-every 10
```

如果多个黑棋贴在一起仍然检测不到，放宽黑棋补救检测：

```powershell
python .\piece_center_detect.py --camera-id 2 --black-blob-v-max 145 --black-blob-min-distance 6 --print-every 10
```

如果黑色棋盒也被检测出来，优先使用 ROI 限定棋盘区域：

```powershell
python .\piece_center_detect.py --camera-id 2 --roi 70,40,590,580 --print-every 10
```

也可以用滑条方式打开 ROI：

```powershell
python .\piece_center_detect.py --camera-id 2 --tune --no-labels --print-every 10
```

然后在调参窗口中把 `UseROI` 设为 `1`，拖动 `ROI_X`、`ROI_Y`、`ROI_W`、`ROI_H`，只框住棋盘区域。

## 后续建议

- 第 2 关展示可以继续使用 `piece_center_detect.py`。
- 第 3 关应接入棋盘四角标定，把像素中心坐标转换成棋盘行列 `(row, col)`。
- 若比赛展示要求统一入口，可以把 `piece_center_detect.py` 的能力并入 `tools/live_vision_monitor.py`，通过 `--draw-boxes` 和 `--print-centers` 控制。
