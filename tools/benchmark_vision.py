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
from vision.detection_cli import add_detection_arguments, detection_kwargs
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
        matrix = detect_stones(image, grid_points, **detection_kwargs(args))
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
    add_detection_arguments(parser)
    return parser


def main() -> None:
    raise SystemExit(run_benchmark(build_parser().parse_args()))


if __name__ == "__main__":
    main()
