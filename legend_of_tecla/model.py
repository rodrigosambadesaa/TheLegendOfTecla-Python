"""Modelo de dominio de The Legend of Tecla.

La reimplementación Python mantiene una separación deliberada entre dominio,
mundo, motor y entrada/salida para que el proyecto siga siendo fácil de probar y
ampliar, como el original Java.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Direction(Enum):
    NORTH = (-1, 0, "norte", "n")
    SOUTH = (1, 0, "sur", "s")
    EAST = (0, 1, "este", "e")
    WEST = (0, -1, "oeste", "o")

    @property
    def dr(self) -> int:
        return self.value[0]

    @property
    def dc(self) -> int:
        return self.value[1]

    @classmethod
    def parse(cls, raw: str) -> "Direction":
        normalized = raw.strip().lower()
        aliases = {
            "arriba": cls.NORTH,
            "up": cls.NORTH,
            "abajo": cls.SOUTH,
            "down": cls.SOUTH,
            "derecha": cls.EAST,
            "right": cls.EAST,
            "izquierda": cls.WEST,
            "left": cls.WEST,
        }
        for direction in cls:
            if normalized in direction.value[2:]:
                return direction
        if normalized in aliases:
            return aliases[normalized]
        raise ValueError(f"direccion no reconocida: {raw}")


class Difficulty(Enum):
    VERY_EASY = ("muy facil", 0.50)
    EASY = ("facil", 0.75)
    NORMAL = ("normal", 1.00)
    HARD = ("dificil", 1.25)
    VERY_HARD = ("muy dificil", 1.50)
    NIGHTMARE = ("pesadilla", 1.80)
    INSANE = ("demente", 2.20)

    @property
    def enemy_ratio(self) -> float:
        return self.value[1]

    @classmethod
    def parse(cls, raw: str | None) -> "Difficulty":
        if not raw:
            return cls.NORMAL
        normalized = raw.strip().lower().replace("á", "a").replace("í", "i")
        aliases = {
            "muyfacil": cls.VERY_EASY,
            "muy facil": cls.VERY_EASY,
            "very_easy": cls.VERY_EASY,
            "facil": cls.EASY,
            "easy": cls.EASY,
            "normal": cls.NORMAL,
            "dificil": cls.HARD,
            "hard": cls.HARD,
            "muydificil": cls.VERY_HARD,
            "muy dificil": cls.VERY_HARD,
            "very_hard": cls.VERY_HARD,
            "pesadilla": cls.NIGHTMARE,
            "nightmare": cls.NIGHTMARE,
            "demente": cls.INSANE,
            "insane": cls.INSANE,
        }
        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(f"dificultad no reconocida: {raw}") from exc


class VictoryCondition(Enum):
    PLAYER_ONLY = "solo_jugador"
    PLAYER_AND_ALLIES = "jugador_y_aliados"

    @classmethod
    def parse(cls, raw: str | None) -> "VictoryCondition":
        if not raw:
            return cls.PLAYER_AND_ALLIES
        normalized = raw.strip().lower()
        if normalized in {"1", "solo", "solo_jugador", "jugador"}:
            return cls.PLAYER_ONLY
        if normalized in {"2", "todos", "jugador_y_aliados", "aliados"}:
            return cls.PLAYER_AND_ALLIES
        raise ValueError(f"condicion de victoria no reconocida: {raw}")


@dataclass(frozen=True, order=True)
class Position:
    row: int
    col: int

    def moved(self, direction: Direction, steps: int = 1) -> "Position":
        return Position(self.row + direction.dr * steps, self.col + direction.dc * steps)

    def distance_to(self, other: "Position") -> int:
        return abs(self.row - other.row) + abs(self.col - other.col)

    def line_to(self, direction: Direction, max_steps: int) -> Iterable["Position"]:
        for step in range(1, max_steps + 1):
            yield self.moved(direction, step)


class ItemType(Enum):
    MEDKIT = "botiquin"
    ENERGY = "torito"
    TORITO_RED = "torito_rojo"
    WEAPON = "arma"
    ARMOR = "armadura"
    AMMO = "municion"
    LANTERN = "linterna"
    WATER_BUCKET = "cuboagua"
    EXPLOSIVE = "explosivo"
    CREDENTIAL = "credencial"
    COMPONENT = "componente"


@dataclass(slots=True)
class Item:
    name: str
    item_type: ItemType
    weight: int = 1
    value: int = 0
    range: int = 1
    ammo_type: str | None = None
    magazine_size: int = 0
    ammo_loaded: int = 0
    penetration: int = 0
    reusable: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def is_weapon(self) -> bool:
        return self.item_type is ItemType.WEAPON

    @property
    def is_armor(self) -> bool:
        return self.item_type is ItemType.ARMOR

    @property
    def is_consumable(self) -> bool:
        return self.item_type in {ItemType.MEDKIT, ItemType.ENERGY, ItemType.TORITO_RED, ItemType.AMMO, ItemType.EXPLOSIVE}

    def clone(self, name: str | None = None) -> "Item":
        return Item(
            name=name or self.name,
            item_type=self.item_type,
            weight=self.weight,
            value=self.value,
            range=self.range,
            ammo_type=self.ammo_type,
            magazine_size=self.magazine_size,
            ammo_loaded=self.ammo_loaded,
            penetration=self.penetration,
            reusable=self.reusable,
            tags=set(self.tags),
        )


class CharacterState(Enum):
    NORMAL = "normal"
    BURNING = "ardiendo"
    WET = "mojado"
    RESTING = "descansando"
    POISONED = "envenenado"
    STUNNED = "aturdido"
    INSPIRED = "inspirado"
    BLEEDING = "sangrando"
    HIDDEN = "oculto"


@dataclass(slots=True)
class TemporaryEffect:
    state: CharacterState
    remaining_turns: int
    power: int = 1

    def tick(self) -> bool:
        self.remaining_turns -= 1
        return self.remaining_turns > 0


@dataclass(slots=True)
class Character:
    name: str
    position: Position
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    vision: int = 4
    capacity: int = 20
    level: int = 1
    inventory: list[Item] = field(default_factory=list)
    weapon: Item | None = None
    armor: Item | None = None
    effects: list[TemporaryEffect] = field(default_factory=list)
    evacuated: bool = False
    alive: bool = True

    @property
    def load(self) -> int:
        return sum(item.weight for item in self.inventory)

    @property
    def attack_damage(self) -> int:
        base = 2 + self.level // 8
        if self.weapon:
            base += self.weapon.value
        return base

    @property
    def attack_range(self) -> int:
        return self.weapon.range if self.weapon else 1

    @property
    def defense(self) -> int:
        return self.armor.value if self.armor else 0

    def can_carry(self, item: Item) -> bool:
        return self.load + item.weight <= self.capacity

    def add_item(self, item: Item) -> None:
        if not self.can_carry(item):
            raise ValueError(f"{self.name} no puede cargar {item.name}: capacidad superada")
        self.inventory.append(item)

    def remove_item(self, name: str) -> Item:
        normalized = name.strip().lower()
        for index, item in enumerate(self.inventory):
            if item.name.lower() == normalized:
                return self.inventory.pop(index)
        raise ValueError(f"{self.name} no tiene {name}")

    def find_item(self, name: str) -> Item | None:
        normalized = name.strip().lower()
        return next((item for item in self.inventory if item.name.lower() == normalized), None)

    def equip(self, item_name: str) -> str:
        item = self.remove_item(item_name)
        if item.is_weapon:
            if self.weapon:
                self.inventory.append(self.weapon)
            self.weapon = item
            return f"{self.name} equipa {item.name}."
        if item.is_armor:
            if self.armor:
                self.inventory.append(self.armor)
            self.armor = item
            return f"{self.name} equipa {item.name}."
        self.inventory.append(item)
        raise ValueError(f"{item.name} no se puede equipar")

    def unequip(self, what: str) -> str:
        normalized = what.strip().lower()
        if normalized in {"arma", "weapon", self.weapon.name.lower() if self.weapon else ""} and self.weapon:
            item = self.weapon
            self.weapon = None
            self.add_item(item)
            return f"{self.name} desequipa {item.name}."
        if normalized in {"armadura", "armor", self.armor.name.lower() if self.armor else ""} and self.armor:
            item = self.armor
            self.armor = None
            self.add_item(item)
            return f"{self.name} desequipa {item.name}."
        raise ValueError(f"{self.name} no lleva equipado {what}")

    def receive_damage(self, raw_damage: int, penetration: int = 0) -> int:
        effective_defense = max(0, self.defense - penetration)
        damage = max(1, raw_damage - effective_defense)
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.alive = False
        return damage

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def recover_energy(self, amount: int) -> int:
        before = self.energy
        self.energy = min(self.max_energy, self.energy + amount)
        return self.energy - before

    def spend_energy(self, amount: int) -> None:
        if self.energy < amount:
            raise ValueError(f"{self.name} no tiene energia suficiente")
        self.energy -= amount

    def apply_effect(self, state: CharacterState, turns: int, power: int = 1) -> None:
        existing = next((effect for effect in self.effects if effect.state is state), None)
        if existing:
            existing.remaining_turns = max(existing.remaining_turns, turns)
            existing.power += power
        else:
            self.effects.append(TemporaryEffect(state, turns, power))

    def tick_effects(self) -> list[str]:
        messages: list[str] = []
        active: list[TemporaryEffect] = []
        for effect in self.effects:
            if effect.state is CharacterState.BURNING:
                damage = self.receive_damage(effect.power)
                messages.append(f"{self.name} sufre {damage} por fuego.")
            elif effect.state is CharacterState.BLEEDING:
                damage = self.receive_damage(1)
                messages.append(f"{self.name} pierde {damage} por sangrado.")
            if effect.tick():
                active.append(effect)
        self.effects = active
        return messages


@dataclass(slots=True)
class Player(Character):
    character_class: str = "marine"
    experience: int = 0
    skills: set[str] = field(default_factory=set)

    def add_xp(self, amount: int) -> None:
        self.experience += amount
        while self.experience >= self.level * 100 and self.level < 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_hp += 2
            self.max_energy += 2
            self.hp = self.max_hp
            self.energy = self.max_energy


@dataclass(slots=True)
class Ally(Character):
    role: str = "combatiente"
    inspected: set[Position] = field(default_factory=set)
    score: int = 0

    @property
    def medic(self) -> bool:
        return self.role == "medico"


class AlertState(Enum):
    IDLE = "ocioso"
    SUSPICIOUS = "sospecha"
    SEARCHING = "buscando"
    ALERTED = "alertado"
    ENGAGING = "combatiendo"
    PROTECTING = "protegiendo"
    RETREATING = "retirada"
    BOSS_PHASE = "fase_jefe"


@dataclass(slots=True)
class Enemy(Character):
    archetype: str = "sectoid"
    role: str = "soldado"
    alert: AlertState = AlertState.IDLE
    memory: Position | None = None
    boss_phase: int = 1


@dataclass(slots=True)
class Statistics:
    turns: int = 0
    damage_done: int = 0
    damage_taken: int = 0
    enemies_killed: int = 0
    allies_lost: int = 0
    items_collected: int = 0
    crafted_items: int = 0
    traps_disarmed: int = 0
    fires_extinguished: int = 0


@dataclass(slots=True)
class Achievement:
    code: str
    title: str
    description: str
    unlocked: bool = False
