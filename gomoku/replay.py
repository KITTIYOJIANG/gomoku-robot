from __future__ import annotations
from pathlib import Path
from typing import Optional

from .core import GomokuBoard, Stone
from .record import GameRecorder, GameRecord, MoveRecord


def print_board(board: GomokuBoard) -> None:
    print()
    print(board)
    print()


def choose_record_file() -> Optional[Path]:
    """
    在当前工作目录的 records/ 下列出所有棋谱文件，
    让你选择一个来回放。
    """
    records_dir = Path.cwd() / "records"
    if not records_dir.exists():
        print("当前目录下还没有 records/ 目录。先打一盘并保存棋谱吧。")
        return None

    files = sorted(records_dir.glob("*.json"))
    if not files:
        print("records/ 目录中没有棋谱文件。")
        return None

    print("找到以下棋谱文件：")
    for i, f in enumerate(files, start=1):
        print(f"{i}. {f.name}")

    while True:
        choice = input(f"请选择要回放的棋谱序号 (1-{len(files)}，或 q 退出)：").strip()
        if choice.lower() in ("q", "quit", "exit"):
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(files):
                return files[idx - 1]
        print("输入不合法，请重新输入。")


def replay_game(record: GameRecord) -> None:
    board = GomokuBoard(size=record.board_size)
    print("开始回放棋局：")
    print(f"棋盘大小：{record.board_size}x{record.board_size}")
    print(f"先手：{'黑' if record.first_player == int(Stone.BLACK) else '白'}")
    if record.winner is not None:
        print(f"胜者：{'黑' if record.winner == int(Stone.BLACK) else '白'}")
    else:
        print("胜者：平局或未标记")
    print_board(board)

    for move in record.moves:
        input(f"按回车查看第 {move.index} 手（{'黑' if move.player == 1 else '白'}）...")
        stone = Stone(move.player)
        board.grid[move.row][move.col] = stone
        board.last_move = (move.row, move.col)
        board.move_count += 1
        print_board(board)

    print("回放结束。")


def main() -> None:
    path = choose_record_file()
    if path is None:
        return
    record = GameRecorder.load(path)
    replay_game(record)


if __name__ == "__main__":
    main()