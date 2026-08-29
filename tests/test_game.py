from pathlib import Path

import pytest

from legend_of_tecla import GameConfig, create_game, load_game, save_game
from legend_of_tecla.catalog import make_item
from legend_of_tecla.game import load_scenario
from legend_of_tecla.model import Difficulty, Position, VictoryCondition
from legend_of_tecla.world import InteractiveState, InteractiveType


def test_default_game_runs_and_renders():
    game = create_game(GameConfig(player_name="Rodrigo", seed=1))
    text = game.render()
    assert "J" in text
    assert "X" in text
    response = game.execute("ayuda")
    assert "mover" in response


def test_move_pickup_equip_and_attack():
    game = create_game(GameConfig(seed=2, dimensions=(6, 6)))
    game.grid.place_item(Position(0, 1), make_item("espada_corta", "espada_test"))
    assert "mueves" in game.execute("mover este")
    assert "espada_test" in game.execute("recoger")
    assert "equipa" in game.execute("equipar espada_test")
    enemy = game.living_enemies()[0]
    enemy.position = Position(0, 2)
    old_hp = enemy.hp
    result = game.execute("atacar este")
    assert enemy.hp < old_hp
    assert "Golpeas" in result


def test_save_and_load_roundtrip(tmp_path: Path):
    game = create_game(GameConfig(seed=3, allies=2, victory_condition=VictoryCondition.PLAYER_AND_ALLIES))
    target = tmp_path / "save.json"
    save_game(game, target)
    loaded = load_game(target)
    assert loaded.player.name == game.player.name
    assert len(loaded.allies) == 2
    assert loaded.grid.rows == game.grid.rows


def test_load_txt_scenario():
    grid = load_scenario(Path("data/escenario_basico"))
    assert grid.rows == 6
    assert grid.cols == 6
    assert grid.cell(Position(2, 2)).dark is True
    assert grid.cell(Position(3, 1)).water_source is True


def test_json_scenario_interactive_elements():
    grid = load_scenario(Path("data/escenario_json"))
    cell = grid.cell(Position(2, 4))
    assert cell.element.kind is InteractiveType.DOOR
    assert cell.element.state is InteractiveState.LOCKED


def test_procedural_seed_is_reproducible():
    a = create_game(GameConfig(mode="procedural", seed=123, dimensions=(10, 10)))
    b = create_game(GameConfig(mode="procedural", seed=123, dimensions=(10, 10)))
    assert a.render() == b.render()


def test_allies_and_enemy_scaling_respects_limit():
    game = create_game(GameConfig(mode="grande", allies=12, difficulty=Difficulty.INSANE, variant=5))
    assert len(game.enemies) <= len(game.allies) + 1
    assert any(ally.role == "medico" for ally in game.allies)


def test_crafting_consumes_ingredients():
    game = create_game(GameConfig(seed=4))
    game.player.add_item(make_item("chatarra"))
    game.player.add_item(make_item("polvora"))
    result = game.execute("fabricar granada")
    assert "Fabricas" in result
    assert any(item.name == "granada_casera" for item in game.player.inventory)


def test_corrupt_save_rejected(tmp_path: Path):
    target = tmp_path / "bad.json"
    target.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError):
        load_game(target)
