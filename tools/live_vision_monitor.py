"""Run Gomoku vision on a live camera feed or a single image.

Examples:

    python tools/live_vision_monitor.py \
      --camera-id 0 \
      --corners "72,18;513,28;508,461;74,468"

    python tools/live_vision_monitor.py \
      --image calibration_tools/board_010_random_game.jpg \
      --corners "72,18;513,28;508,461;74,468" \
      --output outputs/board_010_detected.jpg \
      --no-window

    python tools/live_vision_monitor.py \
      --camera-id 0 \
      --corners "72,18;513,28;508,461;74,468" \
      --capture-dir calibration_tools/live_benchmark_20260527
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.board_detector import draw_board_detection, load_image
from vision.detection_cli import add_detection_arguments, detection_kwargs
from vision.grid_mapper import generate_grid_points, parse_corners
from vision.stone_detector import detect_stones, draw_stone_detection, format_board_matrix


def save_image(path_text: str, image) -> None:
    path = Path(path_text)
    save_image_path(path, image)


def save_image_path(path: Path, image) -> None:
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"Failed to write image: {path}")


def label_file_contains(label_path: Path, image_name: str) -> bool:
    if not label_path.exists():
        return False
    lines = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines()]
    return image_name in lines


def append_label_stub(label_path: Path, image_name: str) -> None:
    if label_file_contains(label_path, image_name):
        return

    label_path.parent.mkdir(parents=True, exist_ok=True)
    needs_leading_blank = label_path.exists() and label_path.stat().st_size > 0
    with label_path.open("a", encoding="utf-8") as handle:
        if needs_leading_blank:
            handle.write("\n")
        handle.write(f"{image_name}\n")
        handle.write("black:\n")
        handle.write("white:\n")


def next_capture_index(capture_dir: Path, prefix: str, start_index: int) -> int:
    index = start_index
    while (capture_dir / f"{prefix}_{index:03d}.jpg").exists():
        index += 1
    return index


def capture_dataset_sample(
    capture_dir: Path,
    prefix: str,
    index: int,
    frame,
    annotated,
    write_label_template: bool,
) -> tuple[Path, Path]:
    raw_path = capture_dir / f"{prefix}_{index:03d}.jpg"
    annotated_path = capture_dir / "annotated" / f"{prefix}_{index:03d}_detected.jpg"
    save_image_path(raw_path, frame)
    save_image_path(annotated_path, annotated)

    if write_label_template:
        append_label_stub(capture_dir / "label.txt", raw_path.name)

    return raw_path, annotated_path


def analyze_frame(frame, corners, grid_points, args: argparse.Namespace):
    board_matrix = detect_stones(frame, grid_points, **detection_kwargs(args))
    output = draw_board_detection(frame, corners)
    output = draw_stone_detection(output, grid_points, board_matrix)
    return board_matrix, output


def run_static_image(args: argparse.Namespace) -> int:
    image = load_image(args.image)
    corners = parse_corners(args.corners)
    grid_points = generate_grid_points(corners, board_size=args.board_size)
    board_matrix, output = analyze_frame(image, corners, grid_points, args)

    print(format_board_matrix(board_matrix))
    if args.output:
        save_image(args.output, output)
        print(f"Saved annotated image: {args.output}")
    if not args.no_window:
        cv2.imshow(args.window_name, output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return 0


def run_camera(args: argparse.Namespace) -> int:
    corners = parse_corners(args.corners)
    grid_points = generate_grid_points(corners, board_size=args.board_size)
    capture_dir = Path(args.capture_dir) if args.capture_dir else None
    capture_index = (
        next_capture_index(capture_dir, args.capture_prefix, args.capture_start_index)
        if capture_dir
        else args.capture_start_index
    )

    cap = cv2.VideoCapture(args.camera_id)
    if args.width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera: {args.camera_id}")

    if not args.no_window:
        print("Controls: press 's' to save a dataset sample, 'q' to quit.")

    frame_index = 0
    last_output = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Failed to read camera frame.")

            board_matrix, output = analyze_frame(frame, corners, grid_points, args)
            last_output = output

            if frame_index % args.matrix_every == 0:
                print(f"\nFRAME {frame_index}")
                print(format_board_matrix(board_matrix))

            if args.output and (args.once or frame_index % args.save_every == 0):
                save_image(args.output, output)
            if args.raw_output and (args.once or frame_index % args.save_every == 0):
                save_image(args.raw_output, frame)
            if args.once and capture_dir:
                raw_path, annotated_path = capture_dataset_sample(
                    capture_dir,
                    args.capture_prefix,
                    capture_index,
                    frame,
                    output,
                    not args.no_label_template,
                )
                print(f"Saved capture: {raw_path}")
                print(f"Saved annotated capture: {annotated_path}")

            if args.once:
                break

            if not args.no_window:
                cv2.imshow(args.window_name, output)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("s") and capture_dir:
                    raw_path, annotated_path = capture_dataset_sample(
                        capture_dir,
                        args.capture_prefix,
                        capture_index,
                        frame,
                        output,
                        not args.no_label_template,
                    )
                    print(f"Saved capture: {raw_path}")
                    print(f"Saved annotated capture: {annotated_path}")
                    capture_index += 1

            frame_index += 1
    finally:
        cap.release()
        if not args.no_window:
            cv2.destroyAllWindows()

    if args.output and last_output is not None and not args.once:
        save_image(args.output, last_output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Gomoku vision on camera frames or a static image.")
    parser.add_argument("--image", help="Optional static image path. If omitted, camera mode is used.")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--corners", required=True, help="Manual corners: 'x1,y1;x2,y2;x3,y3;x4,y4'.")
    parser.add_argument("--board-size", type=int, default=15)
    parser.add_argument("--width", type=int, help="Optional camera capture width.")
    parser.add_argument("--height", type=int, help="Optional camera capture height.")
    parser.add_argument("--output", help="Optional annotated output image path.")
    parser.add_argument("--raw-output", help="Optional raw camera frame output path.")
    parser.add_argument("--capture-dir", help="Directory for interactive benchmark captures.")
    parser.add_argument("--capture-prefix", default="live_board", help="Filename prefix for capture-dir samples.")
    parser.add_argument("--capture-start-index", type=int, default=1, help="First numeric suffix for capture-dir samples.")
    parser.add_argument("--no-label-template", action="store_true", help="Do not append blank entries to capture-dir/label.txt.")
    parser.add_argument("--matrix-every", type=int, default=30, help="Print matrix every N frames in camera mode.")
    parser.add_argument("--save-every", type=int, default=30, help="Save output every N frames in camera mode.")
    parser.add_argument("--once", action="store_true", help="Process one camera frame and exit.")
    parser.add_argument("--no-window", action="store_true", help="Do not open an OpenCV preview window.")
    parser.add_argument("--window-name", default="Gomoku Vision Monitor")
    add_detection_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.image:
        raise SystemExit(run_static_image(args))
    raise SystemExit(run_camera(args))


if __name__ == "__main__":
    main()
