from __future__ import annotations

from pathlib import Path
from typing import Optional

from .core import GomokuBoard, Stone
from .record import GameRecord, GameRecorder


def choose_record_file() -> Optional[Path]:
    records_dir = Path.cwd() / "records"
    if not records_dir.exists():
        print("No records directory found.")
        return None

    files = sorted(records_dir.glob("*.json"))
    if not files:
        print("No JSON records found.")
        return None

    for i, path in enumerate(files, start=1):
        print(f"{i}. {path.name}")

    while True:
        choice = input(f"Choose record (1-{len(files)}, q to quit): ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        print("Invalid choice.")


def print_board(board: GomokuBoard) -> None:
    print()
    print(board)
    print()


def replay_game(record: GameRecord, wait_for_enter: bool = True) -> None:
    board = GomokuBoard(size=record.board_size)
    print(f"Replay: {record.board_size}x{record.board_size}")
    print_board(board)

    for move in record.moves:
        if wait_for_enter:
            input(f"Press Enter for move {move.index}...")
        board.grid[move.row][move.col] = Stone(move.player)
        board.last_move = (move.row, move.col)
        board.move_count += 1
        print_board(board)

    print("Replay finished.")


def main() -> None:
    path = choose_record_file()
    if path is None:
        return
    replay_game(GameRecorder.load(path))


if __name__ == "__main__":
    main()
