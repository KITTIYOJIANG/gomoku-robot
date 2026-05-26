from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def load_image(image_path: str | Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    return image


def order_points(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype="float32").reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(sums)]
    rect[2] = pts[np.argmax(sums)]
    rect[1] = pts[np.argmin(diffs)]
    rect[3] = pts[np.argmax(diffs)]
    return rect


def preprocess_edges(image: np.ndarray, blur_kernel: int = 5) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    return cv2.Canny(blurred, 50, 150)


def find_largest_quad(edges: np.ndarray, min_area: float = 10_000) -> Optional[np.ndarray]:
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            return order_points(approx.reshape(4, 2))
    return None


def detect_board_corners(image: np.ndarray, min_area: float = 10_000) -> Optional[np.ndarray]:
    edges = preprocess_edges(image)
    return find_largest_quad(edges, min_area=min_area)


def warp_board(image: np.ndarray, corners: np.ndarray, output_size: int = 600) -> np.ndarray:
    rect = order_points(corners)
    dst = np.array(
        [
            [0, 0],
            [output_size - 1, 0],
            [output_size - 1, output_size - 1],
            [0, output_size - 1],
        ],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (output_size, output_size))


def draw_board_detection(image: np.ndarray, corners: Optional[np.ndarray]) -> np.ndarray:
    output = image.copy()
    if corners is None:
        return output

    pts = order_points(corners).astype(int)
    cv2.polylines(output, [pts.reshape(-1, 1, 2)], isClosed=True, color=(0, 255, 0), thickness=2)
    for idx, (x, y) in enumerate(pts):
        cv2.circle(output, (int(x), int(y)), 6, (0, 0, 255), -1)
        cv2.putText(output, str(idx), (int(x) + 8, int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect the largest quadrilateral board area in an image.")
    parser.add_argument("--image", required=True, help="Input board image path.")
    parser.add_argument("--show", action="store_true", help="Show detection window.")
    parser.add_argument("--output", help="Optional output image path.")
    args = parser.parse_args()

    image = load_image(args.image)
    corners = detect_board_corners(image)
    if corners is None:
        print("No board-like quadrilateral found.")
    else:
        print("Detected corners:")
        for x, y in corners:
            print(f"{x:.1f}, {y:.1f}")

    output = draw_board_detection(image, corners)
    if args.output:
        cv2.imwrite(args.output, output)
    if args.show:
        cv2.imshow("board detection", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

