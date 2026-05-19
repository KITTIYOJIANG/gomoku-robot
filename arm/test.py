import serial
import time

PORT = 'COM5'  # 你的截图显示是 COM5
BAUDRATE = 115200  # 众灵主板默认波特率

try:
    print(f"🔄 正在连接 STM32 ({PORT})...")
    conn = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)  # 等待主板复位
    print("✅ 连接成功！硬件已就绪。")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    exit()

print("=" * 50)
print("🛠️ 机械臂交互测试模式")
print("测试指令 1 (单舵机): #000P1500T1000!")
print("测试指令 2 (多舵机): {#000P1500T1000!#001P1500T1000!}")
print("输入 'q' 退出程序。")
print("=" * 50)

try:
    while True:
        # 等待用户手动输入指令
        cmd = input("👉 请输入控制指令: ").strip()

        if cmd.lower() == 'q':
            break
        if not cmd:
            continue

        # 🌟 重点：强制加上 \r\n，适配所有严苛的单片机协议
        send_cmd = cmd + "\r\n"

        # 发送给 STM32
        conn.write(send_cmd.encode('utf-8'))
        print(f"➡️ 已发送: {cmd}")

except KeyboardInterrupt:
    pass
finally:
    conn.close()
    print("🔌 串口已关闭。")