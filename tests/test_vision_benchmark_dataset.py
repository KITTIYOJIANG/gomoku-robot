from pathlib import Path

from tools.benchmark_vision import collect_predictions, parse_labels
from vision.board_detector import load_image
from vision.grid_mapper import generate_grid_points, parse_corners
from vision.stone_detector import detect_stones


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_CORNERS = "72,18;513,28;508,461;74,468"


def test_benchmark_dataset_detects_labeled_stones_without_false_positives():
    image_dir = PROJECT_ROOT / "calibration_tools"
    labels = parse_labels(image_dir / "label.txt")
    grid_points = generate_grid_points(parse_corners(BENCHMARK_CORNERS))

    black_gt = white_gt = 0
    black_hits = white_hits = 0
    false_black = false_white = 0

    for entry in labels:
        image = load_image(image_dir / entry.image_name)
        pred_black, pred_white = collect_predictions(detect_stones(image, grid_points))

        black_gt += len(entry.black)
        white_gt += len(entry.white)
        black_hits += len(pred_black & entry.black)
        white_hits += len(pred_white & entry.white)
        false_black += len(pred_black - entry.black)
        false_white += len(pred_white - entry.white)

    assert black_hits == black_gt == 22
    assert white_hits == white_gt == 15
    assert false_black == 0
    assert false_white == 0
