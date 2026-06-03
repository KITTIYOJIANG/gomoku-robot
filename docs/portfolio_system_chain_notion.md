# 硬核工程作品集：感知-决策-机械臂执行链路

更新时间：2026-06-03  
用途：Notion 展示版  
项目方向：基于视觉感知的桌面棋类具身智能机械臂系统

---

## 1. 项目一句话

本项目构建一个面向实体五子棋棋盘的机器人系统：通过 USB 摄像头识别棋盘和黑白棋，使用五子棋 AI 决策下一步落子，再把棋盘坐标发送给机械臂控制层完成落子动作。

当前重点是把工程链路讲清楚：

感知 -> 棋盘建模 -> AI 决策 -> 上位机接口 -> 机械臂控制 -> STM32/舵机执行

---

## 2. 仓库与证据来源

### 上位机 GitHub 主仓

GitHub：

https://github.com/KITTIYOJIANG/gomoku-robot

本地路径：

```text
D:\Projects\gomoku_project
```

负责内容：

- USB 摄像头读取
- OpenCV 视觉识别
- 黑白棋检测
- 棋盘矩阵建模
- 五子棋 AI 决策
- PyQt 上位机 GUI
- AI 到机械臂 mock 接口

### 下位机 GitHub 仓库

GitHub：

https://github.com/KITTIYOJIANG/gomoku-arm-controller

本地路径：

```text
D:\Projects\gomoku_arm_controller
```

负责内容：

- 棋盘坐标合法性检查
- 棋盘坐标到机械臂姿态映射
- 姿态表 pose table
- PWM 命令生成
- STM32 串口通信
- 吸盘控制
- home / place / stop / status 命令

---

## 3. 系统链路

```text
真实棋盘 / USB 摄像头
    ↓
OpenCV 感知层
    ↓
棋子检测：黑棋 / 白棋 / 中心坐标
    ↓
棋盘建模：15x15 board matrix
    ↓
五子棋 AI 决策
    ↓
输出目标棋盘坐标 row, col
    ↓
上位机机械臂适配器
    ↓
下位机控制仓库 gomoku-arm-controller
    ↓
坐标映射 / 姿态表 / PWM / 串口
    ↓
STM32 / 舵机 / 吸盘
    ↓
实体落子
    ↓
视觉复核
```

---

## 4. 模块边界

### 感知层

负责：

- 摄像头画面读取
- 黑白棋检测
- 检测框绘制
- 中心点坐标输出
- 棋盘角点和网格映射

不负责：

- AI 决策
- 机械臂运动控制
- 舵机 PWM 细节

关键文件：

- `piece_center_detect.py`
- `vision/stone_detector.py`
- `vision/board_detector.py`
- `vision/grid_mapper.py`
- `tools/live_vision_monitor.py`

### 棋盘建模层

负责：

- 将视觉结果转换为 15x15 棋盘状态矩阵
- 区分空位、黑棋、白棋
- 为 AI 提供当前局面

关键能力：

- 当前静态 benchmark 已达到黑白棋 100% recall，0 误报
- 第 3 关将继续推进：像素中心坐标 -> 棋盘行列 row/col

### 决策层

负责：

- 根据当前棋盘矩阵计算下一步
- 输出 `(row, col)`
- 支持人机对战、人人对战、AI 自对弈等模式

关键文件：

- `gomoku/ai.py`
- `gomoku/ai_logic.py`
- `gomoku/core.py`
- `demo_ai_to_arm_mock.py`

### 上位机适配层

负责：

- 保持 GUI 现有接口
- 把 AI 输出的 `(row, col)` 交给机械臂控制层
- 默认 mock，避免误触发真实硬件

关键文件：

- `gomoku/stm32_controller.py`

### 下位机机械臂控制层

负责：

- 接收 `(row, col)`
- 校验坐标是否合法
- 查询姿态表或坐标映射
- 执行动作序列
- 生成 PWM 命令
- 处理 ACK / STOP / status

关键文件：

- `arm_controller/cli.py`
- `arm_controller/stm32_controller.py`
- `arm_controller/pose_table.py`
- `arm_controller/serial_protocol.py`
- `docs/stm32_protocol.md`

---

## 5. 当前完成度

| 模块 | 完成度 | 当前状态 |
|---|---:|---|
| 五子棋规则核心 | 90% | 已有落子、胜负判断、棋盘状态 |
| AI 决策 | 80% | 能根据局面输出下一步 |
| PyQt 上位机 GUI | 75% | 已有棋盘显示、模式切换、AI 请求 |
| 静态视觉 benchmark | 100% | 黑白棋 100% recall，0 误报 |
| 第 2 关棋子中心检测 | 75% | 已有实时检测、检测框、中心点、坐标打印、滑条调参、稳定器 |
| 第 3 关像素转行列 | 45% | 有棋盘矩阵思路，待做独立演示 |
| AI 到机械臂 mock | 70% | 已证明接口边界是 `(row, col)` |
| 下位机 CLI | 65% | 支持 place / home / stop / status |
| 姿态表与标定 | 55% | 有 pose table 和四角插值方案 |
| 真实机械臂闭环 | 25% | 协议和 mock 有了，真实硬件仍需验证 |

---

## 6. 已经能展示的证据

### 视觉识别证据

静态 benchmark 命令：

