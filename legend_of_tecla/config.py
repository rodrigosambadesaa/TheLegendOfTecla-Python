"""Configuracion externa del juego.

Equivalente Pythonico al paquete Java ``config``. Permite cargar preferencias
desde JSON o INI sin acoplar el motor a argumentos de consola.
"""
from __future__ import annotations

import configparser
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .constants import DEFAULTS
from .model import Difficulty, VictoryCondition
from .validation import entero_entre, texto_obligatorio


@dataclass(frozen=True, slots=True)
class ConfiguracionJuego:
    jugador_nombre: str = DEFAULTS.jugador_nombre
    jugador_clase: str = DEFAULTS.jugador_clase
    dificultad: Difficulty = Difficulty.NORMAL
    condicion_victoria: VictoryCondition = VictoryCondition.PLAYER_AND_ALLIES
    filas: int = DEFAULTS.filas
    columnas: int = DEFAULTS.columnas
    aliados: int = 0
    semilla: int | None = None
    datos: str | None = None
    audio: bool = False
    modo_gui: bool = False

    def __post_init__(self) -> None:
        texto_obligatorio(self.jugador_nombre, "Nombre del jugador")
        texto_obligatorio(self.jugador_clase, "Clase del jugador")
        entero_entre(self.filas, 2, 200, "Filas")
        entero_entre(self.columnas, 2, 200, "Columnas")
        entero_entre(self.aliados, 0, 20, "Aliados")

    @property
    def dimensiones(self) -> tuple[int, int]:
        return self.filas, self.columnas

    def actualizado(self, **cambios: Any) -> "ConfiguracionJuego":
        return replace(self, **cambios)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dificultad"] = self.dificultad.value[0]
        data["condicion_victoria"] = self.condicion_victoria.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfiguracionJuego":
        return cls(
            jugador_nombre=str(data.get("jugador_nombre", DEFAULTS.jugador_nombre)),
            jugador_clase=str(data.get("jugador_clase", DEFAULTS.jugador_clase)),
            dificultad=Difficulty.parse(data.get("dificultad")),
            condicion_victoria=VictoryCondition.parse(data.get("condicion_victoria")),
            filas=int(data.get("filas", DEFAULTS.filas)),
            columnas=int(data.get("columnas", DEFAULTS.columnas)),
            aliados=int(data.get("aliados", 0)),
            semilla=None if data.get("semilla") in {None, ""} else int(data["semilla"]),
            datos=None if not data.get("datos") else str(data["datos"]),
            audio=bool(data.get("audio", False)),
            modo_gui=bool(data.get("modo_gui", False)),
        )


def cargar_configuracion(path: str | Path) -> ConfiguracionJuego:
    ruta = Path(path)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la configuracion: {ruta}")
    if ruta.suffix.lower() == ".json":
        return ConfiguracionJuego.from_dict(json.loads(ruta.read_text(encoding="utf-8")))
    parser = configparser.ConfigParser()
    parser.read(ruta, encoding="utf-8")
    seccion = parser["juego"] if parser.has_section("juego") else parser.defaults()
    return ConfiguracionJuego.from_dict(dict(seccion))


def guardar_configuracion(config: ConfiguracionJuego, path: str | Path) -> None:
    ruta = Path(path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.suffix.lower() == ".json":
        ruta.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return
    parser = configparser.ConfigParser()
    parser["juego"] = {k: "" if v is None else str(v) for k, v in config.to_dict().items()}
    with ruta.open("w", encoding="utf-8") as handle:
        parser.write(handle)
