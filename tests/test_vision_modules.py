import numpy as np

from vision.grid_mapper import generate_grid_points, parse_corners
from vision.stone_detector import BLACK, EMPTY, classify_grid_point


def test_parse_corners_and_generate_grid():
    corners = parse_corners("0,0;140,0;140,140;0,140")
    grid = generate_grid_points(corners, board_size=15)
    assert grid.shape == (15, 15, 2)
    assert tuple(grid[0, 0]) == (0.0, 0.0)
    assert tuple(grid[14, 14]) == (140.0, 140.0)
    assert tuple(grid[7, 7]) == (70.0, 70.0)


def test_small_dark_star_point_is_not_black_stone():
    gray = np.full((80, 80), 160, dtype=np.uint8)
    gray[38:42, 38:42] = 20
    assert classify_grid_point(gray, 40, 40) == EMPTY


def test_large_dark_region_is_black_stone():
    gray = np.full((80, 80), 160, dtype=np.uint8)
    yy, xx = np.ogrid[:80, :80]
    mask = (xx - 40) ** 2 + (yy - 40) ** 2 <= 13 ** 2
    gray[mask] = 20
    assert classify_grid_point(gray, 40, 40) == BLACK
