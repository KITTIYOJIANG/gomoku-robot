from __future__ import annotations
from typing import Optional, Tuple

from .core import GomokuBoard, Stone, Coord
from .ai import HeuristicAI  # 以后你可以换成 HeuristicAI
from .record import GameRecorder

def parse_coord(s: str, size: int) -> Optional[Coord]:
    """
    支持几种输入：
        - "H8" / "h8"
        - "8 8"（行 列，从 1 开始）
    返回内部坐标 (row, col)，从 0 开始。
    """
    s = s.strip()
    if not s:
        return None

    # 形式1：字母+数字，如 H8
    if len(s) >= 2 and s[0].isalpha():
        col_char = s[0].upper()
        if not ("A" <= col_char <= chr(ord("A") + size - 1)):
            return None
        try:
            row_num = int(s[1:])
        except ValueError:
            return None
        col = ord(col_char) - ord("A")
        row = row_num - 1
        if 0 <= row < size and 0 <= col < size:
            return (row, col)
        return None

    # 形式2：数字数字，如 "8 8"
    parts = s.split()
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        row = int(parts[0]) - 1
        col = int(parts[1]) - 1
        if 0 <= row < size and 0 <= col < size:
            return (row, col)

    return None


def human_turn(board: GomokuBoard, player: Stone) -> Optional[Coord]:
    while True:
        coord_str = input(f"轮到 {'黑棋(●)' if player == Stone.BLACK else '白棋(○)'}，请输入坐标（如 H8 或 8 8，输入 q 退出）： ").strip()
        if coord_str.lower() in ("q", "quit", "exit"):
            return None
        coord = parse_coord(coord_str, board.size)
        if coord is None:
            print("坐标格式不对，请重新输入。")
            continue
        row, col = coord
        if not board.is_valid_move(row, col):
            print("该位置已有棋子或不合法，请重新输入。")
            continue
        return coord


def print_board(board: GomokuBoard) -> None:
    print()
    print(board)
    print()


def run_human_vs_ai() -> None:
    """
    人机对战：你执黑先手，AI 执白。
    对局会记录到 GameRecorder，结束后可选择保存棋谱。
    """
    board = GomokuBoard()
    ai = HeuristicAI(Stone.WHITE)
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)

    print("欢迎来到命令行五子棋（人机对战模式）！")
    print("你执黑(●)，AI 执白(○)。")
    print_board(board)

    winner: Optional[Stone] = None

    while True:
        # 人类回合（黑）
        player = Stone.BLACK
        move = human_turn(board, player)
        if move is None:
            print("你选择退出游戏。")
            break
        if not board.place_stone(*move):
            print("落子失败（理论不会出现），请重试。")
            continue

        recorder.add_move(player, move)

        print_board(board)
        winner = board.check_winner()
        if winner is not None:
            print("恭喜，你赢了！（黑方胜）" if winner == Stone.BLACK else "AI 获胜（白方胜）")
            break
        if board.is_full():
            print("棋盘已满，平局。")
            break

        # AI 回合（白）
        print("轮到 AI 思考中……")
        ai_move = ai.select_move(board)
        if ai_move is None:
            print("AI 无棋可下，平局。")
            break
        board.place_stone(*ai_move)
        recorder.add_move(Stone.WHITE, ai_move)

        print(f"AI 落子：行 {ai_move[0]+1}, 列 {chr(ord('A') + ai_move[1])}")
        print_board(board)

        winner = board.check_winner()
        if winner is not None:
            print("AI 获胜（白方胜）" if winner == Stone.WHITE else "你赢了！（黑方胜）")
            break
        if board.is_full():
            print("棋盘已满，平局。")
            break

    # -------- 对局结束，保存棋谱 --------
    recorder.set_winner(winner)
    choice = input("是否保存棋谱到 records/ 目录？(Y/n)：").strip().lower()
    if choice in ("", "y", "yes"):
        path = recorder.save_to_default(prefix="human_vs_ai")
        print(f"棋谱已保存：{path}")
    else:
        print("本局棋谱未保存。")

def run_human_vs_human() -> None:
    """
    双人对战：方便测试。
    """
    board = GomokuBoard()
    print("命令行五子棋（双人对战模式）")
    print_board(board)
    recorder = GameRecorder(board_size=board.size, first_player=Stone.BLACK)

    while True:
        player = board.current_player
        move = human_turn(board, player)
        if move is None:
            print("游戏结束。")
            break
        if not board.place_stone(*move):
            print("落子失败，请重试。")
            continue
        recorder.add_move(player, move)

        print_board(board)
        winner = board.check_winner()
        if winner is not None:
            if winner == Stone.BLACK:
                print("黑棋(●) 获胜！")
            else:
                print("白棋(○) 获胜！")
            break
        if board.is_full():
            print("棋盘已满，平局。")
            break

        # -------- 对局结束，保存棋谱 --------
        recorder.set_winner(winner)
        choice = input("是否保存棋谱到 records/ 目录？(Y/n)：").strip().lower()
        if choice in ("", "y", "yes"):
            path = recorder.save_to_default(prefix="human_vs_ai")
            print(f"棋谱已保存：{path}")
        else:
            print("本局棋谱未保存。")


def main() -> None:
    print("请选择模式：")
    print("1. 人机对战（你 vs AI）")
    print("2. 双人对战（本地）")
    choice = input("输入 1 或 2（默认 1）： ").strip()
    if choice == "2":
        run_human_vs_human()
    else:
        run_human_vs_ai()


if __name__ == "__main__":
    main()

# python -m gomoku.cli 运行游戏