from pathlib import Path

from legend_of_tecla.config import ConfiguracionJuego, guardar_configuracion
from legend_of_tecla.facade import cargar_partida, crear_partida, crear_partida_desde_config, guardar_partida, sincronizar_logros
from legend_of_tecla.game import GameConfig
from legend_of_tecla.model import Position


def _scenario(tmp_path: Path) -> Path:
    scenario = tmp_path / "escenario"
    scenario.mkdir()
    (scenario / "mapa.txt").write_text("J..\n.#X\n", encoding="utf-8")
    (scenario / "objetos.txt").write_text("0,1,botiquin\n", encoding="utf-8")
    (scenario / "enemigos.txt").write_text("1,0,sectoid,Alien\n", encoding="utf-8")
    return scenario


def test_facade_uses_enemy_definitions_from_text_scenario(tmp_path: Path):
    scenario = _scenario(tmp_path)

    game = crear_partida(GameConfig(mode="ficheros", data_dir=scenario, seed=3))

    assert game.grid.start == Position(0, 0)
    assert game.grid.goal == Position(1, 2)
    assert len(game.enemies) == 1
    assert game.enemies[0].name == "Alien"
    assert game.enemies[0].archetype == "sectoid"
    assert game.enemies[0].position == Position(1, 0)


def test_facade_save_load_uses_versioned_persistence(tmp_path: Path):
    game = crear_partida(GameConfig(seed=7, dimensions=(5, 5)))
    game.execute("inspeccionar")
    path = tmp_path / "partida.json"

    guardar_partida(game, path)
    loaded = cargar_partida(path)

    assert loaded.statistics.turns == game.statistics.turns
    assert loaded.player.name == game.player.name
    assert loaded.grid.rows == game.grid.rows


def test_create_game_from_persistent_config(tmp_path: Path):
    scenario = _scenario(tmp_path)
    config_path = tmp_path / "config.json"
    guardar_configuracion(
        ConfiguracionJuego(jugador_nombre="Rodrigo", jugador_clase="zapador", filas=2, columnas=3, datos=str(scenario), semilla=11),
        config_path,
    )

    game = crear_partida_desde_config(config_path)

    assert game.player.name == "Rodrigo"
    assert game.player.character_class == "zapador"
    assert game.enemies[0].name == "Alien"


def test_facade_merges_extended_achievement_registry():
    game = crear_partida(GameConfig(seed=5))
    game.statistics.enemies_killed = 5
    game.statistics.items_collected = 10
    game.statistics.traps_disarmed = 3
    game.statistics.turns = 12

    unlocked = sincronizar_logros(game)

    codes = {achievement.code for achievement in unlocked}
    assert {"primer_enemigo", "limpieza", "coleccionista", "zapador"} <= codes
    assert "primer_paso" in game.achievements
    assert "primer_enemigo" in game.achievements
