# 棋眼 Pro / Qiyan Pro  
基于视觉识别与机械臂控制的智能五子棋对弈系统（软件核心）

> 仓库名：`gomoku-robot`  
> This repo currently focuses on the **software core** of the system: game engine, AI, GUI, recording and experiment tools.  
> Hardware (camera + STM32 robot arm) is designed but not yet fully integrated.

---

## 1. 项目简介 / Overview

**中文说明**

棋眼 Pro 是一个面向课程大作业 / 毕设场景的 **智能五子棋对弈系统**。  
整体目标是：通过 **计算机视觉 + 上位机策略决策 + STM32 机械臂控制**，实现真实棋盘上的人机对弈。

本仓库当前实现的是 **完整的软件核心部分**：

- 五子棋规则引擎（落子、胜负判定、棋盘表示）
- 启发式 + 小搜索的 AI 对手
- 命令行 & PyQt 图形界面的人机对弈
- 对局记录、棋谱回放
- AI 自对弈与实验统计工具
- 为后续摄像头识别 / 机械臂控制预留接口与 GUI 状态区

硬件（摄像头 + STM32 机械臂）暂未接入，但协议和上位机对接思路已经规划完毕。

---

**English Overview**

**Qiyan Pro** is an intelligent Gomoku (five-in-a-row) system designed for a **course project / capstone** style scenario.  

The long-term goal is to support **real-board play** with:

- computer vision (camera detecting stones on a physical board),
- a host-side AI engine making decisions,
- and a STM32-based robot arm placing stones on the board.

This repository currently focuses on the **software core**:

- Gomoku game engine (rules, move validation, win detection)
- Heuristic AI with shallow search
- CLI & PyQt GUI for human–AI games
- Game recording and replay (kifu)
- AI self-play & experiment tools
- Placeholders and UI areas for future camera & robot arm integration

Hardware is not yet connected, but protocols and interfaces on the host side are designed.

---

## 2. 主要特性 / Key Features

### 🎮 游戏与界面 / Game & UI

- ✅ **命令行人机对弈**（Human vs AI, CLI）
- ✅ **命令行双人对弈**（Human vs Human, CLI）
- ✅ **PyQt 图形界面上位机**
  - 棋盘绘制、鼠标点击落子
  - 角色切换：你执黑 / 你执白（AI 先手或玩家先手）
  - 难度选择：简单 / 中等 / 困难（内部调整 AI 搜索范围）
  - GUI 内保存棋谱、加载并回放对局
  - 对战统计面板：总局数、胜场、平局数、平均步数
  - 设备状态区：预留给摄像头、机械臂状态显示

### 🧠 AI 与规则 / AI & Engine

- **GomokuBoard**：
  - 15×15 棋盘
  - 合法性判断、轮换执手
  - 胜负判定（横/竖/主对角/副对角五连）
- **HeuristicAI**：
  - 冲四、堵四
  - 识别并优先防守“活三”
  - 基于窗口统计的启发式评分函数
  - 简单双层搜索（两步 minimax 风格：自己走一步 + 对手走一步）
  - 可调参数：搜索半径、候选点数量等
- **RandomAI**：
  - 随机合法落子，用作基线 AI

### 📜 棋谱与回放 / Recording & Replay

- 每一局可保存为 **JSON 棋谱文件**（包含步序、执手、时间等基础信息）
- 支持：
  - 命令行回放（逐手查看）
  - GUI 回放窗口：上一步 / 下一步 / 重置

### 🧪 AI 实验工具 / AI Experiment Tools

- `selfplay.py` 支持：
  - Heuristic vs Heuristic
  - Heuristic vs Random
  - Random vs Heuristic
  - 批量运行 N 局，输出胜负统计与平均步数
  - 可选保存所有自对弈棋谱，供后续分析

---

## 3. 技术栈 / Tech Stack

