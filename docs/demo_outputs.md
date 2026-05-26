# Demo Outputs

This file records reproducible command outputs for the two-repository Gomoku robot system.

## Environment

Local repositories:

```text
D:/Projects/gomoku_project
D:/Projects/gomoku_arm_controller
```

Arm mode:

```powershell
$env:GOMOKU_ARM_MOCK='1'
```

## Test Baseline

Host project:

```powershell
cd D:\Projects\gomoku_project
python -m pytest tests -q -p no:cacheprovider
```

Result:

```text
9 passed in 0.41s
```

Arm controller project:

```powershell
cd D:\Projects\gomoku_arm_controller
python -m pytest -q -p no:cacheprovider
```

Result:

```text
7 passed in 0.04s
```

## AI-to-Arm Mock Integration

### Empty Board

Command:

```powershell
cd D:\Projects\gomoku_project
$env:GOMOKU_ARM_MOCK='1'
python .\demo_ai_to_arm_mock.py --case empty
```

Result:

```text
[Demo] case=empty
[Demo] ai_stone=BLACK
[Demo] selected_move=row=7, col=7
[ArmAdapter] Connected to standalone arm controller (mock mode).
[ARM] place_stone(row=7, col=7, mock=True)
[MOCK TX] {#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[MOCK TX] {#005P0500T0300!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[Demo] arm_execute_ok=True
```

### Block Four

Command:

```powershell
python .\demo_ai_to_arm_mock.py --case block_four
```

Result:

```text
[Demo] case=block_four
[Demo] ai_stone=WHITE
[Demo] selected_move=row=7, col=6
[ArmAdapter] Connected to standalone arm controller (mock mode).
[ARM] place_stone(row=7, col=6, mock=True)
[MOCK TX] {#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[MOCK TX] {#005P0500T0300!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[Demo] arm_execute_ok=True
```

### Win Now

Command:

```powershell
python .\demo_ai_to_arm_mock.py --case win_now
```

Result:

```text
[Demo] case=win_now
[Demo] ai_stone=WHITE
[Demo] selected_move=row=6, col=5
[ArmAdapter] Connected to standalone arm controller (mock mode).
[ARM] place_stone(row=6, col=5, mock=True)
[MOCK TX] {#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[MOCK TX] {#005P0500T0300!}
[MOCK TX] {#000P1500T0800!#001P1500T0800!#002P1500T0800!#003P1500T0800!}
[Demo] arm_execute_ok=True
```

## What This Proves

The current software system already has a reproducible mock integration chain:

```text
seeded board state
  -> HeuristicAI selects row/col
  -> host STM32Controller adapter
  -> standalone arm controller
  -> mock STM32/PWM command output
```

Current limitation:

- The arm controller still uses placeholder `xyz_to_pwm()` values, so this proves software integration but not physical placement accuracy.
