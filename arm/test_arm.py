import serial
import time

# ⚠️ 确保端口号正确
PORT = 'COM5'
BAUDRATE = 115200


def send_cmd(ser, cmd_str, wait_time=0):
    """发送指令并自动等待动作完成"""
    print(f"📡 发送指令: {cmd_str}")
    ser.write((cmd_str + '\r\n').encode('utf-8'))
    if wait_time > 0:
        time.sleep(wait_time)


try:
    print(f"🔌 正在连接机械臂 (端口: {PORT})...")
    arm = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)  # 等待复位稳定
    print("✅ 连接成功！开始执行完整的【抓取与放置】动作流...\n")

    # ==========================================
    # 🌟 固定状态定义区
    # ==========================================
    PUMP_ON = "#005P2500T0000!"  # 开启抽气
    PUMP_OFF = "#005P0500T0000!"  # 关闭抽气
    WRIST_ROLL = "#004P1500T0000!"  # 4号腕部自转永远居中

    # 1. 安全复位点 (Home) - 身体直立，气泵关闭
    CMD_HOME = "{#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!" + WRIST_ROLL + PUMP_OFF + "}"

    # ==========================================
    # 🎯 坐标填入区 (请把你用示教器测出的结果填到这里！)
    # 物理极性提醒：1号越小越下压，2号越大越下压
    # ==========================================

    # 2. 取子悬停点 (Hover) - 在固定取料点正上方 3~5 厘米处悬停
    # 👉 把你测出的悬停高度坐标填在这里 (大臂稍大，小臂稍小)
    CMD_HOVER_PICK = "{#000P1500T1000!#001P1000T1000!#002P1700T1000!#003P0800T1000!}"

    # 3. 取子接触点 (Down) - 垂直下降完美贴合棋子
    # 👉 把你测出的贴合高度坐标填在这里 (大臂比上面小，小臂比上面大)
    CMD_DOWN_PICK = "{#000P1500T0500!#001P1150T0500!#002P1650T0500!#003P1500T0500!}"

    # 4. 落子悬停点 (Hover Drop) - 在棋盘目标点正上方悬停
    # (如果是测试，可以先让它在原地下放，或者转动底座#000)
    CMD_HOVER_DROP = "{#000P1200T1000!#001P1400T1000!#002P1400T1000!#003P1500T1000!}"

    # 5. 落子接触点 (Down Drop) - 垂直下降贴合棋盘
    CMD_DOWN_DROP = "{#000P1200T0500!#001P1150T0500!#002P1650T0500!#003P1500T0500!}"

    # ==========================================
    # 🎬 核心动作流执行 (逻辑时序极其严格，不可随意调换)
    # ==========================================
    print("🎬 [步骤 1] 机械臂复位至安全点...")
    send_cmd(arm, CMD_HOME, wait_time=1.5)

    print("🎬 [步骤 2] 移动至【取料区】上方悬停...")
    send_cmd(arm, CMD_HOVER_PICK, wait_time=1.5)

    print("🎬 [步骤 3] 开启气泵，建立真空...")
    send_cmd(arm, "{" + PUMP_ON + "}", wait_time=0.5)

    print("🎬 [步骤 4] 垂直下压，吸取棋子！")
    send_cmd(arm, CMD_DOWN_PICK, wait_time=0.8)

    print("🎬 [步骤 5] 保持吸力，垂直抬起回悬停点...")
    send_cmd(arm, CMD_HOVER_PICK, wait_time=1.0)

    print("🎬 [步骤 6] 携带棋子，平移至【落子目标】上方悬停...")
    send_cmd(arm, CMD_HOVER_DROP, wait_time=1.5)

    print("🎬 [步骤 7] 垂直下压，准备落子...")
    send_cmd(arm, CMD_DOWN_DROP, wait_time=0.8)

    print("🎬 [步骤 8] 关闭气泵，释放棋子！")
    send_cmd(arm, "{" + PUMP_OFF + "}", wait_time=0.5)

    print("🎬 [步骤 9] 失去吸力，垂直抬起离开棋子...")
    send_cmd(arm, CMD_HOVER_DROP, wait_time=1.0)

    print("🎬 [步骤 10] 任务完美结束，回归安全点！")
    send_cmd(arm, CMD_HOME, wait_time=1.5)

    print("🎉 一套完美的 Pick and Place 动作流执行完毕！")
    arm.close()

except Exception as e:
    print(f"❌ 报错啦：{e}")