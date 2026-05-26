from demo_ai_to_arm_mock import build_demo_board
from gomoku.ai import HeuristicAI
from gomoku.core import Stone


def test_empty_demo_opens_center():
    board, ai_stone = build_demo_board("empty")
    assert ai_stone == Stone.BLACK
    assert HeuristicAI(ai_stone).select_move(board) == (7, 7)


def test_block_four_demo_blocks_black_threat():
    board, ai_stone = build_demo_board("block_four")
    assert ai_stone == Stone.WHITE
    assert HeuristicAI(ai_stone).select_move(board) in [(7, 6), (7, 11)]


def test_win_now_demo_takes_winning_move():
    board, ai_stone = build_demo_board("win_now")
    assert ai_stone == Stone.WHITE
    assert HeuristicAI(ai_stone).select_move(board) in [(6, 5), (6, 10)]
