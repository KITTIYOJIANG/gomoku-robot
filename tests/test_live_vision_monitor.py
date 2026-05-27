from pathlib import Path
import shutil
import uuid

from tools.live_vision_monitor import append_label_stub, next_capture_index


def make_workspace_tmp() -> Path:
    path = Path("tmp") / "test_live_vision_monitor" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_append_label_stub_creates_benchmark_label_block():
    workdir = make_workspace_tmp()
    label_path = workdir / "label.txt"

    try:
        append_label_stub(label_path, "live_board_001.jpg")
        append_label_stub(label_path, "live_board_002.jpg")

        assert label_path.read_text(encoding="utf-8") == (
            "live_board_001.jpg\n"
            "black:\n"
            "white:\n"
            "\n"
            "live_board_002.jpg\n"
            "black:\n"
            "white:\n"
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_append_label_stub_does_not_duplicate_existing_image():
    workdir = make_workspace_tmp()
    label_path = workdir / "label.txt"

    try:
        append_label_stub(label_path, "live_board_001.jpg")
        append_label_stub(label_path, "live_board_001.jpg")

        assert label_path.read_text(encoding="utf-8").count("live_board_001.jpg") == 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_next_capture_index_skips_existing_images():
    workdir = make_workspace_tmp()

    try:
        (workdir / "live_board_001.jpg").write_bytes(b"")
        (workdir / "live_board_002.jpg").write_bytes(b"")

        assert next_capture_index(workdir, "live_board", 1) == 3
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
