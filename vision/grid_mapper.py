from __future__ import annotations

import argparse
from typing import Iterable

import numpy as np

from .board_detector import order_points


def parse_corners(text: str) -> np.ndarray:
    """Parse corners like '80,26;513,30;517,456;86,467'."""
    pairs = []
    for part in text.split(";"):
        x_text, y_text = part.split(",")
        pairs.append([float(x_text.strip()), float(y_text.strip())])
    if len(pairs) != 4:
        raise ValueError("Exactly four corners are required.")
    return order_points(np.array(pairs, dtype="float32"))


def interpolate_point(left: np.ndarray, right: np.ndarray, t: float) -> np.ndarray:
    return left * (1.0 - t) + right * t


def generate_grid_points(corners: Iterable[Iterable[float]], board_size: int = 15) -> np.ndarray:
    """Generate a board_size x board_size array of image-space grid points."""
    if board_size < 2:
        raise ValueError("board_size must be at least 2")

    tl, tr, br, bl = order_points(np.asarray(corners, dtype="float32"))
    grid = np.zeros((board_size, board_size, 2), dtype="float32")

    for row in range(board_size):
        row_t = row / (board_size - 1)
        left = interpolate_point(tl, bl, row_t)
        right = interpolate_point(tr, br, row_t)
        for col in range(board_size):
            col_t = col / (board_size - 1)
            grid[row, col] = interpolate_point(left, right, col_t)

    return grid


def board_to_image_point(grid_points: np.ndarray, row: int, col: int) -> tuple[float, float]:
    if not (0 <= row < grid_points.shape[0] and 0 <= col < grid_points.shape[1]):
        raise ValueError(f"Board coordinate out of range: ({row}, {col})")
    x, y = grid_points[row, col]
    return float(x), float(y)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 15x15 grid points from four board corners.")
    parser.add_argument("--corners", required=True, help="Example: '80,26;513,30;517,456;86,467'")
    parser.add_argument("--board-size", type=int, default=15)
    args = parser.parse_args()

    corners = parse_corners(args.corners)
    grid = generate_grid_points(corners, board_size=args.board_size)
    for row in range(args.board_size):
        row_points = []
        for col in range(args.board_size):
            x, y = board_to_image_point(grid, row, col)
            row_points.append(f"({x:.1f},{y:.1f})")
        print(" ".join(row_points))


if __name__ == "__main__":
    main()

