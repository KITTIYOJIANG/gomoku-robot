from __future__ import annotations

import random
import traceback

from .core import GomokuBoard, Stone

try:
    from .ai import HeuristicAI
except ImportError:
    HeuristicAI = None


def get_best_move(board: GomokuBoard, ai_color: Stone):
    """Return the next AI move as `(row, col)`.

    This is the GUI-facing adapter. It keeps the PyQt layer simple while the
    concrete AI implementation can be changed in `gomoku.ai`.
    """

    ai_color = Stone(ai_color)
    print("[AI] analyzing board...")

    if HeuristicAI is not None:
        try:
            ai = HeuristicAI(ai_color)
            best_move = ai.select_move(board)
            if best_move is not None:
                print(f"[AI] selected move: row={best_move[0]}, col={best_move[1]}")
                return best_move
        except Exception:
            print("[AI] heuristic AI failed; falling back to random move.")
            print(traceback.format_exc())

    empty_spots = [
        (r, c)
        for r in range(board.size)
        for c in range(board.size)
        if board.grid[r][c] == Stone.EMPTY
    ]
    if empty_spots:
        return random.choice(empty_spots)

    return None, None