- **Language**: Python 3.x
- **GUI**: PyQt5
- **Core Modules**:
  - `gomoku.core` – GomokuBoard & basic rules
  - `gomoku.ai` – HeuristicAI & RandomAI
  - `gomoku.record` – GameRecorder & JSON kifu
  - `gomoku.gui_qt` – PyQt-based host GUI
  - `gomoku.selfplay` – AI self-play / batch experiment
  - `gomoku.replay` – CLI replay
  - `gomoku.ai_debug` – AI debugging helper scripts

---

## 4. 项目结构 / Project Structure

```text
gomoku-robot/
├─ README.md                  # 项目说明（本文件）
├─ gomoku/
│  ├─ __init__.py
│  ├─ core.py                 # 棋盘与规则引擎
│  ├─ ai.py                   # HeuristicAI & RandomAI
│  ├─ cli.py                  # 命令行入口（人机/双人/自对弈）
│  ├─ ai_debug.py             # AI 调试与测试脚本
│  ├─ record.py               # GameRecorder，棋谱保存/加载
│  ├─ replay.py               # 命令行棋谱回放
│  ├─ gui_qt.py               # PyQt 图形界面上位机
│  ├─ selfplay.py             # AI 自对弈/实验工具
│  └─ ...                     # 未来扩展（摄像头、串口、硬件控制等）
├─ records/                   # 自动生成：保存棋谱的目录
└─ docs/ / images/ (optional) # 可选：文档与截图
```

## 5. 环境配置 / Setup

### 5.1 依赖 / Dependencies

建议使用 **Python 3.9+**。

安装依赖（示例）：

```bash
pip install pyqt5
```

## 6. 使用说明 / Usage
### 6.1 命令行模式（CLI）

在项目根目录（包含 gomoku/ 的目录）打开终端：
```bash
python -m gomoku.cli
```

你会看到菜单：
```
请选择模式：
1. 人机对战（你 vs AI）
2. 双人对战（本地）
3. AI 自对弈实验（AI vs AI）
```

**模式 1：人机对战（命令行）**

- 你执黑先手，AI 执白（可在代码中轻松调整）

- 落子输入示例：

  - `H8` / `h8`（列+行）

  - `8 8`（行 列，1-based）

- 系统在对局结束时提示：

  - 黑方胜 / 白方胜 / 平局

**模式 2：双人对战（命令行）**

- 双方轮流输入坐标在同一终端落子

- 适合测试规则引擎或纯人类对弈

**模式 3：AI 自对弈实验（命令行）**

进入后可以选择：

- Heuristic vs Heuristic

- Heuristic vs Random

- Random vs Heuristic

并设置：

- 对弈局数（如 10、50、100）

- 是否保存每一局棋谱到 records/ 目录

命令行版本的棋谱回放：
```bash 
python -m gomoku.replay
```

选择 `records/` 下的某个 `.json` 文件，即可一步步回放整局棋。
---
## 6.2 图形界面（PyQt GUI）

运行：
```bash
python -m gomoku.gui_qt
```

你会看到：

- 左侧：可点击落子的棋盘

- 右侧：

  - 对战统计：总局数、你的胜场、AI 胜场、平局数、平均步数

  - 设备状态区：当前显示“摄像头：未接入 / 机械臂：未接入”，预留给未来硬件模块

- 底部：

  - 状态文字：当前轮到谁（你 / AI，黑 / 白）

  - 角色选择：你执黑 / 你执白（决定谁先手）

  - 难度选择：简单 / 中等 / 困难

  - “回放棋谱”按钮

  - “新局”按钮

**GUI 功能说明：**

  - 使用鼠标点击棋盘交点落子。

  - 对局结束后，会弹窗询问是否保存棋谱至 records/。

  - 点击“回放棋谱”：

    - 选择一个 .json 棋谱文件，将打开独立的回放窗口。

    - 可通过“上一步 / 下一步 / 重置”控制棋局进度。

## 7. AI 设计概述 / AI Design Overview
**中文简述**

当前 HeuristicAI 的核心策略：
1. 强制性步骤优先：
- 若有一步可以直接胜利 → 立即下。
- 若对手有一步可以直接胜利 → 优先堵。

2. 防守活三：
- 扫描所有长度为 5 的窗口，检测模式 .○○○.（对手活三）。
- 优先在端点处落子堵截，防止对手轻松做出四连或多重威胁。

