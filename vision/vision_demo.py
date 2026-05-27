from __future__ import annotations

import argparse

import cv2

from .board_detector import detect_board_corners, draw_board_detection, load_image
from .detection_cli import add_detection_arguments, detection_kwargs
from .grid_mapper import generate_grid_points, parse_corners
from .stone_detector import detect_stones, draw_stone_detection, format_board_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the first static-image Gomoku vision pipeline.")
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--corners", help="Manual corners: 'x1,y1;x2,y2;x3,y3;x4,y4'.")
    parser.add_argument("--board-size", type=int, default=15)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--output", help="Optional visualization output path.")
    add_detection_arguments(parser)
    args = parser.parse_args()

    image = load_image(args.image)

    if args.corners:
        corners = parse_corners(args.corners)
    else:
        corners = detect_board_corners(image)
        if corners is None:
            raise RuntimeError("Board detection failed. Re-run with --corners.")

    grid_points = generate_grid_points(corners, board_size=args.board_size)
    board_matrix = detect_stones(
        image,
        grid_points,
        **detection_kwargs(args),
    )

    print(format_board_matrix(board_matrix))

    output = draw_board_detection(image, corners)
    output = draw_stone_detection(output, grid_points, board_matrix)
    if args.output:
        cv2.imwrite(args.output, output)
    if args.show:
        cv2.imshow("vision demo", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
