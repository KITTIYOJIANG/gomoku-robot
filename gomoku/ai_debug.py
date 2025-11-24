from __future__ import annotations

from .core import GomokuBoard, Stone
from .ai import HeuristicAI


def print_board(board: GomokuBoard) -> None:
    print()
    print(board)
    print()


def put(board: GomokuBoard, stone: Stone, row: int, col: int) -> None:
    """直接往棋盘上摆子，用于测试（不走正常轮转逻辑）"""
    if board.grid[row][col] != Stone.EMPTY:
        raise ValueError(f"({row}, {col}) 已有棋子")
    board.grid[row][col] = stone
    board.move_count += 1
    board.last_move = (row, col)


def test_block_open_four() -> None:
    """
    测试1：黑棋已经有一条活四，白棋必须堵。
    预期：AI（白）在这条线两端任意一个位置落子。
    """
    print("=" * 60)
    print("测试1：堵对方活四")

    board = GomokuBoard()
    # 在第 8 行（索引7），摆出黑棋 4 连： (7,7)-(7,10)
    row = 7
    for col in range(7, 11):
        put(board, Stone.BLACK, row, col)

    print_board(board)
    ai = HeuristicAI(Stone.WHITE)
    move = ai.select_move(board)
    print("AI 选择落子位置(行,列索引，从0开始)：", move)

    if move is None:
        print("❌ AI 没有找到落点（错误）")
        return

    r, c = move
    if r == row and c in (6, 11):
        print("✅ 通过：AI 正确选择在活四的一端进行堵截。")
    else:
        print("⚠ AI 没有选择最佳堵点，但后续可以通过调参/改算法继续优化。")


def test_make_own_five() -> None:
    """
    测试2：白棋自己已经有 4 连，只差一步就能五连。
    预期：AI 直接在能连成五的点上落子。
    """
    print("=" * 60)
    print("测试2：自己已经有四连，AI 应该直接连五取胜")

    board = GomokuBoard()
    row = 5
    # 白棋四连 (5,5)-(5,8)，两边空
    for col in range(5, 9):
        put(board, Stone.WHITE, row, col)

    # 随便放几个黑棋干扰，避免太理想化
    put(board, Stone.BLACK, 6, 6)
    put(board, Stone.BLACK, 6, 7)

    print_board(board)
    ai = HeuristicAI(Stone.WHITE)
    move = ai.select_move(board)
    print("AI 选择落子位置(行,列索引，从0开始)：", move)

    if move is None:
        print("❌ AI 没有找到落点（错误）")
        return

    r, c = move
    if r == row and c in (4, 9):
        print("✅ 通过：AI 选择在四连的一端落子，形成五连。")
    else:
        print("⚠ AI 没有直接在四连两端落子，可以考虑优化评价函数。")


def test_mid_game_sense() -> None:
    """
    测试3：中盘局面，看看 AI 是否会往已有棋子附近下，而不是乱飞。
    """
    print("=" * 60)
    print("测试3：中盘局面落子倾向")

    board = GomokuBoard()

    # 随机构造一个中盘：黑白各若干子
    moves = [
        (Stone.BLACK, 7, 7),
        (Stone.WHITE, 7, 8),
        (Stone.BLACK, 8, 7),
        (Stone.WHITE, 6, 7),
        (Stone.BLACK, 8, 8),
        (Stone.WHITE, 6, 8),
    ]
    for stone, r, c in moves:
        put(board, stone, r, c)

    print_board(board)
    ai = HeuristicAI(Stone.WHITE)
    move = ai.select_move(board)
    print("AI 选择落子位置(行,列索引，从0开始)：", move)

    if move is None:
        print("❌ AI 没有找到落点（错误）")
        return

    r, c = move
    # 检查是否在已有棋子附近（曼哈顿距离 <= 3）
    near_any = any(
        abs(r - rr) + abs(c - cc) <= 3
        for (_, rr, cc) in moves
    )
    if near_any:
        print("✅ AI 倾向在已有棋子附近落子，行为看起来比较合理。")
    else:
        print("⚠ AI 选择的位置比较偏远，可能需要调 search_radius 或评分。")


def main() -> None:
    test_block_open_four()
    test_make_own_five()
    test_mid_game_sense()


if __name__ == "__main__":
    main()
