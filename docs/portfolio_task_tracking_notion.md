# 硬核工程作品集：任务追踪页

更新时间：2026-06-03  
用途：Notion 任务库 / 子页面拆分版  
对应主页面：`docs/portfolio_system_chain_notion.md`

---

## 1. 使用方式

这个页面用于把“当前完成度”里的未完成模块拆成可 tracking 的任务。

推荐 Notion 结构：

- 主页面：放系统结构图、模块清单、完成度总览
- 子页面或任务数据库：放本页每一个任务块
- 每个任务块维护状态、优先级、验收标准、证据路径和下一步动作

建议数据库字段：

- `Status`：Not started / In progress / Blocked / Done
- `Priority`：P0 / P1 / P2
- `Module`：Perception / Board Mapping / AI / GUI / Host-Arm Adapter / Arm Controller / Evidence
- `Repo`：Upper / Arm / Both
- `Type`：Parent / Subtask
- `Parent Task`：所属父任务
- `Progress`：模块完成度
- `Due`：截止日期
- `Evidence`：截图、命令输出、GitHub 文件、视频
- `Next Action`：下一步动作

如果要直接导入 Notion 数据库，也可以使用：

```text
D:\Projects\gomoku_project\docs\portfolio_task_database.csv
```

### 1.1 父任务表

父任务对应你截图里的“当前完成度”每一行，用来表示一个模块整体状态。

| Task ID | 父任务 | Status | Priority | Module | Progress | Repo | 下一步 |
|---|---|---|---|---|---:|---|---|
| MOD-01 | 五子棋规则核心 | In progress | P2 | Core Rules | 90% | Upper | 补边界测试和作品集证据 |
| MOD-02 | AI 决策 | In progress | P1 | AI | 80% | Upper | 记录 AI 输入局面和输出下一步的演示 |
| MOD-03 | PyQt 上位机 GUI | In progress | P1 | GUI | 75% | Upper | 接入视觉识别矩阵展示 |
| MOD-04 | 静态视觉 benchmark | Done | P2 | Perception | 100% | Upper | 作为不可回退基线保留 |
| MOD-05 | 第 2 关棋子中心检测 | In progress | P0 | Perception | 75% | Upper | 固定 USB 摄像头实时检测参数并录证据 |
| MOD-06 | 第 3 关像素转行列 | Not started | P1 | Board Mapping | 45% | Upper | 做独立 demo，把像素中心转成 `(row, col)` |
| MOD-07 | AI 到机械臂 mock | In progress | P1 | Host-Arm Adapter | 70% | Both | 补 mock 命令链路截图 |
| MOD-08 | 下位机 CLI | In progress | P1 | Arm Controller | 65% | Arm | 整理 README、CLI 示例和测试证据 |
| MOD-09 | 姿态表与标定 | In progress | P2 | Calibration | 55% | Arm | 做真实四角/中心点标定 |
| MOD-10 | 真实机械臂闭环 | Not started | P2 | Full Loop | 25% | Both | 先完成单步真实硬件验证 |

### 1.2 子任务表

子任务对应每个未完成模块下面要继续推进的小任务。导入 Notion 后，建议用 `Parent Task` 字段关联到父任务。

