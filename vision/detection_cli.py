from __future__ import annotations

import argparse
from typing import Any


DETECTION_ARGUMENTS: tuple[tuple[str, dict[str, Any]], ...] = (
    ("--roi-radius", {"type": int, "default": 14}),
    ("--bg-radius", {"type": int, "default": 28}),
    ("--black-diff", {"type": float, "default": 35.0}),
    ("--white-diff", {"type": float, "default": 35.0}),
    ("--black-area-ratio", {"type": float, "default": 0.35}),
    ("--white-area-ratio", {"type": float, "default": 0.35}),
    ("--black-rescue-diff", {"type": float, "default": 20.0}),
    ("--black-rescue-area-ratio", {"type": float, "default": 0.44}),
    ("--low-light-black-min-diff", {"type": float, "default": 0.0}),
    ("--low-light-black-max-diff", {"type": float, "default": 14.0}),
    ("--low-light-black-min-bg", {"type": float, "default": 105.0}),
    ("--low-light-black-max-bg", {"type": float, "default": 120.0}),
    ("--low-light-black-min-center", {"type": float, "default": 115.0}),
    ("--low-light-black-max-center", {"type": float, "default": 130.0}),
    ("--low-light-black-min-bright-ratio", {"type": float, "default": 0.55}),
    ("--low-light-black-max-p10", {"type": float, "default": 30.0}),
    ("--low-light-black-min-median", {"type": float, "default": 140.0}),
    ("--low-light-black-max-median", {"type": float, "default": 170.0}),
    ("--low-light-black-min-std", {"type": float, "default": 55.0}),
    ("--low-light-black-max-std", {"type": float, "default": 70.0}),
    ("--low-light-black-min-green-red-delta", {"type": float, "default": 5.0}),
    ("--white-disk-radius", {"type": int, "default": 12}),
    ("--soft-white-min-diff", {"type": float, "default": 8.0}),
    ("--soft-white-max-diff", {"type": float, "default": 27.0}),
    ("--soft-white-bright-diff", {"type": float, "default": 20.0}),
    ("--soft-white-area-ratio", {"type": float, "default": 0.32}),
    ("--soft-white-min-bg", {"type": float, "default": 155.0}),
    ("--soft-white-min-center", {"type": float, "default": 170.0}),
    ("--soft-white-min-p10", {"type": float, "default": 80.0}),
    ("--soft-white-min-median", {"type": float, "default": 190.0}),
    ("--low-light-white-min-diff", {"type": float, "default": 15.0}),
    ("--low-light-white-max-diff", {"type": float, "default": 19.0}),
    ("--low-light-white-min-bg", {"type": float, "default": 145.0}),
    ("--low-light-white-min-center", {"type": float, "default": 165.0}),
    ("--low-light-white-min-p10", {"type": float, "default": 120.0}),
    ("--low-light-white-min-median", {"type": float, "default": 170.0}),
    ("--low-light-white-max-std", {"type": float, "default": 35.0}),
    ("--shadow-white-min-diff", {"type": float, "default": -8.0}),
    ("--shadow-white-max-diff", {"type": float, "default": 0.0}),
    ("--shadow-white-min-bg", {"type": float, "default": 110.0}),
    ("--shadow-white-min-center", {"type": float, "default": 105.0}),
    ("--shadow-white-min-bright-ratio", {"type": float, "default": 0.40}),
    ("--shadow-white-max-p10", {"type": float, "default": 30.0}),
    ("--shadow-white-min-median", {"type": float, "default": 130.0}),
    ("--shadow-white-min-std", {"type": float, "default": 60.0}),
    ("--subtle-white-min-diff", {"type": float, "default": 5.0}),
    ("--subtle-white-max-diff", {"type": float, "default": 8.0}),
    ("--subtle-white-min-bg", {"type": float, "default": 180.0}),
    ("--subtle-white-min-center", {"type": float, "default": 185.0}),
    ("--subtle-white-min-bright-ratio", {"type": float, "default": 0.10}),
    ("--subtle-white-min-p10", {"type": float, "default": 160.0}),
    ("--subtle-white-min-median", {"type": float, "default": 195.0}),
    ("--subtle-white-max-std", {"type": float, "default": 35.0}),
    ("--color-white-min-green-red-delta", {"type": float, "default": 25.0}),
    ("--edge-white-min-diff", {"type": float, "default": 2.0}),
    ("--edge-white-max-diff", {"type": float, "default": 6.0}),
    ("--edge-white-min-bg", {"type": float, "default": 140.0}),
    ("--edge-white-min-center", {"type": float, "default": 145.0}),
    ("--edge-white-max-bright-ratio", {"type": float, "default": 0.05}),
    ("--edge-white-min-p10", {"type": float, "default": 130.0}),
    ("--edge-white-min-median", {"type": float, "default": 150.0}),
    ("--edge-white-max-std", {"type": float, "default": 12.0}),
)


DETECTION_KWARG_NAMES = tuple(
    flag.removeprefix("--").replace("-", "_") for flag, _ in DETECTION_ARGUMENTS
)


def add_detection_arguments(parser: argparse.ArgumentParser) -> None:
    for flag, kwargs in DETECTION_ARGUMENTS:
        parser.add_argument(flag, **kwargs)


def detection_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {name: getattr(args, name) for name in DETECTION_KWARG_NAMES}
