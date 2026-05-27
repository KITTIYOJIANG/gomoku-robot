"""Benchmark the static-image Gomoku vision pipeline.

Run from `D:/Projects/gomoku_project`:

    python tools/benchmark_vision.py \
      --image-dir calibration_tools \
      --labels calibration_tools/label.txt \
      --corners "72,18;513,28;508,461;74,468"

The labels file format is:

    board_001_empty.jpg
    black:
    white:

    board_002_black_center.jpg
    black: 7,7
    white:

Coordinates are zero-based `(row,col)`.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.board_detector import load_image
from vision.grid_mapper import generate_grid_points, parse_corners
from vision.stone_detector import detect_stones


@dataclass(frozen=True)
class LabelEntry:
    image_name: str
    black: set[tuple[int, int]]
    white: set[tuple[int, int]]


@dataclass
class VisionStats:
    black_gt: int = 0
    white_gt: int = 0
    black_hits: int = 0
    white_hits: int = 0
    false_black: int = 0
    false_white: int = 0

    def print_summary(self) -> None:
        print("\nSUMMARY")
        print(f"black recall: {self.black_hits}/{self.black_gt} = {_ratio(self.black_hits, self.black_gt):.2%}")
        print(f"white recall: {self.white_hits}/{self.white_gt} = {_ratio(self.white_hits, self.white_gt):.2%}")
        print(f"false black: {self.false_black}")
        print(f"false white: {self.false_white}")


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def parse_coord_list(text: str) -> set[tuple[int, int]]:
    text = text.strip()
    if not text:
        return set()

    coords = set()
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        row_text, col_text = part.split(",", 1)
        coords.add((int(row_text.strip()), int(col_text.strip())))
    return coords


def parse_labels(path: Path) -> list[LabelEntry]:
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    lines = [line.strip() for line in raw_lines if line.strip()]

    if len(lines) % 3 != 0:
        raise ValueError("Labels file must contain groups of image/black/white lines.")

    entries: list[LabelEntry] = []
    for index in range(0, len(lines), 3):
        image_name = lines[index]
        black_key, black_text = lines[index + 1].split(":", 1)
        white_key, white_text = lines[index + 2].split(":", 1)
        if black_key.strip().lower() != "black" or white_key.strip().lower() != "white":
            raise ValueError(f"Invalid label block near line {index + 1}.")
        entries.append(
            LabelEntry(
                image_name=image_name,
                black=parse_coord_list(black_text),
                white=parse_coord_list(white_text),
            )
        )
    return entries


def collect_predictions(matrix: list[list[int]]) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    black = set()
    white = set()
    for row, values in enumerate(matrix):
        for col, value in enumerate(values):
            if value == 1:
                black.add((row, col))
            elif value == 2:
                white.add((row, col))
    return black, white


def run_benchmark(args: argparse.Namespace) -> int:
    image_dir = Path(args.image_dir)
    labels = parse_labels(Path(args.labels))
    corners = parse_corners(args.corners)
    grid_points = generate_grid_points(corners, board_size=args.board_size)
    stats = VisionStats()

    for entry in labels:
        image_path = image_dir / entry.image_name
        image = load_image(image_path)
        matrix = detect_stones(
            image,
            grid_points,
            roi_radius=args.roi_radius,
            bg_radius=args.bg_radius,
            black_diff=args.black_diff,
            white_diff=args.white_diff,
            black_area_ratio=args.black_area_ratio,
            white_area_ratio=args.white_area_ratio,
            black_rescue_diff=args.black_rescue_diff,
            black_rescue_area_ratio=args.black_rescue_area_ratio,
            low_light_black_min_diff=args.low_light_black_min_diff,
            low_light_black_max_diff=args.low_light_black_max_diff,
            low_light_black_min_bg=args.low_light_black_min_bg,
            low_light_black_max_bg=args.low_light_black_max_bg,
            low_light_black_min_center=args.low_light_black_min_center,
            low_light_black_max_center=args.low_light_black_max_center,
            low_light_black_min_bright_ratio=args.low_light_black_min_bright_ratio,
            low_light_black_max_p10=args.low_light_black_max_p10,
            low_light_black_min_median=args.low_light_black_min_median,
            low_light_black_max_median=args.low_light_black_max_median,
            low_light_black_min_std=args.low_light_black_min_std,
            low_light_black_max_std=args.low_light_black_max_std,
            low_light_black_min_green_red_delta=args.low_light_black_min_green_red_delta,
            white_disk_radius=args.white_disk_radius,
            soft_white_min_diff=args.soft_white_min_diff,
            soft_white_max_diff=args.soft_white_max_diff,
            soft_white_bright_diff=args.soft_white_bright_diff,
            soft_white_area_ratio=args.soft_white_area_ratio,
            soft_white_min_bg=args.soft_white_min_bg,
            soft_white_min_center=args.soft_white_min_center,
            soft_white_min_p10=args.soft_white_min_p10,
            soft_white_min_median=args.soft_white_min_median,
            low_light_white_min_diff=args.low_light_white_min_diff,
            low_light_white_max_diff=args.low_light_white_max_diff,
            low_light_white_min_bg=args.low_light_white_min_bg,
            low_light_white_min_center=args.low_light_white_min_center,
            low_light_white_min_p10=args.low_light_white_min_p10,
            low_light_white_min_median=args.low_light_white_min_median,
            low_light_white_max_std=args.low_light_white_max_std,
            shadow_white_min_diff=args.shadow_white_min_diff,
            shadow_white_max_diff=args.shadow_white_max_diff,
            shadow_white_min_bg=args.shadow_white_min_bg,
            shadow_white_min_center=args.shadow_white_min_center,
            shadow_white_min_bright_ratio=args.shadow_white_min_bright_ratio,
            shadow_white_max_p10=args.shadow_white_max_p10,
            shadow_white_min_median=args.shadow_white_min_median,
            shadow_white_min_std=args.shadow_white_min_std,
            subtle_white_min_diff=args.subtle_white_min_diff,
            subtle_white_max_diff=args.subtle_white_max_diff,
            subtle_white_min_bg=args.subtle_white_min_bg,
            subtle_white_min_center=args.subtle_white_min_center,
            subtle_white_min_bright_ratio=args.subtle_white_min_bright_ratio,
            subtle_white_min_p10=args.subtle_white_min_p10,
            subtle_white_min_median=args.subtle_white_min_median,
            subtle_white_max_std=args.subtle_white_max_std,
            color_white_min_green_red_delta=args.color_white_min_green_red_delta,
            edge_white_min_diff=args.edge_white_min_diff,
            edge_white_max_diff=args.edge_white_max_diff,
            edge_white_min_bg=args.edge_white_min_bg,
            edge_white_min_center=args.edge_white_min_center,
            edge_white_max_bright_ratio=args.edge_white_max_bright_ratio,
            edge_white_min_p10=args.edge_white_min_p10,
            edge_white_min_median=args.edge_white_min_median,
            edge_white_max_std=args.edge_white_max_std,
        )
        pred_black, pred_white = collect_predictions(matrix)

        black_hits = pred_black & entry.black
        white_hits = pred_white & entry.white
        false_black = pred_black - entry.black
        false_white = pred_white - entry.white
        miss_black = entry.black - pred_black
        miss_white = entry.white - pred_white

        stats.black_gt += len(entry.black)
        stats.white_gt += len(entry.white)
        stats.black_hits += len(black_hits)
        stats.white_hits += len(white_hits)
        stats.false_black += len(false_black)
        stats.false_white += len(false_white)

        print(entry.image_name)
        print(f"  pred_black: {sorted(pred_black)}")
        print(f"  pred_white: {sorted(pred_white)}")
        if miss_black or miss_white:
            print(f"  missed_black: {sorted(miss_black)}")
            print(f"  missed_white: {sorted(miss_white)}")
        if false_black or false_white:
            print(f"  false_black: {sorted(false_black)}")
            print(f"  false_white: {sorted(false_white)}")

    stats.print_summary()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark static Gomoku board vision.")
    parser.add_argument("--image-dir", default="calibration_tools")
    parser.add_argument("--labels", default="calibration_tools/label.txt")
    parser.add_argument("--corners", required=True)
    parser.add_argument("--board-size", type=int, default=15)
    parser.add_argument("--roi-radius", type=int, default=14)
    parser.add_argument("--bg-radius", type=int, default=28)
    parser.add_argument("--black-diff", type=float, default=35.0)
    parser.add_argument("--white-diff", type=float, default=35.0)
    parser.add_argument("--black-area-ratio", type=float, default=0.35)
    parser.add_argument("--white-area-ratio", type=float, default=0.35)
    parser.add_argument("--black-rescue-diff", type=float, default=20.0)
    parser.add_argument("--black-rescue-area-ratio", type=float, default=0.44)
    parser.add_argument("--low-light-black-min-diff", type=float, default=0.0)
    parser.add_argument("--low-light-black-max-diff", type=float, default=14.0)
    parser.add_argument("--low-light-black-min-bg", type=float, default=105.0)
    parser.add_argument("--low-light-black-max-bg", type=float, default=120.0)
    parser.add_argument("--low-light-black-min-center", type=float, default=115.0)
    parser.add_argument("--low-light-black-max-center", type=float, default=130.0)
    parser.add_argument("--low-light-black-min-bright-ratio", type=float, default=0.55)
    parser.add_argument("--low-light-black-max-p10", type=float, default=30.0)
    parser.add_argument("--low-light-black-min-median", type=float, default=140.0)
    parser.add_argument("--low-light-black-max-median", type=float, default=170.0)
    parser.add_argument("--low-light-black-min-std", type=float, default=55.0)
    parser.add_argument("--low-light-black-max-std", type=float, default=70.0)
    parser.add_argument("--low-light-black-min-green-red-delta", type=float, default=5.0)
    parser.add_argument("--white-disk-radius", type=int, default=12)
    parser.add_argument("--soft-white-min-diff", type=float, default=8.0)
    parser.add_argument("--soft-white-max-diff", type=float, default=27.0)
    parser.add_argument("--soft-white-bright-diff", type=float, default=20.0)
    parser.add_argument("--soft-white-area-ratio", type=float, default=0.32)
    parser.add_argument("--soft-white-min-bg", type=float, default=155.0)
    parser.add_argument("--soft-white-min-center", type=float, default=170.0)
    parser.add_argument("--soft-white-min-p10", type=float, default=80.0)
    parser.add_argument("--soft-white-min-median", type=float, default=190.0)
    parser.add_argument("--low-light-white-min-diff", type=float, default=15.0)
    parser.add_argument("--low-light-white-max-diff", type=float, default=19.0)
    parser.add_argument("--low-light-white-min-bg", type=float, default=145.0)
    parser.add_argument("--low-light-white-min-center", type=float, default=165.0)
    parser.add_argument("--low-light-white-min-p10", type=float, default=120.0)
    parser.add_argument("--low-light-white-min-median", type=float, default=170.0)
    parser.add_argument("--low-light-white-max-std", type=float, default=35.0)
    parser.add_argument("--shadow-white-min-diff", type=float, default=-8.0)
    parser.add_argument("--shadow-white-max-diff", type=float, default=0.0)
    parser.add_argument("--shadow-white-min-bg", type=float, default=110.0)
    parser.add_argument("--shadow-white-min-center", type=float, default=105.0)
    parser.add_argument("--shadow-white-min-bright-ratio", type=float, default=0.40)
    parser.add_argument("--shadow-white-max-p10", type=float, default=30.0)
    parser.add_argument("--shadow-white-min-median", type=float, default=130.0)
    parser.add_argument("--shadow-white-min-std", type=float, default=60.0)
    parser.add_argument("--subtle-white-min-diff", type=float, default=5.0)
    parser.add_argument("--subtle-white-max-diff", type=float, default=8.0)
    parser.add_argument("--subtle-white-min-bg", type=float, default=180.0)
    parser.add_argument("--subtle-white-min-center", type=float, default=185.0)
    parser.add_argument("--subtle-white-min-bright-ratio", type=float, default=0.10)
    parser.add_argument("--subtle-white-min-p10", type=float, default=160.0)
    parser.add_argument("--subtle-white-min-median", type=float, default=195.0)
    parser.add_argument("--subtle-white-max-std", type=float, default=35.0)
    parser.add_argument("--color-white-min-green-red-delta", type=float, default=25.0)
    parser.add_argument("--edge-white-min-diff", type=float, default=2.0)
    parser.add_argument("--edge-white-max-diff", type=float, default=6.0)
    parser.add_argument("--edge-white-min-bg", type=float, default=140.0)
    parser.add_argument("--edge-white-min-center", type=float, default=145.0)
    parser.add_argument("--edge-white-max-bright-ratio", type=float, default=0.05)
    parser.add_argument("--edge-white-min-p10", type=float, default=130.0)
    parser.add_argument("--edge-white-min-median", type=float, default=150.0)
    parser.add_argument("--edge-white-max-std", type=float, default=12.0)
    return parser


def main() -> None:
    raise SystemExit(run_benchmark(build_parser().parse_args()))


if __name__ == "__main__":
    main()
