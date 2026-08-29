"""Mapa, celdas, elementos interactivos y serialización del mundo."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .model import Item, ItemType, Position


class InteractiveType(Enum):
    NONE = "ninguno"
    DOOR = "puerta"
    TERMINAL = "terminal"
    SWITCH = "interruptor"
    BARRICADE = "barricada"
    TRAP = "trampa"
    COVER = "cobertura"


class InteractiveState(Enum):
    OPEN = "ABIERTA"
    CLOSED = "CERRADA"
    LOCKED = "BLOQUEADA"
    ACTIVE = "ACTIVO"
    INACTIVE = "INACTIVO"
    ARMED = "ARMADA"
    DISARMED = "DESARMADA"
    DESTROYED = "DESTRUIDA"


@dataclass(slots=True)
class InteractiveElement:
    kind: InteractiveType = InteractiveType.NONE
    element_id: str = ""
    state: InteractiveState = InteractiveState.INACTIVE
    reference: str = ""
    resistance: int = 0
    difficulty: int = 0

    @property
    def blocks_movement(self) -> bool:
        return self.kind in {InteractiveType.DOOR, InteractiveType.BARRICADE} and self.state in {
            InteractiveState.CLOSED,
            InteractiveState.LOCKED,
            InteractiveState.ACTIVE,
        }

    @property
    def dangerous(self) -> bool:
        return self.kind is InteractiveType.TRAP and self.state is InteractiveState.ARMED


@dataclass(slots=True)
class Cell:
    walkable: bool = True
    dark: bool = False
    wood: bool = False
    wall_torch: bool = False
    water_source: bool = False
    fire: int = 0
    items: list[Item] = field(default_factory=list)
    element: InteractiveElement = field(default_factory=InteractiveElement)

    def symbol(self, inspected: bool, illuminated: bool) -> str:
        if not inspected and self.dark and not illuminated:
            return "?"
        if not self.walkable:
            return "#"
        if self.fire > 0:
            return "F"
        if self.element.kind is InteractiveType.DOOR:
            return "/" if self.element.state is InteractiveState.OPEN else "+"
        if self.element.kind is InteractiveType.TRAP and self.element.state is InteractiveState.ARMED:
            return "^" if inspected else "."
        if self.water_source:
            return "U"
        if self.wall_torch:
            return "T"
        if self.wood:
            return "="
        if self.items:
            return "o"
        return "."


@dataclass(slots=True)
class MapGrid:
    rows: int
    cols: int
    start: Position = Position(0, 0)
    goal: Position | None = None
    cells: list[list[Cell]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.cells:
            self.cells = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        if self.goal is None:
            self.goal = Position(self.rows - 1, self.cols - 1)
        self.validate_position(self.start)
        self.validate_position(self.goal)

    def validate_position(self, pos: Position) -> None:
        if not self.inside(pos):
            raise ValueError(f"posicion fuera del mapa: {pos.row},{pos.col}")

    def inside(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def cell(self, pos: Position) -> Cell:
        self.validate_position(pos)
        return self.cells[pos.row][pos.col]

    def is_walkable(self, pos: Position) -> bool:
        if not self.inside(pos):
            return False
        cell = self.cell(pos)
        return cell.walkable and not cell.element.blocks_movement

    def neighbors(self, pos: Position) -> Iterable[Position]:
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            candidate = Position(pos.row + delta_row, pos.col + delta_col)
            if self.is_walkable(candidate):
                yield candidate

    def reachable_positions(self, origin: Position | None = None) -> set[Position]:
        origin = origin or self.start
        if not self.is_walkable(origin):
            return set()
        frontier = [origin]
        visited = {origin}
        while frontier:
            current = frontier.pop()
            for neighbor in self.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    frontier.append(neighbor)
        return visited

    def shortest_path(self, start: Position, end: Position) -> list[Position]:
        if start == end:
            return [start]
        frontier = [start]
        previous: dict[Position, Position | None] = {start: None}
        for current in frontier:
            for neighbor in self.neighbors(current):
                if neighbor in previous:
                    continue
                previous[neighbor] = current
                if neighbor == end:
                    path = [end]
                    while path[-1] != start:
                        parent = previous[path[-1]]
                        assert parent is not None
                        path.append(parent)
                    return list(reversed(path))
                frontier.append(neighbor)
        return []

    def place_item(self, pos: Position, item: Item) -> None:
        self.cell(pos).items.append(item)

    def take_items(self, pos: Position) -> list[Item]:
        items = self.cell(pos).items
        self.cell(pos).items = []
        return items

    def render_ascii(
        self,
        player: Position,
        enemies: Iterable[Position] = (),
        allies: Iterable[Position] = (),
        inspected: set[Position] | None = None,
        illuminated: set[Position] | None = None,
    ) -> str:
        inspected = inspected or set()
        illuminated = illuminated or set()
        enemy_positions = set(enemies)
        ally_positions = set(allies)
        lines: list[str] = []
        for row in range(self.rows):
            chars: list[str] = []
            for col in range(self.cols):
                pos = Position(row, col)
                if pos == player:
                    chars.append("J")
                elif pos in ally_positions:
                    chars.append("A")
                elif pos in enemy_positions:
                    chars.append("E")
                elif pos == self.goal:
                    chars.append("X")
                else:
                    chars.append(self.cell(pos).symbol(pos in inspected, pos in illuminated))
            lines.append("".join(chars))
        return "\n".join(lines)

    def tick_environment(self) -> list[str]:
        messages: list[str] = []
        new_fires: set[Position] = set()
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                pos = Position(r, c)
                if cell.fire > 0:
                    cell.fire -= 1
                    if cell.wood and cell.fire > 0:
                        for neighbor in self.neighbors(pos):
                            neighbor_cell = self.cell(neighbor)
                            if neighbor_cell.wood and neighbor_cell.fire == 0:
                                new_fires.add(neighbor)
                    if cell.fire == 0:
                        messages.append(f"El fuego se apaga en {r},{c}.")
        for pos in new_fires:
            self.cell(pos).fire = 3
            messages.append(f"El fuego se propaga a {pos.row},{pos.col}.")
        return messages

    def to_dict(self) -> dict:
        return {
            "filas": self.rows,
            "columnas": self.cols,
            "inicio": {"fila": self.start.row, "columna": self.start.col},
            "objetivo": {"fila": self.goal.row, "columna": self.goal.col},
            "celdas": [
                {
                    "fila": r,
                    "columna": c,
                    "transitable": cell.walkable,
                    "oscura": cell.dark,
                    "sueloMadera": cell.wood,
                    "antorchaMural": cell.wall_torch,
                    "fuenteAgua": cell.water_source,
                    "fuego": cell.fire,
                    "elementoTipo": cell.element.kind.value,
                    "elementoId": cell.element.element_id,
                    "elementoEstado": cell.element.state.value,
                    "referencia": cell.element.reference,
                    "resistencia": cell.element.resistance,
                    "dificultad": cell.element.difficulty,
                    "objetos": [item_to_dict(item) for item in cell.items],
                }
                for r, row in enumerate(self.cells)
                for c, cell in enumerate(row)
                if not cell.walkable
                or cell.dark
                or cell.wood
                or cell.wall_torch
                or cell.water_source
                or cell.fire
                or cell.items
                or cell.element.kind is not InteractiveType.NONE
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MapGrid":
        rows = int(data.get("filas") or data.get("rows") or 6)
        cols = int(data.get("columnas") or data.get("cols") or 6)
        start_data = data.get("inicio") or {"fila": 0, "columna": 0}
        goal_data = data.get("objetivo") or {"fila": rows - 1, "columna": cols - 1}
        grid = cls(rows, cols, Position(int(start_data["fila"]), int(start_data["columna"])), Position(int(goal_data["fila"]), int(goal_data["columna"])))
        for raw in data.get("celdas", []):
            pos = Position(int(raw.get("fila", 0)), int(raw.get("columna", 0)))
            cell = grid.cell(pos)
            cell.walkable = bool(raw.get("transitable", cell.walkable))
            cell.dark = bool(raw.get("oscura", raw.get("dark", cell.dark)))
            cell.wood = bool(raw.get("sueloMadera", raw.get("wood", cell.wood)))
            cell.wall_torch = bool(raw.get("antorchaMural", raw.get("torch", cell.wall_torch)))
            cell.water_source = bool(raw.get("fuenteAgua", raw.get("water", cell.water_source)))
            cell.fire = int(raw.get("fuego", raw.get("fire", 0)))
            kind = InteractiveType(raw.get("elementoTipo", InteractiveType.NONE.value))
            state = InteractiveState(raw.get("elementoEstado", InteractiveState.INACTIVE.value))
            cell.element = InteractiveElement(
                kind,
                raw.get("elementoId", ""),
                state,
                raw.get("referencia", ""),
                int(raw.get("resistencia", 0)),
                int(raw.get("dificultad", 0)),
            )
            cell.items = [item_from_dict(item) for item in raw.get("objetos", [])]
        return grid


def item_to_dict(item: Item) -> dict:
    return {
        "nombre": item.name,
        "tipo": item.item_type.value,
        "peso": item.weight,
        "valor": item.value,
        "alcance": item.range,
        "municionTipo": item.ammo_type,
        "cargador": item.magazine_size,
        "municionCargada": item.ammo_loaded,
        "penetracion": item.penetration,
        "reutilizable": item.reusable,
        "etiquetas": sorted(item.tags),
    }


def item_from_dict(data: dict) -> Item:
    return Item(
        name=str(data.get("nombre") or data.get("name") or "objeto"),
        item_type=ItemType(data.get("tipo") or data.get("type") or "botiquin"),
        weight=int(data.get("peso") or data.get("weight") or 1),
        value=int(data.get("valor") or data.get("value") or 0),
        range=int(data.get("alcance") or data.get("range") or 1),
        ammo_type=data.get("municionTipo") or data.get("ammo_type"),
        magazine_size=int(data.get("cargador") or data.get("magazine_size") or 0),
        ammo_loaded=int(data.get("municionCargada") or data.get("ammo_loaded") or 0),
        penetration=int(data.get("penetracion") or data.get("penetration") or 0),
        reusable=bool(data.get("reutilizable") or data.get("reusable") or False),
        tags=set(data.get("etiquetas") or data.get("tags") or []),
    )
