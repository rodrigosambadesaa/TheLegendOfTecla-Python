"""Interfaz de consola para jugar o validar partidas desde scripts."""
from __future__ import annotations

import argparse
from pathlib import Path

from .game import GameConfig, create_game, load_game
from .model import Difficulty, VictoryCondition


HELP_TEXT = """The Legend of Tecla - Python

Modos:
  default      mapa compacto de ejemplo
  grande       mapa grande con 50 variantes deterministas
  ficheros     carga escenario.json o mapa.txt/objetos.txt/enemigos.txt
  procedural   mapa reproducible con --seed

Durante la partida escribe 'ayuda' para ver los comandos tácticos.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The Legend of Tecla reimplementado en Python", epilog=HELP_TEXT)
    parser.add_argument("--nombre", default="Tecla")
    parser.add_argument("--clase", choices=["marine", "francotirador", "zapador"], default="marine")
    parser.add_argument("--modo", choices=["default", "grande", "ficheros", "procedural"], default="default")
    parser.add_argument("--dificultad", default="normal")
    parser.add_argument("--dimensiones", help="Formato filasxcolumnas, por ejemplo 12x20")
    parser.add_argument("--datos", type=Path, help="Directorio con escenario.json o txt")
    parser.add_argument("--aliados", default="0", help="0/no, auto o cantidad 1-4999")
    parser.add_argument("--victoria", default="jugador_y_aliados")
    parser.add_argument("--variante", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--nivel-jugador", type=int, default=1)
    parser.add_argument("--nivel-aliados", type=int, default=0)
    parser.add_argument("--rapido", action="store_true", help="Ejecuta una partida no interactiva de humo")
    parser.add_argument("--cargar", type=Path, help="Carga un savegame")
    return parser


def parse_dimensions(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    rows, cols = raw.lower().split("x", 1)
    return int(rows), int(cols)


def parse_allies(raw: str) -> int:
    normalized = raw.strip().lower()
    if normalized in {"", "0", "no", "ninguno"}:
        return 0
    if normalized in {"si", "sí", "auto", "automatico", "automático"}:
        return -1
    value = int(normalized)
    if not 1 <= value <= 4999:
        raise ValueError("aliados debe estar entre 1 y 4999")
    return value


def game_from_args(args: argparse.Namespace):
    if args.cargar:
        return load_game(args.cargar)
    config = GameConfig(
        player_name=args.nombre,
        player_class=args.clase,
        mode=args.modo,
        difficulty=Difficulty.parse(args.dificultad),
        dimensions=parse_dimensions(args.dimensiones),
        data_dir=args.datos,
        allies=parse_allies(str(args.aliados)),
        victory_condition=VictoryCondition.parse(args.victoria),
        variant=max(1, min(50, args.variante)),
        seed=args.seed,
        player_level=max(1, min(100, args.nivel_jugador)),
        ally_level=max(0, min(100, args.nivel_aliados)),
    )
    return create_game(config)


def run_quick(game) -> int:
    print(game.render())
    print(game.status())
    print(game.execute("inspeccionar"))
    print(game.execute("estado"))
    return 0


def run_interactive(game) -> int:
    print("Bienvenido a The Legend of Tecla (Python)")
    print("Leyenda: J=jugador E=enemigo A=aliado F=fuego ?=oscuridad T=antorcha U=fuente ==madera o=objeto X=objetivo")
    while not game.finished:
        print()
        print(game.render())
        print(game.status())
        if game.allies:
            print(game.allies_status())
        try:
            command = input("accion> ")
        except EOFError:
            print("Entrada cerrada. Partida finalizada.")
            return 0
        if command.strip().lower() in {"salir", "exit", "quit"}:
            return 0
        print(game.execute(command))
        events = game.bus.drain_text(8)
        if events:
            print(events)
    print("VICTORIA HUMANA" if game.victory else "VICTORIA ENEMIGA")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    game = game_from_args(args)
    if args.rapido:
        return run_quick(game)
    return run_interactive(game)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
