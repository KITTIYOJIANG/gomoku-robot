from __future__ import annotations

from typing import Optional, Tuple

from .ai import HeuristicAI, RandomAI
from .core import GomokuBoard, Stone
from .record import GameRecorder


Result = Tuple[Optional[Stone], int]


def play_single_game(
    use_random_black: bool = False,
    use_random_white: bool = False,
    save_record: bool = False,
    prefix: str = "ai_vs_ai",
) -> Result:
    board = GomokuBoard()
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)

    black_ai = RandomAI(Stone.BLACK) if use_random_black else HeuristicAI(Stone.BLACK)
    white_ai = RandomAI(Stone.WHITE) if use_random_white else HeuristicAI(Stone.WHITE)
    winner: Optional[Stone] = None

    while True:
        player = board.current_player
        ai = black_ai if player == Stone.BLACK else white_ai
        move = ai.select_move(board)
        if move is None or not board.place_stone(*move):
            break

        recorder.add_move(player, move)
        winner = board.check_winner()
        if winner is not None or board.is_full():
            break

    recorder.set_winner(winner)
    if save_record:
        recorder.save_to_default(prefix=prefix)
    return winner, board.move_count


def run_batch_games(
    num_games: int,
    use_random_black: bool = False,
    use_random_white: bool = False,
    save_records: bool = False,
    prefix: str = "ai_vs_ai",
) -> None:
    black_wins = 0
    white_wins = 0
    draws = 0
    total_moves = 0

    for i in range(1, num_games + 1):
        winner, move_count = play_single_game(
            use_random_black=use_random_black,
            use_random_white=use_random_white,
            save_record=save_records,
            prefix=prefix,
        )
        total_moves += move_count
        if winner == Stone.BLACK:
            black_wins += 1
        elif winner == Stone.WHITE:
            white_wins += 1
        else:
            draws += 1
        print(f"Game {i}: winner={winner}, moves={move_count}")

    print("\nSelf-play summary")
    print(f"games: {num_games}")
    print(f"black wins: {black_wins}")
    print(f"white wins: {white_wins}")
    print(f"draws: {draws}")
    if num_games:
        print(f"average moves: {total_moves / num_games:.1f}")


def main() -> None:
    print("AI self-play experiment")
    print("1. Heuristic black vs Heuristic white")
    print("2. Heuristic black vs Random white")
    print("3. Random black vs Heuristic white")
    choice = input("Mode (default 1): ").strip()

    use_random_black = choice == "3"
    use_random_white = choice == "2"
    prefix = {
        "2": "heuristic_vs_randomW",
        "3": "randomB_vs_heuristic",
    }.get(choice, "heuristic_vs_heuristic")

    n_text = input("Number of games (default 10): ").strip()
    num_games = int(n_text) if n_text.isdigit() and int(n_text) > 0 else 10
    save_text = input("Save records? (y/N): ").strip().lower()
    save_records = save_text in ("y", "yes")

    run_batch_games(
        num_games=num_games,
        use_random_black=use_random_black,
        use_random_white=use_random_white,
        save_records=save_records,
        prefix=prefix,
    )


if __name__ == "__main__":
    main()
