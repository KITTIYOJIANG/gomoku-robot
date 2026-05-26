from __future__ import annotations

import numpy as np
import cv2


EMPTY = 0
BLACK = 1
WHITE = 2


def _clip_roi(gray: np.ndarray, x: int, y: int, radius: int) -> np.ndarray:
    h, w = gray.shape[:2]
    x0 = max(0, x - radius)
    x1 = min(w, x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(h, y + radius + 1)
    return gray[y0:y1, x0:x1]


def classify_grid_point(
    gray: np.ndarray,
    x: float,
    y: float,
    roi_radius: int = 14,
    bg_radius: int = 28,
    black_diff: float = 35.0,
    white_diff: float = 35.0,
    black_area_ratio: float = 0.35,
    white_area_ratio: float = 0.35,
) -> int:
    xi, yi = int(round(x)), int(round(y))
    center_roi = _clip_roi(gray, xi, yi, roi_radius)
    bg_roi = _clip_roi(gray, xi, yi, bg_radius)

    if center_roi.size == 0 or bg_roi.size == 0:
        return EMPTY

    center_mean = float(np.mean(center_roi))
    bg_mean = float(np.mean(bg_roi))

    dark_ratio = float(np.mean(center_roi < bg_mean - black_diff))
    bright_ratio = float(np.mean(center_roi > bg_mean + white_diff))

    if center_mean < bg_mean - black_diff and dark_ratio >= black_area_ratio:
        return BLACK
    if center_mean > bg_mean + white_diff and bright_ratio >= white_area_ratio:
        return WHITE
    return EMPTY


def detect_stones(
    image: np.ndarray,
    grid_points: np.ndarray,
    roi_radius: int = 14,
    bg_radius: int = 28,
    black_diff: float = 35.0,
    white_diff: float = 35.0,
    black_area_ratio: float = 0.35,
    white_area_ratio: float = 0.35,
) -> list[list[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    board_size = grid_points.shape[0]
    matrix = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]

    for row in range(board_size):
        for col in range(board_size):
            x, y = grid_points[row, col]
            matrix[row][col] = classify_grid_point(
                gray,
                x,
                y,
                roi_radius=roi_radius,
                bg_radius=bg_radius,
                black_diff=black_diff,
                white_diff=white_diff,
                black_area_ratio=black_area_ratio,
                white_area_ratio=white_area_ratio,
            )

    return matrix


def draw_stone_detection(image: np.ndarray, grid_points: np.ndarray, board_matrix: list[list[int]]) -> np.ndarray:
    output = image.copy()
    for row in range(grid_points.shape[0]):
        for col in range(grid_points.shape[1]):
            x, y = grid_points[row, col]
            center = (int(round(x)), int(round(y)))
            value = board_matrix[row][col]
            if value == BLACK:
                color = (0, 0, 0)
                radius = 8
            elif value == WHITE:
                color = (255, 255, 255)
                radius = 8
            else:
                color = (0, 0, 255)
                radius = 2
            cv2.circle(output, center, radius, color, 2)
    return output


def format_board_matrix(board_matrix: list[list[int]]) -> str:
    return "\n".join(" ".join(str(cell) for cell in row) for row in board_matrix)