| Task ID | 子任务 | Parent Task | Status | Priority | 验收标准 | 下一步 |
|---|---|---|---|---|---|---|
| SUB-01 | 补规则核心边界测试证据 | MOD-01 | Not started | P2 | 有测试输出或截图证明胜负判断可靠 | 运行规则测试并截图 |
| SUB-02 | 记录 AI 决策演示 | MOD-02 | Not started | P1 | 给定棋盘状态后能看到 AI 输出下一步 | 准备 2 到 3 个典型局面 |
| SUB-03 | GUI 显示视觉矩阵 | MOD-03 | Not started | P1 | GUI 能显示识别出的 15x15 board matrix | 找到 GUI 棋盘状态入口 |
| SUB-04 | 保留静态 benchmark 回归 | MOD-04 | Done | P2 | detector 调参后旧 benchmark 不退化 | 每次改视觉后运行 benchmark |
| SUB-05 | 固定第 2 关现场参数 | MOD-05 | In progress | P0 | 黑白棋框、中心点、坐标稳定显示 | 用 `--tune` 调参并按 `p` 打印 |
| SUB-06 | 录制第 2 关演示证据 | MOD-05 | Not started | P0 | 有窗口截图、终端输出截图、演示视频 | 录 10 到 30 秒 USB 摄像头检测 |
| SUB-07 | 改善白棋闪烁 | MOD-05 | In progress | P0 | 白棋不再频繁消失/出现 | 调 `--stability`、WhiteGain、WhiteMin |
| SUB-08 | 改善黑棋堆叠漏检 | MOD-05 | In progress | P0 | 聚集黑棋能尽量分离成多颗 | 调 Hough 半径、BlobDist、RescueBlack |
| SUB-09 | 实现像素到棋盘坐标 demo | MOD-06 | Not started | P1 | 输出 `(x, y) -> (row, col)` | 新建或扩展 `piece_center_to_board.py` |
| SUB-10 | 在画面上显示棋盘行列 | MOD-06 | Not started | P1 | 标签显示 `Black (row, col)` / `White (row, col)` | 接入透视变换或四角插值 |
| SUB-11 | 输出完整棋盘矩阵 | MOD-06 | Not started | P1 | 终端能打印 15x15 矩阵 | 根据所有棋子中心填充矩阵 |
| SUB-12 | 补 AI 到机械臂 mock 证据 | MOD-07 | Not started | P1 | 日志能看到 AI 输出和 `place row col` | 运行 mock demo 并截图 |
| SUB-13 | 明确真实硬件安全边界 | MOD-07 | Not started | P1 | 文档说明 mock 不等于真实动作 | 更新作品集说明 |
| SUB-14 | 整理下位机 README | MOD-08 | Not started | P1 | README 说明 CLI、协议、pose table | 修改 arm repo README |
| SUB-15 | 补下位机 CLI 测试截图 | MOD-08 | Not started | P1 | 有 `place/home/stop/status` 输出证据 | 在 arm repo 运行 CLI 示例 |
| SUB-16 | 标定棋盘四角姿态 | MOD-09 | Not started | P2 | 有四角真实姿态数据 | 手工移动机械臂记录 PWM/姿态 |
| SUB-17 | 建立真实 pose table | MOD-09 | Not started | P2 | 有可追踪的 `poses.real.json` 或等价文件 | 写入并验证单点姿态 |
| SUB-18 | 真实硬件单步验证 | MOD-10 | Not started | P2 | `status/home/stop/place` 单步可运行 | 从 `status` 和 `home` 开始 |
| SUB-19 | 加闭环安全确认 | MOD-10 | Not started | P2 | 执行动作前需要人工确认或置信度门槛 | 先在 mock 层实现安全开关 |
| SUB-20 | 动作后视觉复核 | MOD-10 | Not started | P2 | 机械臂落子后摄像头能复核棋盘变化 | 等真实单步动作稳定后再接入 |

---

## 2. 当前总览

### 已经可以作为作品集证据展示

- 五子棋规则核心：已有落子、胜负判断、棋盘状态
- AI 决策：能根据局面输出下一步棋
- 静态视觉 benchmark：黑棋 22/22，白棋 15/15，0 误报
- 第 2 关棋子中心检测：已有实时检测、检测框、中心点、坐标打印、滑条调参、稳定器
- AI 到机械臂 mock：已证明接口边界是 `(row, col)`
- 下位机 CLI：已有 `place` / `home` / `stop` / `status`

### 还需要继续 tracking 的部分

- 第 2 关实时 USB 摄像头稳定性
- 第 3 关像素坐标转棋盘行列
- GUI 与真实检测结果联动展示
- 下位机真实硬件验证
- 机械臂姿态表真实标定
- 完整感知-决策-执行闭环

---

