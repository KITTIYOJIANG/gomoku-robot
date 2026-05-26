"""Minimal host-to-arm mock integration demo.

This script proves the current two-repository boundary:

1. The host project owns board state and AI decision-making.
2. The standalone arm-controller project owns physical execution.
3. The interface between them is only `(row, col)`.

Run from `D:/Projects/gomoku_project`:

    set GOMOKU_ARM_MOCK=1
    python demo_ai_to_arm_mock.py
"""

from __future__ import annotations

import argparse
from typing import Iterable

from gomoku.ai import HeuristicAI
from gomoku.core import GomokuBoard, Stone
from gomoku.stm32_controller import STM32Controller


def _stone_from_text(text: str) -> Stone:
    normalized = text.strip().lower()
    if normalized in {"black", "b", "1", "x"}:
        return Stone.BLACK
    if normalized in {"white", "w", "2", "o"}:
        return Stone.WHITE
    raise ValueError(f"Unknown stone: {text}")


def seed_board(board: GomokuBoard, moves: Iterable[tuple[Stone, int, int]]) -> None:
    """Seed board cells directly for deterministic integration demos."""
    for stone, row, col in moves:
        if not board.is_on_board(row, col):
            raise ValueError(f"Seed coordinate out of range: ({row}, {col})")
        if board.grid[row][col] != Stone.EMPTY:
            raise ValueError(f"Seed coordinate already occupied: ({row}, {col})")
        board.grid[row][col] = stone
        board.last_move = (row, col)
        board.move_count += 1


def build_demo_board(case: str) -> tuple[GomokuBoard, Stone]:
    board = GomokuBoard()

    if case == "empty":
        return board, Stone.BLACK

    if case == "block_four":
        seed_board(
            board,
            [
                (Stone.BLACK, 7, 7),
                (Stone.BLACK, 7, 8),
                (Stone.BLACK, 7, 9),
                (Stone.BLACK, 7, 10),
            ],
        )
        return board, Stone.WHITE

    if case == "win_now":
        seed_board(
            board,
            [
                (Stone.WHITE, 6, 6),
                (Stone.WHITE, 6, 7),
                (Stone.WHITE, 6, 8),
                (Stone.WHITE, 6, 9),
            ],
        )
        return board, Stone.WHITE

    raise ValueError(f"Unknown demo case: {case}")


def run_demo(case: str, ai_stone: Stone | None = None) -> tuple[int, int]:
    board, default_ai_stone = build_demo_board(case)
    ai_stone = ai_stone or default_ai_stone

    ai = HeuristicAI(ai_stone)
    move = ai.select_move(board)
    if move is None:
        raise RuntimeError("AI did not return a move.")

    row, col = move
    print(f"[Demo] case={case}")
    print(f"[Demo] ai_stone={ai_stone.name}")
    print(f"[Demo] selected_move=row={row}, col={col}")

    controller = STM32Controller()
    try:
        ok = controller.execute_move(row, col)
    finally:
        controller.close()

    print(f"[Demo] arm_execute_ok={ok}")
    return row, col


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI-to-arm mock integration demo.")
    parser.add_argument(
        "--case",
        default="empty",
        choices=["empty", "block_four", "win_now"],
        help="Demo board state.",
    )
    parser.add_argument(
        "--ai-stone",
        help="Optional AI stone override: black/white.",
    )
    args = parser.parse_args()

    ai_stone = _stone_from_text(args.ai_stone) if args.ai_stone else None
    run_demo(case=args.case, ai_stone=ai_stone)


if __name__ == "__main__":
    main()
