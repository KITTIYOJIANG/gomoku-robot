# Vision Module Plan

This document describes the standalone `vision/` package for the Gomoku robot host project.

## Goal

The vision module converts a board image into a 15x15 board-state matrix:

```text
0 = empty
1 = black stone
2 = white stone
```

## Current Static-Image Pipeline

```text
input image
  -> board corner detection or manual corners
  -> 15x15 grid point generation
  -> local ROI brightness analysis
  -> board matrix output
  -> optional visualization
```

## Modules

- `vision/board_detector.py`
  - load image
  - preprocess edges
  - detect largest quadrilateral board candidate
  - draw detected board corners

- `vision/grid_mapper.py`
  - parse four manual corners
  - generate 15x15 grid points
  - map board coordinates to image coordinates

- `vision/stone_detector.py`
  - classify each grid point as empty, black or white
  - use local contrast and area-ratio filtering
  - avoid treating small board star points as stones

- `vision/vision_demo.py`
  - end-to-end static-image demo
  - prints a 15x15 matrix
  - optionally writes a visualization image

## Example

```bash
python -m vision.vision_demo --image .\calibration_tools\my_real_board.jpg --corners "80,26;513,30;517,456;86,467"
```

Optional visualization:

```bash
python -m vision.vision_demo --image .\calibration_tools\my_real_board.jpg --corners "80,26;513,30;517,456;86,467" --output outputs/vision_demo.jpg
```

## Live Validation Tool

Use `tools/live_vision_monitor.py` after collecting reliable board corners. It shares the same detector thresholds as the benchmark and static demo.

Static dry-run on a saved image:

```bash
python tools/live_vision_monitor.py --image calibration_tools/board_010_random_game.jpg --corners "72,18;513,28;508,461;74,468" --output outputs/board_010_live_monitor.jpg --no-window
```

Live camera check:

```bash
python tools/live_vision_monitor.py --camera-id 0 --corners "72,18;513,28;508,461;74,468"
```

Useful camera options:

```bash
python tools/live_vision_monitor.py --camera-id 0 --width 1280 --height 720 --corners "72,18;513,28;508,461;74,468" --output outputs/live_detected.jpg
```

Press `q` in the OpenCV window to exit.

## Benchmark

The current static benchmark dataset is under `calibration_tools/`.

```bash
python tools/benchmark_vision.py --image-dir calibration_tools --labels calibration_tools/label.txt --corners "72,18;513,28;508,461;74,468"
```

Current dataset result:

```text
black recall: 22/22 = 100.00%
white recall: 15/15 = 100.00%
false black: 0
false white: 0
```

## Known Limitations

- Current detection is still a classical OpenCV baseline, not a deep learning detector.
- Thresholds may need to be tuned for different lighting, camera position and stone material.
- Current benchmark accuracy is measured on a small fixed dataset; new camera angles and lighting should be added before trusting the thresholds broadly.
- Future versions should add more real board images and report accuracy across sessions.
