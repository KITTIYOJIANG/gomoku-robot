from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .core import Coord, Stone


@dataclass
class MoveRecord:
    index: int
    player: int
    row: int
    col: int
    played_at: str


@dataclass
class GameRecord:
    board_size: int
    first_player: int
    winner: Optional[int]
    moves: List[MoveRecord]
    created_at: str


class GameRecorder:
    """JSON game recorder for CLI, GUI and self-play experiments."""

    def __init__(self, board_size: int, first_player: Stone) -> None:
        self.board_size = board_size
        self.first_player = int(first_player)
        self._moves: List[MoveRecord] = []
        self._winner: Optional[int] = None
        self._created_at = datetime.now().isoformat(timespec="seconds")

    def add_move(self, player: Stone, coord: Coord) -> None:
        row, col = coord
        self._moves.append(
            MoveRecord(
                index=len(self._moves) + 1,
                player=int(player),
                row=row,
                col=col,
                played_at=datetime.now().isoformat(timespec="seconds"),
            )
        )

    def set_winner(self, winner: Optional[Stone]) -> None:
        self._winner = int(winner) if winner is not None else None

    def to_dict(self) -> dict:
        return asdict(
            GameRecord(
                board_size=self.board_size,
                first_player=self.first_player,
                winner=self._winner,
                moves=self._moves,
                created_at=self._created_at,
            )
        )

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def save_to_default(self, prefix: str = "human_vs_ai") -> Path:
        records_dir = Path.cwd() / "records"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.save(records_dir / f"{prefix}_{timestamp}.json")

    @staticmethod
    def load(path: Path) -> GameRecord:
        data = json.loads(path.read_text(encoding="utf-8"))
        moves = [
            MoveRecord(
                index=m["index"],
                player=m["player"],
                row=m["row"],
                col=m["col"],
                played_at=m.get("played_at", ""),
            )
            for m in data["moves"]
        ]
        return GameRecord(
            board_size=data["board_size"],
            first_player=data["first_player"],
            winner=data.get("winner"),
            moves=moves,
            created_at=data["created_at"],
        )