## 3. P0 任务

### P0-01：完成作品集系统链路任务页

Status：In progress  
Priority：P0  
Module：Evidence  
Repo：Upper  
Due：2026-06-06

目标：

梳理感知 -> 决策 -> 机械臂执行链路，列出模块边界、当前完成度、可展示证据。

验收标准：

- 主页面能说明系统从摄像头到机械臂执行的完整链路
- 每个模块都有边界说明
- 每个模块都有当前完成度
- 每个模块都有证据路径或待补证据
- 不夸大真实机械臂闭环完成度

当前证据：

```text
D:\Projects\gomoku_project\docs\portfolio_system_chain_notion.md
D:\Projects\gomoku_project\docs\portfolio_system_chain.md
D:\Projects\gomoku_project\docs\project_progress_dashboard.md
```

下一步动作：

- 把 `portfolio_system_chain_notion.md` 复制到 Notion 主任务页
- 把本页任务块拆成 Notion 子页面或数据库条目
- 补一张真实检测窗口截图
- 补一张下位机 CLI 测试截图

---

### P0-02：固定第 2 关实时检测参数

Status：In progress  
Priority：P0  
Module：Perception  
Repo：Upper  
Due：2026-06-06

目标：

让 USB 摄像头实时画面下的黑白棋检测足够稳定，能完成比赛第 2 关展示。

验收标准：

- 能打开 USB 摄像头，当前 camera id 为 `2`
- 能同时检测多个黑棋和多个白棋
- 每个棋子有外接框
- 每个棋子中心有小圆点
- 画面上显示棋子类型和中心坐标
- 终端持续打印中心坐标
- 白棋闪烁明显降低
- 黑棋堆叠时尽量不漏检单颗棋子
- 棋盘线、星位、棋盒不被大量误识别

当前证据：

```text
D:\Projects\gomoku_project\piece_center_detect.py
D:\Projects\gomoku_project\docs\level2_piece_center_detection.md
```

推荐运行命令：

```powershell
python .\piece_center_detect.py --camera-id 2 --tune --no-labels --print-every 10
```

白棋仍闪烁时：

```powershell
python .\piece_center_detect.py --camera-id 2 --stability 7 --print-every 10
```

下一步动作：

- 用 `--tune` 找到现场光照下最稳参数
- 按 `p` 打印最终参数
- 把稳定参数记录进 `docs\level2_piece_center_detection.md`
- 录制一段第 2 关演示视频

---

### P0-03：补齐第 2 关可展示证据

Status：Not started  
Priority：P0  
Module：Evidence  
Repo：Upper  
Due：2026-06-06

目标：

让第 2 关不只是“代码存在”，而是有可以给老师、队友或作品集看的证据。

验收标准：

- 有实时检测窗口截图
- 有终端坐标输出截图
- 有不同棋子数量下的检测截图
- 有一段 10 到 30 秒演示视频
- 文档说明 camera id、运行命令、调参方法

当前证据：

```text
D:\Projects\gomoku_project\piece_center_detect.py
D:\Projects\gomoku_project\docs\level2_piece_center_detection.md
```

下一步动作：

- 截图：黑棋、白棋、混合棋局
- 截图：终端坐标输出
- 视频：按 `q` 退出前的完整检测过程
- 把证据路径追加到文档

---

## 4. P1 任务

### P1-01：实现第 3 关像素坐标转棋盘行列

Status：Not started  
Priority：P1  
Module：Board Mapping  
Repo：Upper  
Due：不确定

目标：

把第 2 关输出的像素中心 `(x, y)` 转成五子棋棋盘坐标 `(row, col)`。

验收标准：

- 输入棋子中心像素坐标
- 输入或配置四个棋盘角点
- 输出 15x15 棋盘行列坐标
- 能过滤棋盘外的点
- 能在画面上显示 `(row, col)`
- 能输出当前棋盘矩阵

当前证据：

```text
D:\Projects\gomoku_project\vision\board_mapper.py
D:\Projects\gomoku_project\piece_center_detect.py
```

