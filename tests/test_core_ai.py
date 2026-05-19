from gomoku.ai import HeuristicAI
from gomoku.core import GomokuBoard, Stone


def put(board: GomokuBoard, stone: Stone, row: int, col: int) -> None:
    board.grid[row][col] = stone
    board.last_move = (row, col)
    board.move_count += 1


def test_place_stone_and_winner():
    board = GomokuBoard()
    for col in range(4):
        assert board.place_stone(7, col)
        assert board.place_stone(8, col)
    assert board.place_stone(7, 4)
    assert board.check_winner() == Stone.BLACK


def test_ai_opens_center():
    board = GomokuBoard()
    ai = HeuristicAI(Stone.BLACK)
    assert ai.select_move(board) == (7, 7)


def test_ai_blocks_open_four():
    board = GomokuBoard()
    for col in range(7, 11):
        put(board, Stone.BLACK, 7, col)
    ai = HeuristicAI(Stone.WHITE)
    assert ai.select_move(board) in [(7, 6), (7, 11)]
