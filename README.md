# Gomoku Robot / 棋眼 Pro

Gomoku Robot 是一个面向真实棋盘人机对弈场景的智能五子棋机器人系统。项目结合五子棋规则引擎、启发式 AI、PyQt 上位机、OpenCV 视觉识别与独立机械臂控制仓库，目标是实现从真实棋盘识别到机器人自主落子的完整闭环。

> 当前仓库负责上位机、视觉识别、棋局建模、AI 决策与棋谱工具。机械臂底层控制已拆分到独立仓库：[gomoku-arm-controller](https://github.com/KITTIYOJIANG/gomoku-arm-controller)。

## Overview

长期目标链路：

```text
真实棋盘 / 摄像头图像
  -> OpenCV 棋盘识别
  -> 黑白棋子识别
  -> 15x15 棋盘状态矩阵
  -> 五子棋 AI 决策
  -> 棋盘坐标 row/col
  -> 调用 gomoku-arm-controller
  -> STM32 / 机械臂完成落子
```

English:

Gomoku Robot is a physical-board Gomoku robot host system. The long-term goal is to connect camera-based board recognition, host-side AI decision-making, and STM32-based robotic arm actuation into a complete perception-decision-action loop.

## Repository Boundary

本仓库 `gomoku-robot` 负责：

- 摄像头读取与棋盘图像处理
- 透视变换与 15x15 棋盘状态矩阵生成
- 五子棋规则引擎、AI 决策和 PyQt 上位机 GUI
- 命令行对弈、棋谱记录、棋谱回放和 AI 自对弈实验
- 将 AI 落子结果以 `(row, col)` 形式交给机械臂控制层

独立仓库 `gomoku-arm-controller` 负责：

- 棋盘坐标合法性检查
- 棋盘坐标到机械臂坐标映射
- STM32 串口协议和 PWM 指令生成
- mock 模式、机械臂示教、硬件标定和动作执行

这种拆分让上位机和机械臂控制可以分别开发、测试和展示。

## Current Status

已完成 / 已具备雏形：

- 五子棋规则引擎：落子、合法性判断、胜负判定、棋盘表示
- 启发式 AI：冲四、堵四、防守活三、浅层搜索
- CLI 人机对弈与本地双人对弈
- AI 自对弈与实验统计
- JSON 棋谱记录与回放
- PyQt 上位机界面
- 摄像头实时读取
- 基于 OpenCV 的透视变换
- 局部亮度差分的黑白棋检测
- 15x15 棋盘状态矩阵更新
- 与独立机械臂控制仓库的适配层
- 机械臂 mock 调用验证

仍在推进：

- 棋盘识别鲁棒性提升
- 真实 STM32 机械臂联调
- 落子误差、识别准确率和完整对局成功率统计
- 视觉模块进一步拆分为 `vision/board_detector.py`、`vision/grid_mapper.py`、`vision/stone_detector.py`

## Key Features

### Game and UI

- CLI human-vs-AI mode
- CLI human-vs-human mode
- PyQt host GUI
- Board rendering and AI decision request
- Game record saving and replay support
- Device integration area for camera and robotic arm status

### AI and Engine

- `GomokuBoard`
  - 15x15 board
  - legal move validation
  - player switching
  - win detection in horizontal, vertical and diagonal directions
- `HeuristicAI`
  - one-move win detection
  - opponent immediate-win blocking
  - open-three defense
  - window-based heuristic scoring
  - shallow minimax-style search
- `RandomAI`
  - random legal move baseline

### Recording and Experiments

- JSON kifu-style game record
- CLI replay
- AI self-play experiments:
  - Heuristic vs Heuristic
  - Heuristic vs Random
  - Random vs Heuristic

## Tech Stack

- Python
- OpenCV
- NumPy
- PyQt5
- pyserial
- pytest
- STM32 / servo controller

## Project Structure

```text
gomoku-robot/
├─ README.md
├─ requirements.txt
├─ main.py
├─ gomoku/
│  ├─ __init__.py
│  ├─ core.py
│  ├─ ai.py
│  ├─ ai_logic.py
│  ├─ cli.py
│  ├─ gui_qt.py
│  ├─ camera_interface.py
│  ├─ config.py
│  ├─ record.py
│  ├─ replay.py
│  ├─ selfplay.py
│  ├─ ai_debug.py
│  └─ stm32_controller.py
├─ calibration_tools/
├─ arm/
├─ docs/
├─ tests/
└─ records/
```

## Setup

Recommended Python version: Python 3.9+

Install dependencies:

```bash
pip install -r requirements.txt
```

Recommended local layout:

```text
D:/Projects/gomoku_project
D:/Projects/gomoku_arm_controller
```

## Usage

### Run the Host GUI

```bash
python main.py
```

By default, the arm controller adapter uses mock mode to avoid moving real hardware accidentally:

```bash
set GOMOKU_ARM_MOCK=1
python main.py
```

To use real serial control after hardware is ready:

```bash
set GOMOKU_ARM_MOCK=0
python main.py
```

### Run CLI Gomoku

```bash
python -m gomoku.cli
```

Supported input formats:

- `H8`
- `8 8`

### Run AI Self-Play

```bash
python -m gomoku.selfplay
```

### Run Record Replay

```bash
python -m gomoku.replay
```

### Run AI Debug Cases

```bash
python -m gomoku.ai_debug
```

### Run Tests

```bash
python -m pytest tests
```

## Arm Controller Integration Test

Run inside this repository:

```bash
python -c "from gomoku.stm32_controller import STM32Controller; c=STM32Controller(); c.execute_move(7, 7); c.close()"
```

Run directly inside the arm controller repository:

```bash
python -m arm_controller.cli place --row 7 --col 7 --mock
```

## AI Design

The current `HeuristicAI` follows these principles:

1. Forcing moves first
   - If there is a one-move win, play it.
   - If the opponent has a one-move win, block it immediately.

2. Open-three defense
   - Scan length-5 windows for open-three patterns.
   - Prefer to block such patterns at their endpoints.

3. Heuristic evaluation
   - Count player and opponent stones in each 5-cell window.
   - Ignore blocked windows occupied by both sides.
   - Reward longer chains and heavily penalize opponent 3/4-in-a-row threats.

4. Shallow search
   - Simulate my move and the opponent's strongest reply.
   - Choose the move with the best score under this worst-case response.

## Hardware and Vision Plan

### Camera and Vision

The planned vision pipeline is:

- detect board area
- apply perspective transform
- locate 15x15 grid points
- detect black and white stones
- output a board matrix where `0 = empty`, `1 = black`, `2 = white`
- synchronize the recognized state with `GomokuBoard` and the PyQt GUI

### STM32 and Robotic Arm

The planned host-to-arm protocol is:

```text
P x y\n
OK x y\n
ERR code\n
```

The host project sends board coordinates. The standalone arm controller handles coordinate mapping, serial commands, PWM actions, calibration and hardware safety.

## Documentation

- `docs/arm_controller_integration.md`: boundary between this host project and the standalone arm controller.

## Resume Description

中文：

- 开发面向真实棋盘人机对弈场景的智能五子棋机器人上位机系统，集成 PyQt GUI、OpenCV 棋盘识别、15x15 棋盘状态矩阵生成、启发式 AI 决策、棋谱记录/回放与独立机械臂控制适配层。
- 将机械臂底层控制从上位机仓库中解耦，设计为独立 `gomoku-arm-controller` 项目，通过抽象棋盘坐标 `(row, col)` 完成上位机与 STM32 机械臂控制层的边界划分。

English:

- Developed the host-side software for a physical Gomoku robot system, integrating a PyQt GUI, OpenCV-based board recognition, 15x15 board-state modeling, heuristic AI decision-making, game recording/replay, and an adapter to a standalone robotic arm controller.
- Decoupled low-level robotic arm control from the host application by defining a clean board-coordinate interface between the vision/AI system and the STM32-based actuation layer.

## Roadmap

- Improve board recognition robustness
- Split vision logic into standalone modules
- Add benchmark images and recognition accuracy statistics
- Add integration examples with `gomoku-arm-controller`
- Complete real STM32 mechanical arm placement validation
- Record placement error, recognition accuracy and full-game success rate
