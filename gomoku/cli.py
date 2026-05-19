from __future__ import annotations

from typing import Optional

from .ai import HeuristicAI
from .core import Coord, GomokuBoard, Stone
from .record import GameRecorder


def parse_coord(text: str, size: int) -> Optional[Coord]:
    text = text.strip()
    if not text:
        return None

    if len(text) >= 2 and text[0].isalpha():
        col_char = text[0].upper()
        if not ("A" <= col_char <= chr(ord("A") + size - 1)):
            return None
        try:
            row_num = int(text[1:])
        except ValueError:
            return None
        row = row_num - 1
        col = ord(col_char) - ord("A")
        return (row, col) if 0 <= row < size and 0 <= col < size else None

    parts = text.split()
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        row = int(parts[0]) - 1
        col = int(parts[1]) - 1
        return (row, col) if 0 <= row < size and 0 <= col < size else None

    return None


def print_board(board: GomokuBoard) -> None:
    print()
    print(board)
    print()


def human_turn(board: GomokuBoard, player: Stone) -> Optional[Coord]:
    label = "black" if player == Stone.BLACK else "white"
    while True:
        text = input(f"{label} move, enter H8 or '8 8' (q to quit): ").strip()
        if text.lower() in ("q", "quit", "exit"):
            return None
        coord = parse_coord(text, board.size)
        if coord is None:
            print("Invalid coordinate format.")
            continue
        if not board.is_valid_move(*coord):
            print("Illegal move.")
            continue
        return coord


def run_human_vs_ai() -> None:
    board = GomokuBoard()
    ai = HeuristicAI(Stone.WHITE)
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)
    winner: Optional[Stone] = None

    print("CLI Gomoku: human black vs AI white")
    print_board(board)

    while True:
        human_move = human_turn(board, Stone.BLACK)
        if human_move is None:
            print("Game aborted.")
            break
        board.place_stone(*human_move)
        recorder.add_move(Stone.BLACK, human_move)
        print_board(board)

        winner = board.check_winner()
        if winner is not None or board.is_full():
            break

        ai_move = ai.select_move(board)
        if ai_move is None:
            break
        board.place_stone(*ai_move)
        recorder.add_move(Stone.WHITE, ai_move)
        print(f"AI move: row {ai_move[0] + 1}, col {chr(ord('A') + ai_move[1])}")
        print_board(board)

        winner = board.check_winner()
        if winner is not None or board.is_full():
            break

    recorder.set_winner(winner)
    if winner is None:
        print("Result: draw or unfinished")
    else:
        print(f"Result: {'black' if winner == Stone.BLACK else 'white'} wins")

    choice = input("Save record to records/? (Y/n): ").strip().lower()
    if choice in ("", "y", "yes"):
        print(f"Record saved: {recorder.save_to_default(prefix='human_vs_ai')}")


def run_human_vs_human() -> None:
    board = GomokuBoard()
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)
    winner: Optional[Stone] = None

    print("CLI Gomoku: human vs human")
    print_board(board)

    while True:
        player = board.current_player
        move = human_turn(board, player)
        if move is None:
            print("Game aborted.")
            break
        board.place_stone(*move)
        recorder.add_move(player, move)
        print_board(board)

        winner = board.check_winner()
        if winner is not None or board.is_full():
            break

    recorder.set_winner(winner)
    choice = input("Save record to records/? (Y/n): ").strip().lower()
    if choice in ("", "y", "yes"):
        print(f"Record saved: {recorder.save_to_default(prefix='human_vs_human')}")


def main() -> None:
    print("Select mode:")
    print("1. Human vs AI")
    print("2. Human vs human")
    choice = input("Mode (default 1): ").strip()
    if choice == "2":
        run_human_vs_human()
    else:
        run_human_vs_ai()


if __name__ == "__main__":
    main()
