"""Fachada de aplicacion que conecta motor y servicios.

Este modulo evita que la CLI y futuras interfaces dependan directamente de
pequenos detalles del motor. Centraliza la integracion de configuracion,
escenarios, persistencia versionada y logros.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import overload

from .achievements import RegistroLogros
from .catalog import make_item
from .config import ConfiguracionJuego
from .game import (
    Game,
    GameConfig,
    create_allies,
    create_enemies,
    create_game,
    distribute_supplies,
    make_character_stats,
)
from .io import DefinicionEnemigo, cargar_escenario
from .model import Achievement, Difficulty, Enemy, Player, VictoryCondition
from .persistence import cargar_save, guardar_save
from .world import MapGrid


def game_config_from_configuracion(config: ConfiguracionJuego) -> GameConfig:
    """Convierte la configuracion persistente en ``GameConfig`` del motor."""

    mode = "ficheros" if config.datos else "default"
    return GameConfig(
        player_name=config.jugador_nombre,
        player_class=config.jugador_clase,
        mode=mode,
        difficulty=config.dificultad,
        dimensions=config.dimensiones,
        data_dir=Path(config.datos) if config.datos else None,
        allies=config.aliados,
        victory_condition=config.condicion_victoria,
        seed=config.semilla,
    )


@overload
def crear_partida(config: GameConfig) -> Game: ...


@overload
def crear_partida(config: ConfiguracionJuego) -> Game: ...


def crear_partida(config: GameConfig | ConfiguracionJuego) -> Game:
    """Crea una partida usando todos los servicios disponibles.

    A diferencia de ``game.create_game``, cuando el modo es ``ficheros`` lee
    tambien ``enemigos.txt`` mediante ``io.cargar_escenario`` y convierte esas
    definiciones en enemigos reales del motor.
    """

    game_config = game_config_from_configuracion(config) if isinstance(config, ConfiguracionJuego) else config
    if game_config.mode.lower() != "ficheros" or not game_config.data_dir:
        game = create_game(game_config)
        sincronizar_logros(game)
        return game

    rng = random.Random(game_config.seed if game_config.seed is not None else game_config.variant)
    escenario = cargar_escenario(game_config.data_dir)
    grid = escenario.mapa
    hp, energy, vision, capacity = make_character_stats(game_config.player_level, 28, 25)
    player = Player(
        game_config.player_name,
        grid.start,
        hp,
        hp,
        energy,
        energy,
        vision,
        capacity,
        game_config.player_level,
        character_class=game_config.player_class,
    )
    _equipar_jugador_inicial(player, game_config.player_class)
    allies = create_allies(grid, game_config, rng)
    enemies = _crear_enemigos_desde_definiciones(escenario.enemigos, game_config, rng) if escenario.enemigos else create_enemies(grid, game_config, rng)
    distribute_supplies(grid, game_config, rng, len(allies), len(enemies))
    game = Game(grid, player, enemies, allies, game_config.difficulty, game_config.victory_condition, rng_seed=game_config.seed)
    sincronizar_logros(game)
    return game


def _equipar_jugador_inicial(player: Player, player_class: str) -> None:
    player.add_item(make_item("botiquin", "botiquin_inicial"))
    player.add_item(make_item("torito", "torito_inicial"))
    player.weapon = make_item(
        "rifle_asalto" if player_class == "marine" else "rifle_precision" if player_class == "francotirador" else "escopeta"
    )
    player.armor = make_item("chaleco_ligero")


def _crear_enemigos_desde_definiciones(
    definiciones: list[DefinicionEnemigo],
    config: GameConfig,
    rng: random.Random,
) -> list[Enemy]:
    enemigos: list[Enemy] = []
    dificultad = config.difficulty.enemy_ratio
    for index, definicion in enumerate(definiciones):
        hp_base, energia_base = _estadisticas_enemigo(definicion.tipo)
        hp = max(1, int(hp_base * dificultad))
        energia = max(1, int(energia_base * dificultad))
        nombre = definicion.nombre or f"{definicion.tipo}_{index + 1}"
        enemy = Enemy(
            nombre,
            definicion.posicion,
            hp,
            hp,
            energia,
            energia,
            4 + index % 2,
            20,
            1 + index // 5,
            archetype=definicion.tipo.lower(),
            role="mando" if "commander" in definicion.tipo.lower() else "soldado",
        )
        weapon_kind = "sable_xeno" if index % 3 == 0 else "fusil_xeno"
        enemy.weapon = make_item(weapon_kind, f"{weapon_kind}_{index + 1}")
        enemy.armor = make_item("coraza_xeno", f"coraza_xeno_{index + 1}")
        enemigos.append(enemy)
    rng.shuffle(enemigos)
    return enemigos


def _estadisticas_enemigo(tipo: str) -> tuple[int, int]:
    normalized = tipo.strip().lower().replace("_", "")
    if normalized in {"heavyfloater", "heavy"}:
        return 34, 22
    if normalized in {"berserker"}:
        return 45, 30
    if normalized in {"commander", "commanderprime"}:
        return 38, 34
    if normalized in {"jefe", "boss", "jefepsi"}:
        return 60, 40
    if normalized in {"floater"}:
        return 26, 26
    return 22, 22


def guardar_partida(game: Game, path: str | Path) -> None:
    """Guarda una partida con envoltorio versionado de persistencia."""

    guardar_save(game.to_save_dict(), path)


def cargar_partida(path: str | Path) -> Game:
    """Carga una partida tanto del formato versionado nuevo como del antiguo."""

    save = cargar_save(path)
    game = Game.from_save_dict(save.payload)
    sincronizar_logros(game)
    return game


def sincronizar_logros(game: Game) -> list[Achievement]:
    """Fusiona logros historicos del motor con el registro ampliado."""

    registro = RegistroLogros()
    for codigo, logro in game.achievements.items():
        registro.logros.setdefault(codigo, logro)
        registro.logros[codigo].unlocked = logro.unlocked
    desbloqueados = registro.evaluar(game.statistics)
    game.achievements = registro.logros
    return desbloqueados


def crear_partida_desde_config(path: str | Path) -> Game:
    from .config import cargar_configuracion

    return crear_partida(cargar_configuracion(path))


__all__ = [
    "cargar_partida",
    "crear_partida",
    "crear_partida_desde_config",
    "game_config_from_configuracion",
    "guardar_partida",
    "sincronizar_logros",
]
