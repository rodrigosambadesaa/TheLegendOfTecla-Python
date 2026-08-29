"""Replay determinista con validación SHA-256.

El replay guarda configuración inicial, comandos ejecutados y hash final del
estado serializado. Es útil para regresiones, para documentar partidas probadas
y para aproximar el sistema de replay versionado del proyecto Java.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .game import GameConfig, create_game
from .model import Difficulty, VictoryCondition


@dataclass(slots=True)
class Replay:
    version: int
    config: dict
    commands: list[str]
    initial_sha256: str
    final_sha256: str
    outputs: list[str]


@dataclass(slots=True)
class ReplayReport:
    replay: Replay
    ok: bool
    final_sha256: str
    outputs: list[str]


def game_digest(game) -> str:
    payload = json.dumps(game.to_save_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def config_to_dict(config: GameConfig) -> dict:
    data = asdict(config)
    data["difficulty"] = config.difficulty.value[0]
    data["victory_condition"] = config.victory_condition.value
    data["data_dir"] = str(config.data_dir) if config.data_dir else None
    return data


def config_from_dict(data: dict) -> GameConfig:
    raw = dict(data)
    raw["difficulty"] = Difficulty.parse(raw.get("difficulty"))
    raw["victory_condition"] = VictoryCondition.parse(raw.get("victory_condition"))
    if raw.get("data_dir"):
        raw["data_dir"] = Path(raw["data_dir"])
    return GameConfig(**raw)


def record_replay(config: GameConfig, commands: Iterable[str]) -> Replay:
    game = create_game(config)
    initial = game_digest(game)
    outputs: list[str] = []
    command_list = [command.strip() for command in commands if command.strip()]
    for command in command_list:
        outputs.append(game.execute(command))
    final = game_digest(game)
    return Replay(1, config_to_dict(config), command_list, initial, final, outputs)


def replay_commands(replay: Replay) -> ReplayReport:
    if replay.version != 1:
        raise ValueError(f"versión de replay no soportada: {replay.version}")
    config = config_from_dict(replay.config)
    game = create_game(config)
    if game_digest(game) != replay.initial_sha256:
        return ReplayReport(replay, False, game_digest(game), [])
    outputs: list[str] = []
    for command in replay.commands:
        outputs.append(game.execute(command))
    final = game_digest(game)
    return ReplayReport(replay, final == replay.final_sha256, final, outputs)


def save_replay(replay: Replay, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(replay), ensure_ascii=False, indent=2), encoding="utf-8")


def load_replay(path: Path) -> Replay:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"replay corrupto: {exc}") from exc
    return Replay(
        int(data.get("version", 0)),
        dict(data.get("config", {})),
        list(data.get("commands", [])),
        str(data.get("initial_sha256", "")),
        str(data.get("final_sha256", "")),
        list(data.get("outputs", [])),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grabador y validador de replays de The Legend of Tecla")
    sub = parser.add_subparsers(dest="action", required=True)

    rec = sub.add_parser("grabar", help="Graba un replay ejecutando comandos")
    rec.add_argument("archivo", type=Path)
    rec.add_argument("comandos", nargs="+", help="Comandos entrecomillados, por ejemplo 'mover este'")

    val = sub.add_parser("validar", help="Valida un replay existente")
    val.add_argument("archivo", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.action == "grabar":
        replay = record_replay(GameConfig(seed=1), args.comandos)
        save_replay(replay, args.archivo)
        print(f"Replay guardado en {args.archivo}")
        print(f"SHA-256 final: {replay.final_sha256}")
        return 0
    replay = load_replay(args.archivo)
    report = replay_commands(replay)
    print("Replay válido." if report.ok else "Replay NO válido.")
    print(f"SHA-256 final observado: {report.final_sha256}")
    return 0 if report.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
