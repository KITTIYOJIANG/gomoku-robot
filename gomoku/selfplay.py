from __future__ import annotations

from typing import Optional, Tuple
from pathlib import Path

from .core import GomokuBoard, Stone
from .ai import HeuristicAI, RandomAI
from .record import GameRecorder


Result = Tuple[Optional[Stone], int]  # (winner, move_count)


def play_single_game(
    use_random_black: bool = False,
    use_random_white: bool = False,
    save_record: bool = False,
    prefix: str = "ai_vs_ai",
) -> Result:
    """
    进行一局 AI vs AI 的自对弈。

    :param use_random_black: 黑方是否使用 RandomAI（用于对比实验）
    :param use_random_white: 白方是否使用 RandomAI
    :param save_record: 是否保存棋谱
    :param prefix: 棋谱文件名前缀
    :return: (winner, move_count)
    """
    board = GomokuBoard()
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)

    # 配置黑白双方 AI
    if use_random_black:
        black_ai = RandomAI(Stone.BLACK)
    else:
        black_ai = HeuristicAI(Stone.BLACK)

    if use_random_white:
        white_ai = RandomAI(Stone.WHITE)
    else:
        white_ai = HeuristicAI(Stone.WHITE)

    current = Stone.BLACK
    winner: Optional[Stone] = None

    while True:
        ai = black_ai if current == Stone.BLACK else white_ai
        move = ai.select_move(board)
        if move is None or not board.is_valid_move(*move):
            # 当前方无子可下 → 平局
            winner = None
            break

        board.place_stone(*move)
        recorder.add_move(current, move)

        winner = board.check_winner()
        if winner is not None or board.is_full():
            break

        current = board.current_player

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
    """
    连续跑多局 AI 自对弈，用于实验统计。
    """
    black_wins = 0
    white_wins = 0
    draws = 0
    total_moves = 0

    for i in range(1, num_games + 1):
        print(f"\n=== 第 {i} 局 / 共 {num_games} 局 ===")
        winner, move_count = play_single_game(
            use_random_black=use_random_black,
            use_random_white=use_random_white,
            save_record=save_records,
            prefix=prefix,
        )

        total_moves += move_count

        if winner == Stone.BLACK:
            black_wins += 1
            print(f"结果：黑方胜（总步数 {move_count}）")
        elif winner == Stone.WHITE:
            white_wins += 1
            print(f"结果：白方胜（总步数 {move_count}）")
        else:
            draws += 1
            print(f"结果：平局（总步数 {move_count}）")

    print("\n=== 实验统计结果 ===")
    print(f"总局数：{num_games}")
    print(f"黑方胜：{black_wins}")
    print(f"白方胜：{white_wins}")
    print(f"平局数：{draws}")
    if num_games > 0:
        print(f"平均步数：{total_moves / num_games:.1f}")


def run_console_menu() -> None:
    """
    命令行交互入口：
    让你选择对局类型 & 局数，方便做实验。
    """
    print("=== AI 自对弈实验 ===")
    print("请选择对局类型：")
    print("1. HeuristicAI (黑) vs HeuristicAI (白)")
    print("2. HeuristicAI (黑) vs RandomAI (白)")
    print("3. RandomAI (黑) vs HeuristicAI (白)")
    choice = input("输入 1/2/3（默认 1）：").strip()

    if choice == "2":
        use_random_black = False
        use_random_white = True
        prefix = "heuristic_vs_randomW"
    elif choice == "3":
        use_random_black = True
        use_random_white = False
        prefix = "randomB_vs_heuristic"
    else:
        use_random_black = False
        use_random_white = False
        prefix = "heuristic_vs_heuristic"

    while True:
        n_str = input("请输入要对弈的局数（正整数，默认 10）：").strip()
        if not n_str:
            num_games = 10
            break
        if n_str.isdigit() and int(n_str) > 0:
            num_games = int(n_str)
            break
        print("输入不合法，请重新输入。")

    save_ans = input("是否保存每一局棋谱到 records/ 目录？(Y/n)：").strip().lower()
    save_records = (save_ans == "" or save_ans in ("y", "yes"))

    run_batch_games(
        num_games=num_games,
        use_random_black=use_random_black,
        use_random_white=use_random_white,
        save_records=save_records,
        prefix=prefix,
    )


def main() -> None:
    run_console_menu()


if __name__ == "__main__":
    main()