建议实现方式：

- 复用当前 benchmark 的角点解析逻辑
- 使用透视变换或四角插值
- 先做独立 demo，不急着接机械臂

建议文件：

```text
D:\Projects\gomoku_project\piece_center_to_board.py
```

或扩展：

```powershell
python .\piece_center_detect.py --camera-id 2 --show-board-coords
```

下一步动作：

- 先写独立 demo
- 用鼠标或检测中心点验证坐标转换
- 再接回实时检测程序

---

### P1-02：GUI 接入实时视觉结果

Status：Not started  
Priority：P1  
Module：GUI  
Repo：Upper  
Due：不确定

目标：

让 PyQt 上位机不只显示内部棋盘，也能显示摄像头识别到的真实棋盘状态。

验收标准：

- GUI 可启动视觉检测
- GUI 可显示识别矩阵
- GUI 能区分人工输入棋局和视觉同步棋局
- GUI 中 AI 决策使用的棋盘状态来源清晰
- 不直接触发真实机械臂动作

当前证据：

```text
D:\Projects\gomoku_project\src
D:\Projects\gomoku_project\piece_center_detect.py
```

下一步动作：

- 找到 GUI 当前棋盘状态管理代码
- 给视觉结果增加一个独立入口
- 先显示矩阵，不联动机械臂

---

### P1-03：AI 决策到机械臂 mock 演示

Status：In progress  
Priority：P1  
Module：Host-Arm Adapter  
Repo：Both  
Due：不确定

目标：

证明上位机 AI 的输出可以转成下位机可理解的落子命令。

验收标准：

- AI 输出 `(row, col)`
- 上位机生成 `place row col` 或等价命令
- 下位机 mock 能接收并返回结果
- 日志中能看到完整命令链路
- 真实硬件动作仍保持关闭

当前证据：

```text
D:\Projects\gomoku_project\docs\arm_controller_integration.md
D:\Projects\gomoku_arm_controller\arm_controller\cli.py
```

下一步动作：

- 补一张 mock 命令输出截图
- 在作品集页标注这是 mock，不是真实硬件闭环
- 等第 3 关完成后再接真实坐标来源

---

### P1-04：整理下位机 GitHub 可展示状态

Status：In progress  
Priority：P1  
Module：Arm Controller  
Repo：Arm  
Due：不确定

目标：

让下位机仓库成为作品集里可以独立展示的工程模块。

验收标准：

- GitHub 仓库存在
- README 说明清楚 CLI、pose table、serial protocol
- 测试能通过
- mock 与真实硬件边界清楚
- 不把未验证硬件功能写成已完成

当前证据：

```text
D:\Projects\gomoku_arm_controller
https://github.com/KITTIYOJIANG/gomoku-arm-controller
```

当前测试状态：

```powershell
python -m pytest tests -q
```

历史结果：

```text
24 passed
```

下一步动作：

- 整理下位机 README
- 补 CLI 使用示例
- 补 mock 测试截图
- 再决定是否提交下位机仓库当前改动

---

## 5. P2 任务

### P2-01：机械臂姿态表真实标定

Status：Not started  
Priority：P2  
Module：Arm Controller  
Repo：Arm  
Due：不确定

目标：

把棋盘 `(row, col)` 映射到机械臂真实可执行姿态。

验收标准：

- 有真实标定点
- 有 pose table 文件
- 四角或多点插值能覆盖棋盘区域
- 单个棋盘点可以稳定移动到目标位置
- 吸盘高度、落子高度、抬升高度分层清楚

当前证据：

```text
D:\Projects\gomoku_arm_controller\arm_controller\pose_table.py
D:\Projects\gomoku_arm_controller\calibration
```

下一步动作：

- 先标定棋盘四角
- 再标定中心点
- 记录 `home`、`pickup`、`place` 三类姿态
- 不急着跑完整闭环

---

### P2-02：真实机械臂单步动作验证

