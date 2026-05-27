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


def _disk_roi(gray: np.ndarray, x: int, y: int, radius: int) -> np.ndarray:
    h, w = gray.shape[:2]
    x0 = max(0, x - radius)
    x1 = min(w, x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(h, y + radius + 1)
    patch = gray[y0:y1, x0:x1]
    yy, xx = np.ogrid[y0 - y : y1 - y, x0 - x : x1 - x]
    mask = xx * xx + yy * yy <= radius * radius
    return patch[mask]


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
    black_rescue_diff: float = 20.0,
    black_rescue_area_ratio: float = 0.44,
    low_light_black_min_diff: float = 0.0,
    low_light_black_max_diff: float = 14.0,
    low_light_black_min_bg: float = 105.0,
    low_light_black_max_bg: float = 120.0,
    low_light_black_min_center: float = 115.0,
    low_light_black_max_center: float = 130.0,
    low_light_black_min_bright_ratio: float = 0.55,
    low_light_black_max_p10: float = 30.0,
    low_light_black_min_median: float = 140.0,
    low_light_black_max_median: float = 170.0,
    low_light_black_min_std: float = 55.0,
    low_light_black_max_std: float = 70.0,
    low_light_black_min_green_red_delta: float = 5.0,
    white_disk_radius: int = 12,
    soft_white_min_diff: float = 8.0,
    soft_white_max_diff: float = 27.0,
    soft_white_bright_diff: float = 20.0,
    soft_white_area_ratio: float = 0.32,
    soft_white_min_bg: float = 155.0,
    soft_white_min_center: float = 170.0,
    soft_white_min_p10: float = 80.0,
    soft_white_min_median: float = 190.0,
    low_light_white_min_diff: float = 15.0,
    low_light_white_max_diff: float = 19.0,
    low_light_white_min_bg: float = 145.0,
    low_light_white_min_center: float = 165.0,
    low_light_white_min_p10: float = 120.0,
    low_light_white_min_median: float = 170.0,
    low_light_white_max_std: float = 35.0,
    shadow_white_min_diff: float = -8.0,
    shadow_white_max_diff: float = 0.0,
    shadow_white_min_bg: float = 110.0,
    shadow_white_min_center: float = 105.0,
    shadow_white_min_bright_ratio: float = 0.40,
    shadow_white_max_p10: float = 30.0,
    shadow_white_min_median: float = 130.0,
    shadow_white_min_std: float = 60.0,
    subtle_white_min_diff: float = 5.0,
    subtle_white_max_diff: float = 8.0,
    subtle_white_min_bg: float = 180.0,
    subtle_white_min_center: float = 185.0,
    subtle_white_min_bright_ratio: float = 0.10,
    subtle_white_min_p10: float = 160.0,
    subtle_white_min_median: float = 195.0,
    subtle_white_max_std: float = 35.0,
    color_white_min_green_red_delta: float = 25.0,
    edge_white_min_diff: float = 2.0,
    edge_white_max_diff: float = 6.0,
    edge_white_min_bg: float = 140.0,
    edge_white_min_center: float = 145.0,
    edge_white_max_bright_ratio: float = 0.05,
    edge_white_min_p10: float = 130.0,
    edge_white_min_median: float = 150.0,
    edge_white_max_std: float = 12.0,
    color_image: np.ndarray | None = None,
) -> int:
    xi, yi = int(round(x)), int(round(y))
    center_roi = _clip_roi(gray, xi, yi, roi_radius)
    bg_roi = _clip_roi(gray, xi, yi, bg_radius)
    white_disk = _disk_roi(gray, xi, yi, white_disk_radius)

    if center_roi.size == 0 or bg_roi.size == 0 or white_disk.size == 0:
        return EMPTY

    center_mean = float(np.mean(center_roi))
    bg_mean = float(np.mean(bg_roi))
    center_diff = center_mean - bg_mean

    dark_ratio = float(np.mean(center_roi < bg_mean - black_diff))
    bright_ratio = float(np.mean(center_roi > bg_mean + white_diff))
    white_disk_p10 = float(np.percentile(white_disk, 10))
    white_disk_median = float(np.median(white_disk))
    white_disk_std = float(np.std(white_disk))
    green_red_delta = None
    if color_image is not None and color_image.ndim == 3:
        color_disk = _disk_roi(color_image, xi, yi, white_disk_radius)
        if color_disk.size:
            _, green_mean, red_mean = np.mean(color_disk, axis=0)
            green_red_delta = float(green_mean - red_mean)

    if center_diff < -black_diff and dark_ratio >= black_area_ratio:
        return BLACK

    rescue_dark_ratio = float(np.mean(center_roi < bg_mean - black_rescue_diff))
    if center_diff < -black_rescue_diff and rescue_dark_ratio >= black_rescue_area_ratio:
        return BLACK

    if (
        green_red_delta is not None
        and low_light_black_min_diff <= center_diff <= low_light_black_max_diff
        and low_light_black_min_bg <= bg_mean <= low_light_black_max_bg
        and low_light_black_min_center <= center_mean <= low_light_black_max_center
        and bright_ratio >= low_light_black_min_bright_ratio
        and white_disk_p10 <= low_light_black_max_p10
        and low_light_black_min_median <= white_disk_median <= low_light_black_max_median
        and low_light_black_min_std <= white_disk_std <= low_light_black_max_std
        and green_red_delta >= low_light_black_min_green_red_delta
    ):
        return BLACK

    if center_diff > white_diff and bright_ratio >= white_area_ratio:
        return WHITE

    soft_white_bright_ratio = float(np.mean(center_roi > bg_mean + soft_white_bright_diff))
    if (
        soft_white_min_diff <= center_diff <= soft_white_max_diff
        and bg_mean >= soft_white_min_bg
        and center_mean >= soft_white_min_center
        and soft_white_bright_ratio >= soft_white_area_ratio
        and white_disk_p10 >= soft_white_min_p10
        and white_disk_median >= soft_white_min_median
    ):
        return WHITE

    if (
        low_light_white_min_diff <= center_diff <= low_light_white_max_diff
        and bg_mean >= low_light_white_min_bg
        and center_mean >= low_light_white_min_center
        and white_disk_p10 >= low_light_white_min_p10
        and white_disk_median >= low_light_white_min_median
        and white_disk_std <= low_light_white_max_std
    ):
        return WHITE

    if (
        shadow_white_min_diff <= center_diff <= shadow_white_max_diff
        and bg_mean >= shadow_white_min_bg
        and center_mean >= shadow_white_min_center
        and bright_ratio >= shadow_white_min_bright_ratio
        and white_disk_p10 <= shadow_white_max_p10
        and white_disk_median >= shadow_white_min_median
        and white_disk_std >= shadow_white_min_std
    ):
        return WHITE

    has_white_color = (
        green_red_delta is not None and green_red_delta >= color_white_min_green_red_delta
    )
    if (
        has_white_color
        and subtle_white_min_diff <= center_diff <= subtle_white_max_diff
        and bg_mean >= subtle_white_min_bg
        and center_mean >= subtle_white_min_center
        and soft_white_bright_ratio >= subtle_white_min_bright_ratio
        and white_disk_p10 >= subtle_white_min_p10
        and white_disk_median >= subtle_white_min_median
        and white_disk_std <= subtle_white_max_std
    ):
        return WHITE

    if (
        has_white_color
        and edge_white_min_diff <= center_diff <= edge_white_max_diff
        and bg_mean >= edge_white_min_bg
        and center_mean >= edge_white_min_center
        and soft_white_bright_ratio <= edge_white_max_bright_ratio
        and white_disk_p10 >= edge_white_min_p10
        and white_disk_median >= edge_white_min_median
        and white_disk_std <= edge_white_max_std
    ):
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
    black_rescue_diff: float = 20.0,
    black_rescue_area_ratio: float = 0.44,
    low_light_black_min_diff: float = 0.0,
    low_light_black_max_diff: float = 14.0,
    low_light_black_min_bg: float = 105.0,
    low_light_black_max_bg: float = 120.0,
    low_light_black_min_center: float = 115.0,
    low_light_black_max_center: float = 130.0,
    low_light_black_min_bright_ratio: float = 0.55,
    low_light_black_max_p10: float = 30.0,
    low_light_black_min_median: float = 140.0,
    low_light_black_max_median: float = 170.0,
    low_light_black_min_std: float = 55.0,
    low_light_black_max_std: float = 70.0,
    low_light_black_min_green_red_delta: float = 5.0,
    white_disk_radius: int = 12,
    soft_white_min_diff: float = 8.0,
    soft_white_max_diff: float = 27.0,
    soft_white_bright_diff: float = 20.0,
    soft_white_area_ratio: float = 0.32,
    soft_white_min_bg: float = 155.0,
    soft_white_min_center: float = 170.0,
    soft_white_min_p10: float = 80.0,
    soft_white_min_median: float = 190.0,
    low_light_white_min_diff: float = 15.0,
    low_light_white_max_diff: float = 19.0,
    low_light_white_min_bg: float = 145.0,
    low_light_white_min_center: float = 165.0,
    low_light_white_min_p10: float = 120.0,
    low_light_white_min_median: float = 170.0,
    low_light_white_max_std: float = 35.0,
    shadow_white_min_diff: float = -8.0,
    shadow_white_max_diff: float = 0.0,
    shadow_white_min_bg: float = 110.0,
    shadow_white_min_center: float = 105.0,
    shadow_white_min_bright_ratio: float = 0.40,
    shadow_white_max_p10: float = 30.0,
    shadow_white_min_median: float = 130.0,
    shadow_white_min_std: float = 60.0,
    subtle_white_min_diff: float = 5.0,
    subtle_white_max_diff: float = 8.0,
    subtle_white_min_bg: float = 180.0,
    subtle_white_min_center: float = 185.0,
    subtle_white_min_bright_ratio: float = 0.10,
    subtle_white_min_p10: float = 160.0,
    subtle_white_min_median: float = 195.0,
    subtle_white_max_std: float = 35.0,
    color_white_min_green_red_delta: float = 25.0,
    edge_white_min_diff: float = 2.0,
    edge_white_max_diff: float = 6.0,
    edge_white_min_bg: float = 140.0,
    edge_white_min_center: float = 145.0,
    edge_white_max_bright_ratio: float = 0.05,
    edge_white_min_p10: float = 130.0,
    edge_white_min_median: float = 150.0,
    edge_white_max_std: float = 12.0,
) -> list[list[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    color_image = image if image.ndim == 3 else None
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
                black_rescue_diff=black_rescue_diff,
                black_rescue_area_ratio=black_rescue_area_ratio,
                low_light_black_min_diff=low_light_black_min_diff,
                low_light_black_max_diff=low_light_black_max_diff,
                low_light_black_min_bg=low_light_black_min_bg,
                low_light_black_max_bg=low_light_black_max_bg,
                low_light_black_min_center=low_light_black_min_center,
                low_light_black_max_center=low_light_black_max_center,
                low_light_black_min_bright_ratio=low_light_black_min_bright_ratio,
                low_light_black_max_p10=low_light_black_max_p10,
                low_light_black_min_median=low_light_black_min_median,
                low_light_black_max_median=low_light_black_max_median,
                low_light_black_min_std=low_light_black_min_std,
                low_light_black_max_std=low_light_black_max_std,
                low_light_black_min_green_red_delta=low_light_black_min_green_red_delta,
                white_disk_radius=white_disk_radius,
                soft_white_min_diff=soft_white_min_diff,
                soft_white_max_diff=soft_white_max_diff,
                soft_white_bright_diff=soft_white_bright_diff,
                soft_white_area_ratio=soft_white_area_ratio,
                soft_white_min_bg=soft_white_min_bg,
                soft_white_min_center=soft_white_min_center,
                soft_white_min_p10=soft_white_min_p10,
                soft_white_min_median=soft_white_min_median,
                low_light_white_min_diff=low_light_white_min_diff,
                low_light_white_max_diff=low_light_white_max_diff,
                low_light_white_min_bg=low_light_white_min_bg,
                low_light_white_min_center=low_light_white_min_center,
                low_light_white_min_p10=low_light_white_min_p10,
                low_light_white_min_median=low_light_white_min_median,
                low_light_white_max_std=low_light_white_max_std,
                shadow_white_min_diff=shadow_white_min_diff,
                shadow_white_max_diff=shadow_white_max_diff,
                shadow_white_min_bg=shadow_white_min_bg,
                shadow_white_min_center=shadow_white_min_center,
                shadow_white_min_bright_ratio=shadow_white_min_bright_ratio,
                shadow_white_max_p10=shadow_white_max_p10,
                shadow_white_min_median=shadow_white_min_median,
                shadow_white_min_std=shadow_white_min_std,
                subtle_white_min_diff=subtle_white_min_diff,
                subtle_white_max_diff=subtle_white_max_diff,
                subtle_white_min_bg=subtle_white_min_bg,
                subtle_white_min_center=subtle_white_min_center,
                subtle_white_min_bright_ratio=subtle_white_min_bright_ratio,
                subtle_white_min_p10=subtle_white_min_p10,
                subtle_white_min_median=subtle_white_min_median,
                subtle_white_max_std=subtle_white_max_std,
                color_white_min_green_red_delta=color_white_min_green_red_delta,
                edge_white_min_diff=edge_white_min_diff,
                edge_white_max_diff=edge_white_max_diff,
                edge_white_min_bg=edge_white_min_bg,
                edge_white_min_center=edge_white_min_center,
                edge_white_max_bright_ratio=edge_white_max_bright_ratio,
                edge_white_min_p10=edge_white_min_p10,
                edge_white_min_median=edge_white_min_median,
                edge_white_max_std=edge_white_max_std,
                color_image=color_image,
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
