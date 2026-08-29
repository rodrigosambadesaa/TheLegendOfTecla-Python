import json
from pathlib import Path

from legend_of_tecla.audio import AudioNulo
from legend_of_tecla.facade import crear_partida
from legend_of_tecla.game import GameConfig
from legend_of_tecla.model import ItemType, Position
from legend_of_tecla.runtime import SesionJuego
from legend_of_tecla.catalog import make_item


def test_runtime_session_parses_short_commands_and_records_history():
    game = crear_partida(GameConfig(dimensions=(4, 4), seed=1))
    audio = AudioNulo()
    session = SesionJuego(game, audio=audio)

    output = session.ejecutar("m este")

    assert "paso" in output.lower() or "mueves" in output.lower()
    assert session.game.player.position == Position(0, 1)
    assert session.historial[-1].comando == "m este"
    assert session.historial[-1].normalizado == "mover este"
    assert "mover" in audio.eventos


def test_runtime_session_syncs_extended_achievements():
    game = crear_partida(GameConfig(dimensions=(4, 4), seed=2))
    game.statistics.enemies_killed = 5
    game.statistics.items_collected = 10
    game.statistics.turns = 3
    session = SesionJuego(game, audio=AudioNulo())

    output = session.ejecutar("estado")

    assert "Logro ampliado" in output
    assert session.game.achievements["limpieza"].unlocked is True
    assert session.game.achievements["coleccionista"].unlocked is True
    assert "logro" in session.audio.eventos


def test_runtime_session_can_save_and_reload_versioned_game(tmp_path: Path):
    game = crear_partida(GameConfig(dimensions=(4, 4), seed=3))
    session = SesionJuego(game)
    session.ejecutar("m sur")
    path = tmp_path / "partida.json"

    session.guardar(path)
    session.ejecutar("m este")
    session.cargar(path)

    assert session.game.player.position == Position(1, 0)
    assert session.historial


def test_runtime_save_load_commands_use_versioned_persistence(tmp_path: Path):
    game = crear_partida(GameConfig(dimensions=(4, 4), seed=33))
    session = SesionJuego(game, audio=AudioNulo())
    path = tmp_path / "partida_cmd.json"

    save_output = session.ejecutar(f"guardar {path}")
    session.ejecutar("m sur")
    load_output = session.ejecutar(f"cargar {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert save_output.startswith("Partida guardada")
    assert load_output.startswith("Partida cargada")
    assert "metadata" in data
    assert "payload" in data
    assert session.game.player.position == Position(0, 0)
    assert "guardar" in session.audio.eventos
    assert "cargar" in session.audio.eventos


def test_runtime_history_command_reports_entries():
    game = crear_partida(GameConfig(dimensions=(4, 4), seed=34))
    session = SesionJuego(game)
    session.ejecutar("estado")

    output = session.ejecutar("historial")

    assert "estado" in output


def test_runtime_session_adapts_grenade_command_to_legacy_dispatcher():
    game = crear_partida(GameConfig(dimensions=(5, 5), seed=4))
    grenade = make_item("granada", "granada_test")
    assert grenade.item_type is ItemType.EXPLOSIVE
    game.player.add_item(grenade)
    session = SesionJuego(game, audio=AudioNulo())

    output = session.ejecutar("granada este")

    assert "Lanzas" in output
    assert session.historial[-1].normalizado == "lanzar este"
    assert "combate" in session.audio.eventos
