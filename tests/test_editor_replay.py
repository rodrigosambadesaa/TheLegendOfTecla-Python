from pathlib import Path

from legend_of_tecla.editor import apply_brush, load_editor_scenario, make_blank_scenario, save_scenario
from legend_of_tecla.game import GameConfig
from legend_of_tecla.model import Position
from legend_of_tecla.replay import load_replay, record_replay, replay_commands, save_replay
from legend_of_tecla.world import InteractiveState, InteractiveType


def test_editor_brushes_and_json_roundtrip(tmp_path: Path):
    grid = make_blank_scenario(5, 7)
    apply_brush(grid, Position(1, 1), "muro")
    apply_brush(grid, Position(2, 2), "puerta")
    apply_brush(grid, Position(3, 3), "trampa")
    apply_brush(grid, Position(4, 6), "objetivo")

    assert grid.cell(Position(1, 1)).walkable is False
    assert grid.cell(Position(2, 2)).element.kind is InteractiveType.DOOR
    assert grid.cell(Position(2, 2)).element.state is InteractiveState.CLOSED
    assert grid.cell(Position(3, 3)).element.kind is InteractiveType.TRAP
    assert grid.goal == Position(4, 6)

    path = tmp_path / "escenario.json"
    save_scenario(grid, path, con_aliados=True)
    loaded = load_editor_scenario(path)
    assert loaded.rows == 5
    assert loaded.cols == 7
    assert loaded.cell(Position(2, 2)).element.kind is InteractiveType.DOOR


def test_replay_records_and_validates(tmp_path: Path):
    replay = record_replay(GameConfig(seed=21, dimensions=(6, 6)), ["inspeccionar", "mover este", "estado"])
    report = replay_commands(replay)

    assert report.ok is True
    assert report.final_sha256 == replay.final_sha256
    assert len(report.outputs) == 3

    path = tmp_path / "replay.json"
    save_replay(replay, path)
    loaded = load_replay(path)
    assert replay_commands(loaded).ok is True


def test_replay_detects_tampering():
    replay = record_replay(GameConfig(seed=22), ["inspeccionar"])
    replay.commands.append("mover este")

    report = replay_commands(replay)

    assert report.ok is False
