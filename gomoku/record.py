from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

from .core import Stone, Coord


@dataclass
class MoveRecord:
    index: int           # 第几手，从 1 开始
    player: int          # 1=黑, 2=白
    row: int             # 0-based
    col: int             # 0-based
    played_at: str       # ISO 时间字符串，可选


@dataclass
class GameRecord:
    board_size: int
    first_player: int
    winner: Optional[int]        # 1/2 或 None（平局/未完）
    moves: List[MoveRecord]
    created_at: str


class GameRecorder:
    """
    简单棋谱记录器：
    - 每落一子调用 add_move
    - 对局结束调用 set_winner
    - 调用 save()/save_to_default 保存为 JSON 文件
    """

    def __init__(self, board_size: int, first_player: Stone) -> None:
        self.board_size = board_size
        self.first_player = int(first_player)
        self._moves: List[MoveRecord] = []
        self._winner: Optional[int] = None
        self._created_at = datetime.now().isoformat(timespec="seconds")

    # -------- 记录落子 --------
    def add_move(self, player: Stone, coord: Coord) -> None:
        idx = len(self._moves) + 1
        row, col = coord
        mr = MoveRecord(
            index=idx,
            player=int(player),
            row=row,
            col=col,
            played_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._moves.append(mr)

    def set_winner(self, winner: Optional[Stone]) -> None:
        self._winner = int(winner) if winner is not None else None

    # -------- 序列化 & 保存 --------
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
        data = self.to_dict()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def save_to_default(self, prefix: str = "human_vs_ai") -> Path:
        """
        保存到当前工作目录下的 records/ 目录，
        文件名形如 human_vs_ai_20251125_143012.json
        """
        records_dir = Path.cwd() / "records"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        return self.save(records_dir / filename)

    # -------- 从文件加载（给回放用） --------
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