"""Adapter from the Gomoku host GUI to the standalone arm controller repo.

The host project should decide *where* to place a stone. The standalone
`gomoku-arm-controller` repo is responsible for *how* the robotic arm moves.

This adapter keeps the old `STM32Controller.execute_move(row, col)` interface
so the current PyQt GUI can keep running while the low-level arm code lives in
a separate repository.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _add_local_arm_repo_to_path() -> None:
    """Add a sibling local arm-controller repo during development.

    Expected local layout:

        D:/Projects/gomoku_project
        D:/Projects/gomoku_arm_controller

    Users can override this with GOMOKU_ARM_CONTROLLER_PATH.
    """

    configured_path = os.getenv("GOMOKU_ARM_CONTROLLER_PATH")
    if configured_path:
        arm_repo = Path(configured_path)
    else:
        arm_repo = Path(__file__).resolve().parents[2] / "gomoku_arm_controller"

    if arm_repo.exists():
        arm_repo_str = str(arm_repo)
        if arm_repo_str not in sys.path:
            sys.path.insert(0, arm_repo_str)


_add_local_arm_repo_to_path()


try:
    from arm_controller.stm32_controller import STM32ArmController
except ImportError:
    STM32ArmController = None


class STM32Controller:
    """Compatibility wrapper used by the PyQt host application."""

    def __init__(self, port: str = "COM5", baudrate: int = 115200, mock: bool | None = None):
        if mock is None:
            mock_env = os.getenv("GOMOKU_ARM_MOCK", "1").strip().lower()
            mock = mock_env not in ("0", "false", "no")

        self.port = port
        self.baudrate = baudrate
        self.mock = mock
        self._controller = None

        if STM32ArmController is None:
            print(
                "[ArmAdapter] gomoku-arm-controller not found. "
                "Set GOMOKU_ARM_CONTROLLER_PATH or clone it next to gomoku_project."
            )
            return

        self._controller = STM32ArmController(
            port=self.port,
            baudrate=self.baudrate,
            mock=self.mock,
        )
        mode = "mock" if self.mock else "serial"
        print(f"[ArmAdapter] Connected to standalone arm controller ({mode} mode).")

    def execute_move(self, row: int, col: int) -> bool:
        if self._controller is None:
            print(f"[ArmAdapter] No arm controller available. Target move: row={row}, col={col}")
            return False

        self._controller.place_stone(row, col)
        return True

    def close(self) -> None:
        if self._controller is not None:
            self._controller.close()