```powershell
python .\tools\benchmark_vision.py --image-dir .\calibration_tools --labels .\calibration_tools\label.txt --corners "72,18;513,28;508,461;74,468"
```

当前结果：

```text
black recall: 22/22 = 100.00%
white recall: 15/15 = 100.00%
false black: 0
false white: 0
```

证据图片目录：

```text
docs/assets/benchmark_evidence_2026-05-30/
```

### 第 2 关实时检测证据

推荐现场调参命令：

```powershell
python .\piece_center_detect.py --camera-id 2 --tune --no-labels --print-every 10
```

稳定检测命令：

```powershell
python .\piece_center_detect.py --camera-id 2 --stability 7 --print-every 10
```

当前支持：

- 检测框
- 中心点
- 坐标打印
- 多棋子检测
- ROI 限制棋盘区域
- 滑条调参
- 跨帧稳定减少白子闪烁

### AI 到机械臂 mock 证据

```powershell
python .\demo_ai_to_arm_mock.py --case win_now
```

证明内容：

- 上位机负责棋局和 AI 决策
- AI 输出 `(row, col)`
- 机械臂适配层接收目标坐标
- 当前先走 mock，避免真实硬件误动作

### 下位机 mock 证据

在下位机仓库运行：

```powershell
cd D:\Projects\gomoku_arm_controller
python -m arm_controller.cli place --row 7 --col 7 --mock
```

期望最终状态：

```text
OK 7 7
```

---

## 7. 本次验证记录

验证时间：2026-06-03

上位机测试：

```text
python -m pytest tests -q
13 passed
```

上位机静态 benchmark：

```text
black recall: 22/22 = 100.00%
white recall: 15/15 = 100.00%
false black: 0
false white: 0
```

下位机测试：

```text
python -m pytest tests -q
24 passed
```

---

## 8. 当前卡点

### 卡点 1：第 2 关实时参数还没固定

影响：

- 比赛展示时可能因为光照变化出现白棋闪烁或误检

解决：

- 使用 `--tune`
- 调整 `Strictness`
- 调整 `Stability`
- 使用 `UseROI` 只框住棋盘
- 按 `p` 打印稳定命令并记录

### 卡点 2：第 3 关像素转行列还没独立演示

影响：

- 目前第 2 关输出的是像素中心 `(x, y)`
- 下一关需要输出棋盘行列 `(row, col)`

解决：

- 复用棋盘四角标定
- 将像素中心映射到 15x15 网格
- 输出每个棋子的 row/col

### 卡点 3：真实机械臂还不能说完整闭环

影响：

- 当前可展示 mock 和协议
- 真实机械臂还需要单步硬件验证

解决：

- 先验证 `status`
- 再验证 `home`
- 再验证 `stop`
- 再验证单格 `place`
- 最后再接完整闭环

---

## 9. 2026-06-06 前优先级

### P0：固定第 2 关现场参数

运行：

```powershell
python .\piece_center_detect.py --camera-id 2 --tune --no-labels --print-every 10
```

完成标准：

- 黑棋稳定框出
- 白棋稳定框出
- 中心点不明显抖动
- 终端持续打印坐标
- 棋盘线、星位、棋盒不过度误检

### P0：录制第 2 关证据

需要录制：

- OpenCV 实时检测窗口
- 检测框和中心点
- 终端坐标输出
- 按 `p` 打印的稳定命令

### P1：推进第 3 关

目标：

```text
像素中心 (x, y) -> 棋盘坐标 (row, col)
```

建议文件：

```text
piece_center_to_board.py
```

或扩展：

```text
piece_center_detect.py --show-board-coords
```

### P1：准备作品集截图

建议截图：

- 系统链路页
- 第 2 关检测窗口
- benchmark 结果
- AI 到机械臂 mock 输出
- 下位机 CLI mock 输出

---

## 10. 作品集表述

项目名称：

基于视觉感知的桌面棋类具身智能机械臂系统

一句话描述：

构建从真实棋盘视觉识别、五子棋 AI 决策到机械臂落子执行的感知-决策-行动链路，并将上位机视觉/AI 与下位机机械臂控制拆分为两个可独立测试的工程仓库。

当前可以诚实展示：

- OpenCV 实时检测黑白棋，输出检测框、中心点和像素坐标
- 静态 benchmark 黑白棋识别 100% recall，0 误报
- PyQt 上位机支持棋盘显示、AI 决策和模式切换
- AI 到机械臂 mock 接口已打通
- 下位机仓库已具备 CLI、pose table、PWM command、ACK/STOP/status 设计

当前不能夸大：

- 不要说真实机械臂完整闭环已经稳定完成
- 不要说第 2 关实时 USB 摄像头在所有光照下完全稳定
- 不要把 mock 机械臂执行说成真实硬件执行

---

## 11. Notion 使用建议

复制到 Notion 后建议这样整理：

- 将“系统链路”放在页面最上方
- 将“当前完成度”转成 Notion 表格
- 将“当前卡点”转成 3 个 Toggle
- 将“2026-06-06 前优先级”转成 To-do list
- 将“作品集表述”单独放到页面底部，后续可直接复制到简历或答辩稿
- 将未完成模块拆到任务 tracking 页：`docs/portfolio_task_tracking_notion.md`
- 如果想直接做成 Notion Task Database，可以导入：`docs/portfolio_task_database.csv`
