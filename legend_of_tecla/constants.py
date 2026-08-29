"""Constantes compartidas del dominio.

Este modulo recupera la idea del paquete Java ``constants``: no contiene logica
de juego, solo nombres canonicos, simbolos y valores por defecto usados por el
modelo, los parsers y la UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SimboloMapa(str, Enum):
    PARED = "#"
    SUELO = "."
    JUGADOR = "J"
    ENEMIGO = "E"
    ALIADO = "A"
    OBJETO = "o"
    SALIDA = "X"
    FUEGO = "F"
    PUERTA_CERRADA = "+"
    PUERTA_ABIERTA = "/"
    TRAMPA = "^"
    DESCONOCIDO = "?"


class NombreComando(str, Enum):
    MOVER = "mover"
    ATACAR = "atacar"
    RECOGER = "recoger"
    USAR = "usar"
    EQUIPAR = "equipar"
    DESEQUIPAR = "desequipar"
    INSPECCIONAR = "inspeccionar"
    ESTADO = "estado"
    AYUDA = "ayuda"
    GUARDAR = "guardar"
    CARGAR = "cargar"


@dataclass(frozen=True, slots=True)
class ValoresPorDefecto:
    jugador_nombre: str = "Tecla"
    jugador_clase: str = "marine"
    filas: int = 8
    columnas: int = 10
    vision: int = 4
    capacidad_mochila: int = 20
    energia_movimiento: int = 2
    danio_base: int = 2
    version_save: int = 2


DEFAULTS = ValoresPorDefecto()

DIRECCIONES_CANONICAS: dict[str, tuple[int, int]] = {
    "norte": (-1, 0),
    "sur": (1, 0),
    "este": (0, 1),
    "oeste": (0, -1),
}

ALIASES_COMANDOS: dict[str, str] = {
    "n": "mover norte",
    "s": "mover sur",
    "e": "mover este",
    "o": "mover oeste",
    "w": "mover norte",
    "a": "mover oeste",
    "d": "mover este",
    "arriba": "mover norte",
    "abajo": "mover sur",
    "derecha": "mover este",
    "izquierda": "mover oeste",
    "coger": "recoger",
    "pick": "recoger",
    "look": "inspeccionar",
    "i": "inventario",
}
