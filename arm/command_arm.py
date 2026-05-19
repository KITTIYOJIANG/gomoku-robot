import serial
import time

PORT = 'COM5'  # ⚠️ 换成你的真实端口
BAUDRATE = 115200

try:
    print(f"🔌 正在连接 (Connecting to) 机械臂端口: {PORT}...")
    arm = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)

    # 初始化：全部归中站立，同时【气泵必须默认关闭 (0500)】
    pwms = {0: 1500, 1: 1500, 2: 1500, 3: 1500, 4: 1500, 5: 500}
    arm.write(b"{#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#005P0500T1000!}\r\n")
    time.sleep(1.5)

    print("\n" + "=" * 55)
    print("🎮 天机手：机械臂键盘示教器 (Interactive Teach Pendant)")
    print("=" * 55)
    print("【玩法说明 (Instructions)】")
    print("👉 微调关节：舵机编号 增减数值 (例: 1 -50)")
    print("👉 开启气泵：输入 s (Suction)")
    print("👉 关闭气泵：输入 r (Release)")
    print("👉 查看状态：输入 i (Info)")
    print("👉 生成代码：输入 p (Print Code)")
    print("👉 退出程序：输入 q (Quit)")
    print("=" * 55 + "\n")


    def print_status():
        """实时 display 所有舵机的 parameters"""
        pump_state = "🟢 吸气 (ON)" if pwms[5] > 1500 else "⚪ 放气 (OFF)"
        print(f"📊 当前姿态 (Current Posture):")
        print(f"   [0 底座]: {pwms[0]:<4} | [1 大臂]: {pwms[1]:<4} | [2 小臂]: {pwms[2]:<4}")
        print(f"   [3 腕部]: {pwms[3]:<4} | [4 旋转]: {pwms[4]:<4} | [5 气泵]: {pump_state}")
        print("-" * 55)


    # Startup 时先显示一次默认状态
    print_status()

    while True:
        cmd = input("\n⌨️ 请下达指令 (Command): ").strip()

        if cmd.lower() == 'q':
            print("👋 退出示教器 (Exiting).")
            break

        elif cmd.lower() == 'p':
            print("\n🎯 【完美坐标诞生，直接 copy 下面这行】 🎯")
            # 自动 format 好可以直接在主控代码中引用的 string
            print(
                f"{{#000P{pwms[0]:04d}T0800!#001P{pwms[1]:04d}T0800!#002P{pwms[2]:04d}T0800!#003P{pwms[3]:04d}T0800!}}")
            print("-" * 40 + "\n")
            continue

        elif cmd.lower() == 'i':
            print_status()
            continue

        elif cmd.lower() == 's':
            pwms[5] = 2500  # 假设 2500 为开启气泵的高电平
            arm.write(f"{{#005P2500T0500!}}\r\n".encode('utf-8'))
            print("💨 气泵已 activate！")
            print_status()
            continue

        elif cmd.lower() == 'r':
            pwms[5] = 500  # 假设 500 为关闭气泵的低电平
            arm.write(f"{{#005P0500T0500!}}\r\n".encode('utf-8'))
            print("🛑 气泵已 deactivate！")
            print_status()
            continue

        # Process 数字微调指令
        try:
            parts = cmd.split()
            if len(parts) != 2:
                raise ValueError

            joint = int(parts[0])
            diff = int(parts[1])

            if joint not in pwms:
                print("❌ Invalid Index: 舵机号只能是 0~5！")
                continue

            if joint == 5:
                print("⚠️ 5号口是气泵，请直接使用 's' 或 'r' 来 control！")
                continue

            # Calculate 新值并进行物理限幅保护
            new_pwm = pwms[joint] + diff
            new_pwm = max(500, min(2500, new_pwm))
            pwms[joint] = new_pwm

            # Transmit 单步微调指令 (500ms 缓慢移动)
            send_str = f"{{#{joint:03d}P{new_pwm:04d}T0500!}}\r\n"
            arm.write(send_str.encode('utf-8'))
            print(f"✅ 执行成功 (Executed): 舵机 {joint} 更新到了 {new_pwm}")

            # 动作执行后自动 update 显示信息
            print_status()

        except Exception:
            print("❌ 指令 Format Error！请检查拼写，例如: 1 -50 或直接输入字母 s/r")

    # 退出前安全关闭气泵
    arm.write(b"{#005P0500T0500!}\r\n")
    arm.close()

except Exception as e:
    print(f"❌ 串口连接失败 (Connection Failed): {e}")