3. 启发式评分：
- 对每个 5 格窗口统计我方 / 对方连续子数。
- 如果窗口内双方都有子则视为“互相堵死”，不计分。
- 连子数越多得分越高，对手的 3 连 / 4 连惩罚权重更大（偏向防守）。

4. 两步搜索（浅层 minimax）：
- 在候选点范围内，模拟“我落一子 → 对手在其候选点中选择对我最不利的一步”。
- 在此最坏情况下得分最高的一步作为最终落子。
- 当候选点数量过大时退回单步启发式，以控制计算量。

English Summary

The current **HeuristicAI** follows these principles:

Forcing moves first:

If there is a one-move win → play it.

If the opponent has a one-move win → block it immediately.

Open-three defense:

Scan all length-5 windows for .OOO. patterns (opponent open-three).

Prefer to block such patterns at their endpoints to prevent easy threats.

Heuristic evaluation:

For each window of 5 cells, count my stones vs the opponent’s stones.

If both players occupy the same window, it is considered blocked and ignored.

Longer chains are rewarded; opponent’s 3/4-in-a-row patterns are heavily penalized.

Two-ply search:

Within a local candidate region, simulate:

my move → opponent’s best reply,

Then choose the move that maximizes my score under the opponent’s best reply.

If there are too many candidates, fall back to single-step evaluation to keep it fast.

## 8. 硬件与视觉规划（预留） / Hardware & Vision Planning (Future Work)

当前仓库侧重软件，硬件相关部分暂为 设计阶段。
The following is planned but not yet fully implemented.

### 8.1 摄像头棋盘识别（Camera + CV）

使用 OpenCV 等库，从摄像头图像中检测：

棋盘位置、网格交点

每个交点上是否有棋子及其颜色

输出一个 15×15 的状态矩阵（0 = empty, 1 = black, 2 = white）

将该矩阵与 GomokuBoard 对接，实现：

“从真实棋盘读取当前局面”

与 GUI 棋盘同步显示

### 8.2 STM32 机械臂控制（Robot Arm via STM32）

设计简单串口协议，例如：

P x y\n 表示在棋盘坐标 (x, y) 落子

OK x y\n 表示指定坐标落子成功

ERR code\n 表示发生错误

STM32 端：

接收串口数据，解析坐标

驱动机械臂移动到对应物理位置

完成夹取/吸附棋子、落子动作

上位机 GUI：

设备状态栏显示串口连接状态、最近指令与执行结果

### 8.3 Host–Device Integration

为摄像头线程/进程提供统一接口，例如：

update_board_from_camera(board_state)
将识别结果更新到 GomokuBoard 和 GUI 棋盘。

为机械臂控制提供统一控制类，例如：

send_move(x, y)
在内部调用串口发送指令，并将发送与反馈日志打印到 GUI 的 Log 区域。

在没有硬件时，可先实现 Mock 版本：

仅打印“虚拟指令”和“虚拟反馈”，方便调试整体流程。

## 9. 实验与论文撰写建议 / Suggestions for Experiments & Report

如果你将此项目用于课程大作业 / 毕设，可以考虑在论文/报告中包含：

### 9.1 实验设计 / Experiments

AI 模型对比：

HeuristicAI vs RandomAI 的胜率（使用 selfplay.py 批量实验）

不同难度参数（搜索半径、候选点数）下 HeuristicAI 的表现对比

对局样例分析：

人机对弈中的典型局面截图（AI 如何冲四、堵四、防守活三）

AI 自对弈生成的棋谱样例与形势分析

性能相关：

平均决策时间（可选）

不同参数下的速度 / 强度平衡

### 9.2 系统设计章节 / System Design Sections

系统架构：

软件模块分层图：

Engine（core） / AI / GUI / Recorder / Hardware Interface

硬件联动（摄像头 + STM32）的整体设计图

算法设计：

HeuristicAI 的启发式规则与评分函数设计

两层搜索的流程图（或伪代码）

结果与分析：

实验统计表格（胜率、平均步数）

对典型局面的 AI 决策进行解释
