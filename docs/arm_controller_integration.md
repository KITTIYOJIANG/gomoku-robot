# Arm Controller Integration

The Gomoku host project and robotic arm control project are now separated.

## Repository Boundary

`gomoku-robot` is responsible for:

- Camera input
- Board recognition
- 15x15 board matrix
- Gomoku AI decision
- PyQt host GUI
- Sending an abstract target coordinate

`gomoku-arm-controller` is responsible for:

- Board coordinate validation
- Board-to-robot coordinate mapping
- STM32 serial command generation
- Servo/PWM action sequence
- Mock-mode testing
- Hardware calibration

## Local Development Layout

Recommended local layout:

```text
D:/Projects/gomoku_project
D:/Projects/gomoku_arm_controller
```

The host project automatically tries to load the sibling arm controller repo.

You can also set:

```bash
set GOMOKU_ARM_CONTROLLER_PATH=D:\Projects\gomoku_arm_controller
```

## Mock Mode

By default, the host uses mock mode to avoid moving real hardware accidentally.

```bash
set GOMOKU_ARM_MOCK=1
python main.py
```

To use the real serial controller:

```bash
set GOMOKU_ARM_MOCK=0
python main.py
```

## Direct Arm Test

Run this inside `gomoku_arm_controller`:

```bash
python -m arm_controller.cli place --row 7 --col 7 --mock
```

When hardware is ready:

```bash
python -m arm_controller.cli place --row 7 --col 7 --port COM5
```
