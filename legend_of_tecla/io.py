"""Carga y exportacion de escenarios.

Soporta el formato academico clasico ``mapa.txt``/``objetos.txt``/``enemigos.txt``
y el formato JSON ampliado usado por el editor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import make_item
from .model import Item, Position
from .world import MapGrid


@dataclass(slots=True)
class DefinicionEnemigo:
    tipo: str
    posicion: Position
    nombre: str = ""


@dataclass(slots=True)
class DefinicionEscenario:
    mapa: MapGrid
    objetos: list[tuple[Position, Item]] = field(default_factory=list)
    enemigos: list[DefinicionEnemigo] = field(default_factory=list)


def cargar_mapa_txt(path: str | Path) -> MapGrid:
    ruta = Path(path)
    lineas = [line.rstrip("\n") for line in ruta.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lineas:
        raise ValueError("El mapa no puede estar vacio")
    filas = len(lineas)
    columnas = max(len(linea) for linea in lineas)
    grid = MapGrid(filas, columnas)
    for r, linea in enumerate(lineas):
        for c in range(columnas):
            char = linea[c] if c < len(linea) else "#"
            pos = Position(r, c)
            cell = grid.cell(pos)
            if char == "#":
                cell.walkable = False
            elif char in {"J", "S"}:
                grid.start = pos
            elif char in {"X", "G"}:
                grid.goal = pos
            elif char == "F":
                cell.fire = 3
            elif char == "?":
                cell.dark = True
            elif char == "=":
                cell.wood = True
    return grid


def cargar_objetos_txt(path: str | Path) -> list[tuple[Position, Item]]:
    ruta = Path(path)
    if not ruta.exists():
        return []
    objetos: list[tuple[Position, Item]] = []
    for raw in ruta.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        partes = [parte.strip() for parte in line.replace(";", ",").split(",")]
        if len(partes) < 3:
            continue
        fila, columna, nombre = int(partes[0]), int(partes[1]), partes[2]
        objetos.append((Position(fila, columna), make_item(nombre)))
    return objetos


def cargar_enemigos_txt(path: str | Path) -> list[DefinicionEnemigo]:
    ruta = Path(path)
    if not ruta.exists():
        return []
    enemigos: list[DefinicionEnemigo] = []
    for raw in ruta.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        partes = [parte.strip() for parte in line.replace(";", ",").split(",")]
        if len(partes) < 3:
            continue
        fila, columna, tipo = int(partes[0]), int(partes[1]), partes[2]
        nombre = partes[3] if len(partes) > 3 else tipo
        enemigos.append(DefinicionEnemigo(tipo, Position(fila, columna), nombre))
    return enemigos


def cargar_escenario(path: str | Path) -> DefinicionEscenario:
    ruta = Path(path)
    if ruta.is_file() and ruta.suffix.lower() == ".json":
        data = json.loads(ruta.read_text(encoding="utf-8"))
        grid = MapGrid.from_dict(data)
        return DefinicionEscenario(grid)
    mapa = cargar_mapa_txt(ruta / "mapa.txt")
    objetos = cargar_objetos_txt(ruta / "objetos.txt")
    for pos, item in objetos:
        if mapa.inside(pos):
            mapa.place_item(pos, item)
    enemigos = cargar_enemigos_txt(ruta / "enemigos.txt")
    return DefinicionEscenario(mapa, objetos, enemigos)


def exportar_escenario_json(escenario: DefinicionEscenario, path: str | Path) -> None:
    ruta = Path(path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    data = escenario.mapa.to_dict()
    data["enemigos"] = [
        {"tipo": e.tipo, "fila": e.posicion.row, "columna": e.posicion.col, "nombre": e.nombre}
        for e in escenario.enemigos
    ]
    ruta.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