Status：Not started  
Priority：P2  
Module：Arm Controller  
Repo：Arm  
Due：不确定

目标：

先验证单条命令能控制真实机械臂，再考虑完整闭环。

验收标准：

- `home` 可执行
- `status` 可返回
- `stop` 可立即中断
- 单个 `place row col` 可执行
- 串口 ACK 或错误码可记录
- 异常时不会继续动作

当前证据：

```text
D:\Projects\gomoku_arm_controller\arm_controller\serial_protocol.py
D:\Projects\gomoku_arm_controller\arm_controller\stm32_controller.py
D:\Projects\gomoku_arm_controller\arm_controller\cli.py
```

下一步动作：

- 确认串口号和波特率
- 先跑 `status`
- 再跑 `home`
- 最后跑单个安全位置 `place`

---

### P2-03：完整真实闭环验证

Status：Not started  
Priority：P2  
Module：Both  
Repo：Both  
Due：不确定

目标：

完成真实摄像头识别、AI 决策、机械臂落子的完整闭环。

验收标准：

- 摄像头识别当前棋局
- 第 3 关输出棋盘矩阵
- AI 输出合法下一步
- 上位机发送下位机命令
- 下位机执行机械臂动作
- 动作后摄像头复核棋盘变化
- 出现识别不确定时停止动作

当前证据：

```text
D:\Projects\gomoku_project
D:\Projects\gomoku_arm_controller
```

下一步动作：

- 等第 2 关和第 3 关稳定后再做
- 先接 mock，再接真实硬件
- 加安全开关和人工确认

---

### P2-04：建立第二批真实摄像头 benchmark

Status：Not started  
Priority：P2  
Module：Perception  
Repo：Upper  
Due：不确定

目标：

确认静态 benchmark 的 100% 结果能否迁移到真实 USB 摄像头新画面。

验收标准：

- 至少 8 组实拍图
- 每张有 raw 原图
- 每张有 annotated 标注图
- 每张有人工标签
- benchmark 能输出黑白棋 recall 和 false positives

建议目录：

```text
D:\Projects\gomoku_project\calibration_tools\live_benchmark_20260603
```

建议命令：

```powershell
python .\tools\live_vision_monitor.py --camera-id 2 --corners "72,18;513,28;508,461;74,468" --output outputs\live_detected.jpg --raw-output outputs\live_raw.jpg
```

下一步动作：

- 拍空棋盘
- 拍黑棋中心
- 拍白棋中心
- 拍低光
- 拍反光
- 拍边缘棋子
- 拍随机局
- 拍混合局

---

## 6. 建议看板视图

### 今日必须做

- P0-01：把系统链路页放进 Notion
- P0-02：调稳第 2 关实时检测参数
- P0-03：补第 2 关截图和视频证据

### 本周推进

- P1-01：第 3 关像素转棋盘行列
- P1-03：AI 到机械臂 mock 演示证据
- P1-04：下位机仓库 README 和测试证据

### 暂不急

- P2-01：真实姿态表标定
- P2-02：真实机械臂单步动作
- P2-03：完整真实闭环
- P2-04：第二批真实摄像头 benchmark

---

## 7. 每个任务子页面模板

复制下面模板到 Notion 子页面：

```text
任务名称：

Status：

Priority：

Module：

Repo：

Due：

目标：

验收标准：

- 
- 
- 

当前证据：

- 
- 

下一步动作：

- 
- 
- 

风险：

- 

完成后更新：

- 截图：
- 视频：
- 命令输出：
- GitHub commit：
```

---

## 8. 不要夸大的表述

作品集和答辩中建议保持这个边界：

- 可以说：上位机视觉、AI、mock 接口已经打通
- 可以说：第 2 关实时检测功能已经具备，正在做现场稳定性调参
- 可以说：下位机仓库已经有 CLI、协议、pose table 和测试基础
- 不要说：真实机械臂闭环已经稳定完成
- 不要说：所有光照和摄像头角度下识别都 100%
- 不要把 mock 执行说成真实硬件执行
