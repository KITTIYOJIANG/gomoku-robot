from __future__ import annotations

from .ai import HeuristicAI
from .core import GomokuBoard, Stone


def put(board: GomokuBoard, stone: Stone, row: int, col: int) -> None:
    if board.grid[row][col] != Stone.EMPTY:
        raise ValueError(f"({row}, {col}) already occupied")
    board.grid[row][col] = stone
    board.move_count += 1
    board.last_move = (row, col)


def test_block_open_four() -> None:
    board = GomokuBoard()
    row = 7
    for col in range(7, 11):
        put(board, Stone.BLACK, row, col)

    ai = HeuristicAI(Stone.WHITE)
    move = ai.select_move(board)
    print(board)
    print("block-open-four move:", move)


def test_make_own_five() -> None:
    board = GomokuBoard()
    row = 5
    for col in range(5, 9):
        put(board, Stone.WHITE, row, col)
    put(board, Stone.BLACK, 6, 6)
    put(board, Stone.BLACK, 6, 7)

    ai = HeuristicAI(Stone.WHITE)
    move = ai.select_move(board)
    print(board)
    print("make-own-five move:", move)


def main() -> None:
    test_block_open_four()
    print("=" * 60)
    test_make_own_five()


if __name__ == "__main__":
    main()
