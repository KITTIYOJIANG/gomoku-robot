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

## Known Limitations

- Current detection is still a classical OpenCV baseline, not a deep learning detector.
- Thresholds may need to be tuned for different lighting, camera position and stone material.
- White stones under strong reflection may require HSV or color-based features.
- Future versions should add benchmark images and report recognition accuracy.
