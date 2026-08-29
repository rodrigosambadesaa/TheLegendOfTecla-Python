"""Motor de juego de The Legend of Tecla en Python."""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from .catalog import BASIC_ITEMS, RECIPES, LootCycle, make_item
from .model import (
    Achievement,
    AlertState,
    Ally,
    Character,
    CharacterState,
    Difficulty,
    Direction,
    Enemy,
    Item,
    ItemType,
    Player,
    Position,
    Statistics,
    VictoryCondition,
)
from .world import InteractiveState, InteractiveType, MapGrid, item_from_dict, item_to_dict


@dataclass(slots=True)
class Event:
    turn: int
    topic: str
    message: str


@dataclass(slots=True)
class EventBus:
    events: list[Event] = field(default_factory=list)

    def publish(self, turn: int, topic: str, message: str) -> None:
        self.events.append(Event(turn, topic, message))

    def drain_text(self, limit: int = 30) -> str:
        return "\n".join(f"[{event.turn:04d}] {event.topic}: {event.message}" for event in self.events[-limit:])


@dataclass(slots=True)
class Mission:
    code: str
    title: str
    description: str
    completed: bool = False


@dataclass(slots=True)
class Campaign:
    index: int = 0
    xp: int = 0
    missions: list[Mission] = field(default_factory=lambda: [
        Mission("evacuar", "Evacuación", "Alcanza la casilla objetivo."),
        Mission("limpiar", "Zona segura", "Elimina todos los enemigos visibles."),
        Mission("rescate", "Nadie queda atrás", "Evacua con todos los aliados vivos."),
    ])


@dataclass(slots=True)
class GameConfig:
    player_name: str = "Tecla"
    player_class: str = "marine"
    mode: str = "default"
    difficulty: Difficulty = Difficulty.NORMAL
    dimensions: tuple[int, int] | None = None
    data_dir: Path | None = None
    allies: int = 0
    victory_condition: VictoryCondition = VictoryCondition.PLAYER_AND_ALLIES
    variant: int = 1
    seed: int | None = None
    player_level: int = 1
    ally_level: int = 0
    ally_upgrades: bool = True
    ally_ammo: bool = True


@dataclass(slots=True)
class Game:
    grid: MapGrid
    player: Player
    enemies: list[Enemy]
    allies: list[Ally] = field(default_factory=list)
    difficulty: Difficulty = Difficulty.NORMAL
    victory_condition: VictoryCondition = VictoryCondition.PLAYER_AND_ALLIES
    inspected: set[Position] = field(default_factory=set)
    illuminated: set[Position] = field(default_factory=set)
    statistics: Statistics = field(default_factory=Statistics)
    achievements: dict[str, Achievement] = field(default_factory=dict)
    bus: EventBus = field(default_factory=EventBus)
    campaign: Campaign = field(default_factory=Campaign)
    finished: bool = False
    victory: bool = False
    spectator: bool = False
    rng_seed: int | None = None

    def __post_init__(self) -> None:
        self.inspected.add(self.player.position)
        if not self.achievements:
            self.achievements = default_achievements()

    def living_enemies(self) -> list[Enemy]:
        return [enemy for enemy in self.enemies if enemy.alive]

    def living_allies(self) -> list[Ally]:
        return [ally for ally in self.allies if ally.alive and not ally.evacuated]

    def character_at(self, pos: Position) -> Character | None:
        if self.player.alive and not self.player.evacuated and self.player.position == pos:
            return self.player
        for character in [*self.allies, *self.enemies]:
            if character.alive and not character.evacuated and character.position == pos:
                return character
        return None

    def enemies_visible(self) -> list[Enemy]:
        humans: list[Character] = [self.player, *self.living_allies()]
        return [enemy for enemy in self.living_enemies() if any(actor.position.distance_to(enemy.position) <= actor.vision for actor in humans)]

    def allies_visible(self) -> list[Ally]:
        return [ally for ally in self.living_allies() if ally.position.distance_to(self.player.position) <= self.player.vision + 2]

    def status(self) -> str:
        weapon = self.player.weapon.name if self.player.weapon else "puños"
        armor = self.player.armor.name if self.player.armor else "sin armadura"
        effects = ",".join(effect.state.value for effect in self.player.effects) or "sin estados"
        return (
            f"{self.player.name} L{self.player.level} {self.player.character_class} | "
            f"vida {self.player.hp}/{self.player.max_hp} | energia {self.player.energy}/{self.player.max_energy} | "
            f"arma {weapon} | armadura {armor} | carga {self.player.load}/{self.player.capacity} | {effects}"
        )

    def allies_status(self) -> str:
        if not self.allies:
            return "Sin aliados."
        lines = []
        for ally in self.allies[:40]:
            state = "evacuado" if ally.evacuated else "vivo" if ally.alive else "muerto"
            lines.append(
                f"{ally.name}({ally.role}) {state} pos={ally.position.row},{ally.position.col} "
                f"vida={ally.hp}/{ally.max_hp} energia={ally.energy}/{ally.max_energy} score={ally.score}"
            )
        if len(self.allies) > 40:
            lines.append(f"... {len(self.allies) - 40} aliados omitidos en vista resumida")
        return "\n".join(lines)

    def render(self) -> str:
        return self.grid.render_ascii(
            self.player.position,
            [enemy.position for enemy in self.enemies_visible()],
            [ally.position for ally in self.allies_visible()],
            self.inspected,
            self.illuminated,
        )

    def execute(self, command: str) -> str:
        if self.finished:
            return self._spectator_tick(command)
        try:
            result = CommandDispatcher(self).execute(command)
        except Exception as exc:  # noqa: BLE001
            return f"Error: {exc}"
        self.after_player_action()
        return result + self._outcome_suffix()

    def after_player_action(self) -> None:
        if self.finished:
            return
        self.statistics.turns += 1
        self._apply_environment_to_characters()
        self._allies_turn()
        self._enemies_turn()
        for message in self.grid.tick_environment():
            self.bus.publish(self.statistics.turns, "ambiente", message)
        self._tick_effects()
        self._check_victory()
        self._unlock_achievements()

    def _apply_environment_to_characters(self) -> None:
        for character in [self.player, *self.living_allies(), *self.living_enemies()]:
            cell = self.grid.cell(character.position)
            if cell.fire:
                damage = character.receive_damage(3)
                self.bus.publish(self.statistics.turns, "fuego", f"{character.name} recibe {damage} por fuego ambiental.")
            if cell.element.dangerous and character is self.player:
                damage = character.receive_damage(max(3, cell.element.resistance // 5 or 5))
                cell.element.state = InteractiveState.DISARMED
                self.bus.publish(self.statistics.turns, "trampa", f"{character.name} activa una trampa y pierde {damage} vida.")

    def _tick_effects(self) -> None:
        for character in [self.player, *self.living_allies(), *self.living_enemies()]:
            for message in character.tick_effects():
                self.bus.publish(self.statistics.turns, "estado", message)

    def _allies_turn(self) -> None:
        for ally in self.living_allies():
            if ally.position == self.grid.goal:
                ally.evacuated = True
                ally.score += 500
                self.bus.publish(self.statistics.turns, "aliado", f"{ally.name} evacua.")
                continue
            target_enemy = nearest(ally.position, self.living_enemies())
            if target_enemy and ally.position.distance_to(target_enemy.position) <= ally.attack_range:
                self._attack(ally, target_enemy)
                continue
            if ally.medic:
                patient = min([self.player, *self.living_allies()], key=lambda c: c.hp / max(1, c.max_hp))
                if patient.hp < patient.max_hp * 0.55 and ally.find_item("botiquin"):
                    item = ally.remove_item("botiquin")
                    healed = patient.heal(item.value or 20)
                    ally.score += healed
                    self.bus.publish(self.statistics.turns, "medico", f"{ally.name} cura {healed} a {patient.name}.")
                    continue
            destination = self.grid.goal if self.victory_condition is VictoryCondition.PLAYER_AND_ALLIES else self.player.position
            if target_enemy and ally.position.distance_to(self.player.position) <= 4:
                destination = target_enemy.position
            self._step_towards(ally, destination)
            ally.inspected.add(ally.position)
            ally.score += max(0, 10 - ally.position.distance_to(self.grid.goal))

    def _enemies_turn(self) -> None:
        humans: list[Character] = [self.player, *self.living_allies()]
        humans = [human for human in humans if human.alive and not human.evacuated]
        for enemy in self.living_enemies():
            if not humans:
                break
            target = choose_enemy_target(enemy, humans, squad_mode=bool(self.allies))
            distance = enemy.position.distance_to(target.position)
            if distance > enemy.vision + 2 and enemy.memory is None:
                continue
            if distance <= enemy.attack_range:
                self._attack(enemy, target)
                enemy.alert = AlertState.ENGAGING
                enemy.memory = target.position
            else:
                if enemy.memory is None or distance <= enemy.vision + 2:
                    enemy.memory = target.position
                    enemy.alert = AlertState.SEARCHING
                self._step_towards(enemy, enemy.memory)

    def _step_towards(self, character: Character, destination: Position) -> bool:
        path = self.grid.shortest_path(character.position, destination)
        if len(path) < 2:
            return False
        next_pos = path[1]
        if self.character_at(next_pos) is None or next_pos == destination:
            if self.grid.is_walkable(next_pos):
                character.position = next_pos
                character.energy = max(0, character.energy - 1)
                return True
        return False

    def _attack(self, attacker: Character, target: Character) -> int:
        if attacker.weapon and attacker.weapon.ammo_type and attacker.weapon.magazine_size > 0:
            if attacker.weapon.ammo_loaded <= 0:
                self.bus.publish(self.statistics.turns, "combate", f"{attacker.name} intenta disparar, pero {attacker.weapon.name} está descargada.")
                return 0
            attacker.weapon.ammo_loaded -= 1
        damage = target.receive_damage(attacker.attack_damage, attacker.weapon.penetration if attacker.weapon else 0)
        if attacker in [self.player, *self.allies]:
            self.statistics.damage_done += damage
        else:
            self.statistics.damage_taken += damage
        self.bus.publish(self.statistics.turns, "combate", f"{attacker.name} ataca a {target.name}: -{damage} vida, queda {target.hp}/{target.max_hp}.")
        if not target.alive:
            self.bus.publish(self.statistics.turns, "muerte", f"{target.name} muere.")
            if isinstance(target, Enemy):
                self.statistics.enemies_killed += 1
                self.player.add_xp(50)
                if target.weapon and "xeno" not in target.weapon.tags:
                    self.grid.place_item(target.position, target.weapon)
            elif isinstance(target, Ally):
                self.statistics.allies_lost += 1
        return damage

    def _check_victory(self) -> None:
        if not self.player.alive:
            if self.living_allies():
                self.spectator = True
                self.bus.publish(self.statistics.turns, "modo", "Jugador muerto: modo espectador disponible con turbo.")
            else:
                self.finished = True
                self.victory = False
            return
        if self.player.position == self.grid.goal:
            self.player.evacuated = True
        if self.victory_condition is VictoryCondition.PLAYER_ONLY:
            self.finished = self.player.evacuated
            self.victory = self.finished
        else:
            all_evacuated = self.player.evacuated and all((not ally.alive) or ally.evacuated for ally in self.allies)
            if all_evacuated:
                self.finished = True
                self.victory = True
        if not self.living_enemies() and self.player.alive:
            self.campaign.missions[1].completed = True

    def _unlock_achievements(self) -> None:
        checks = {
            "primer_paso": self.statistics.turns >= 1,
            "primer_botin": self.statistics.items_collected >= 1,
            "primer_eliminado": self.statistics.enemies_killed >= 1,
            "sin_bajas": self.victory and self.statistics.allies_lost == 0,
            "artesano": self.statistics.crafted_items >= 1,
        }
        for code, unlocked in checks.items():
            achievement = self.achievements.get(code)
            if achievement and unlocked and not achievement.unlocked:
                achievement.unlocked = True
                self.bus.publish(self.statistics.turns, "logro", f"Logro desbloqueado: {achievement.title}")

    def _outcome_suffix(self) -> str:
        if self.finished:
            return "\nVICTORIA HUMANA" if self.victory else "\nVICTORIA ENEMIGA"
        if self.spectator:
            return "\nModo espectador: usa 'turbo' para avanzar turnos."
        return ""

    def _spectator_tick(self, command: str) -> str:
        if command.strip().lower() != "turbo":
            return self._outcome_suffix()
        for _ in range(20):
            if self.finished:
                break
            self.statistics.turns += 1
            self._allies_turn()
            self._enemies_turn()
            self._check_victory()
        return self._outcome_suffix()

    def to_save_dict(self) -> dict:
        return {
            "version": 1,
            "rngSeed": self.rng_seed,
            "turnos": self.statistics.turns,
            "mapa": self.grid.to_dict(),
            "jugador": character_to_dict(self.player),
            "aliados": [character_to_dict(ally) | {"rol": ally.role, "score": ally.score} for ally in self.allies],
            "enemigos": [character_to_dict(enemy) | {"arquetipo": enemy.archetype, "rol": enemy.role, "alerta": enemy.alert.value} for enemy in self.enemies],
            "estadisticas": asdict(self.statistics),
            "logros": {code: achievement.unlocked for code, achievement in self.achievements.items()},
            "celdasInspeccionadas": [{"fila": pos.row, "columna": pos.col} for pos in sorted(self.inspected)],
        }

    @classmethod
    def from_save_dict(cls, data: dict) -> "Game":
        if data.get("version") != 1:
            raise ValueError("savegame de version desconocida")
        grid = MapGrid.from_dict(data["mapa"])
        player = player_from_dict(data["jugador"])
        allies = [ally_from_dict(raw) for raw in data.get("aliados", [])]
        enemies = [enemy_from_dict(raw) for raw in data.get("enemigos", [])]
        game = cls(grid, player, enemies, allies, rng_seed=data.get("rngSeed"))
        stats = data.get("estadisticas", {})
        game.statistics = Statistics(**{name: stats.get(name, 0) for name in asdict(Statistics())})
        for code, unlocked in data.get("logros", {}).items():
            if code in game.achievements:
                game.achievements[code].unlocked = bool(unlocked)
        game.inspected = {Position(int(raw["fila"]), int(raw["columna"])) for raw in data.get("celdasInspeccionadas", [])}
        return game


class CommandDispatcher:
    def __init__(self, game: Game) -> None:
        self.game = game

    def execute(self, command: str) -> str:
        parts = command.strip().split()
        if not parts:
            return "Sin acción."
        verb = parts[0].lower()
        aliases = {"m": "mover", "move": "mover", "coger": "recoger", "tomar": "recoger", "drop": "tirar", "use": "usar", "attack": "atacar", "equip": "equipar", "unequip": "desequipar", "help": "ayuda", "inventario": "estado", "mirar": "inspeccionar"}
        verb = aliases.get(verb, verb)
        handler = getattr(self, f"cmd_{verb}", None)
        if handler is None:
            raise ValueError(f"comando no reconocido: {verb}. Prueba 'ayuda'.")
        return handler(parts[1:])

    def cmd_ayuda(self, _: list[str]) -> str:
        return "Comandos: mover, recoger, tirar, usar, equipar, desequipar, atacar, descansar, lanzar, pedir ayuda, reagrupar, recargar, dar, pedir, intercambiar, abrir, cerrar, hackear, activar, inspeccionar, desactivar, recetas, fabricar, guardar, cargar, estadisticas, logros, estado."

    def cmd_estado(self, _: list[str]) -> str:
        inv = ", ".join(item.name for item in self.game.player.inventory) or "vacío"
        return f"{self.game.status()}\nInventario: {inv}\n{self.game.allies_status()}"

    def cmd_mover(self, parts: list[str]) -> str:
        if not parts:
            raise ValueError("uso: mover <direccion> [pasos]")
        direction = Direction.parse(parts[0])
        steps = int(parts[1]) if len(parts) > 1 else 1
        moved = 0
        for _ in range(max(1, steps)):
            target = self.game.player.position.moved(direction)
            if not self.game.grid.is_walkable(target) or self.game.character_at(target) is not None:
                break
            self.game.player.spend_energy(1)
            self.game.player.position = target
            self.game.inspected.add(target)
            moved += 1
            if target == self.game.grid.goal:
                break
        return f"Te mueves {moved} paso(s) hacia {direction.value[2]}." if moved else "No puedes avanzar por ahí."

    def cmd_recoger(self, _: list[str]) -> str:
        items = self.game.grid.take_items(self.game.player.position)
        if not items:
            return "No hay objetos en esta celda."
        picked: list[str] = []
        for item in items:
            if self.game.player.can_carry(item):
                self.game.player.add_item(item)
                self.game.statistics.items_collected += 1
                picked.append(item.name)
            else:
                self.game.grid.place_item(self.game.player.position, item)
        return "Recoges: " + ", ".join(picked) if picked else "No puedes cargar nada más."

    def cmd_tirar(self, parts: list[str]) -> str:
        item = self.game.player.remove_item(" ".join(parts))
        self.game.grid.place_item(self.game.player.position, item)
        return f"Tiras {item.name}."

    def cmd_usar(self, parts: list[str]) -> str:
        item = self.game.player.remove_item(" ".join(parts))
        if item.item_type is ItemType.MEDKIT:
            return f"Usas {item.name} y recuperas {self.game.player.heal(item.value or 20)} vida."
        if item.item_type in {ItemType.ENERGY, ItemType.TORITO_RED}:
            return f"Bebes {item.name} y recuperas {self.game.player.recover_energy(item.value or 20)} energía."
        if item.item_type is ItemType.LANTERN:
            self.game.illuminated.update(positions_in_radius(self.game.grid, self.game.player.position, item.value or 4))
            if item.reusable:
                self.game.player.inventory.append(item)
            return f"Iluminas el entorno con {item.name}."
        if item.item_type is ItemType.WATER_BUCKET:
            cell = self.game.grid.cell(self.game.player.position)
            if cell.fire:
                cell.fire = 0
                self.game.statistics.fires_extinguished += 1
                return "Apagas el fuego de la celda."
            if cell.water_source:
                item.value = 1
                self.game.player.inventory.append(item)
                return "Rellenas el cubo de agua."
        self.game.player.inventory.append(item)
        raise ValueError(f"no sabes usar {item.name}")

    def cmd_equipar(self, parts: list[str]) -> str:
        return self.game.player.equip(" ".join(parts))

    def cmd_desequipar(self, parts: list[str]) -> str:
        return self.game.player.unequip(" ".join(parts))

    def cmd_atacar(self, parts: list[str]) -> str:
        target = self._target_from_argument(parts[0]) if parts else nearest(self.game.player.position, self.game.enemies_visible())
        if target is None:
            return "No hay enemigo válido al alcance."
        times = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 1
        messages = []
        for _ in range(max(1, times)):
            if not target.alive:
                break
            if self.game.player.position.distance_to(target.position) > self.game.player.attack_range:
                messages.append(f"{target.name} está fuera de alcance.")
                break
            damage = self.game._attack(self.game.player, target)
            messages.append(f"Golpeas a {target.name} por {damage}.")
        return " ".join(messages)

    def _target_from_argument(self, arg: str) -> Enemy | None:
        try:
            direction = Direction.parse(arg)
            for pos in self.game.player.position.line_to(direction, self.game.player.attack_range):
                enemy = next((enemy for enemy in self.game.living_enemies() if enemy.position == pos), None)
                if enemy:
                    return enemy
        except ValueError:
            pass
        normalized = arg.lower()
        return next((enemy for enemy in self.game.living_enemies() if enemy.name.lower() == normalized), None)

    def cmd_descansar(self, _: list[str]) -> str:
        hp = self.game.player.heal(5)
        energy = self.game.player.recover_energy(8)
        self.game.player.apply_effect(CharacterState.RESTING, 1)
        for enemy in self.game.living_enemies():
            enemy.memory = self.game.player.position
            enemy.alert = AlertState.ALERTED
        return f"Descansas: +{hp} vida, +{energy} energía. El ruido atrae enemigos."

    def cmd_lanzar(self, parts: list[str]) -> str:
        direction = Direction.parse(parts[0])
        explosive = next((item for item in self.game.player.inventory if item.item_type is ItemType.EXPLOSIVE), None)
        if explosive is None:
            raise ValueError("no tienes explosivos")
        self.game.player.inventory.remove(explosive)
        impact = self.game.player.position
        for pos in self.game.player.position.line_to(direction, explosive.range or 4):
            if not self.game.grid.inside(pos) or not self.game.grid.is_walkable(pos):
                break
            impact = pos
        self.game.grid.cell(impact).fire = 3
        damaged = []
        for enemy in self.game.living_enemies():
            if enemy.position.distance_to(impact) <= 1:
                damaged.append(f"{enemy.name} -{enemy.receive_damage(explosive.value or 18, penetration=4)}")
        return f"Lanzas {explosive.name} a {impact.row},{impact.col}. " + ", ".join(damaged)

    def cmd_pedir(self, parts: list[str]) -> str:
        if parts and parts[0].lower() == "ayuda":
            return self.cmd_ayuda_aliada([])
        item = self._ally(parts[1]).remove_item(parts[0])
        self.game.player.add_item(item)
        return f"{parts[1]} entrega {item.name}."

    def cmd_ayuda_aliada(self, _: list[str]) -> str:
        for ally in self.game.living_allies():
            if ally.position.distance_to(self.game.player.position) > 1:
                self.game._step_towards(ally, self.game.player.position)
        return "Pides ayuda: los aliados se acercan o exploran suministros antes de acudir."

    def cmd_reagrupar(self, parts: list[str]) -> str:
        formation = parts[0].lower() if parts else "defensiva"
        offsets = [Position(0, -1), Position(0, 1), Position(-1, 0), Position(1, 0)]
        for index, ally in enumerate(self.game.living_allies()):
            offset = offsets[index % len(offsets)]
            target = Position(self.game.player.position.row + offset.row, self.game.player.position.col + offset.col)
            if self.game.grid.is_walkable(target) and self.game.character_at(target) is None:
                ally.position = target
        return f"Formación {formation} aplicada."

    def cmd_recargar(self, parts: list[str]) -> str:
        weapon = self.game.player.weapon
        if not weapon or not weapon.ammo_type or weapon.magazine_size <= 0:
            return "No hay arma recargable."
        needed = weapon.magazine_size - weapon.ammo_loaded
        if needed <= 0:
            return f"{weapon.name} ya está cargada."
        ammo = next((item for item in self.game.player.inventory if item.item_type is ItemType.AMMO and item.ammo_type == weapon.ammo_type), None)
        if not ammo:
            return f"No tienes munición {weapon.ammo_type}."
        loaded = min(needed, ammo.value)
        weapon.ammo_loaded += loaded
        ammo.value -= loaded
        if ammo.value <= 0:
            self.game.player.inventory.remove(ammo)
        return f"Recargas {weapon.name}: +{loaded} ({weapon.ammo_loaded}/{weapon.magazine_size})."

    def cmd_dar(self, parts: list[str]) -> str:
        item = self.game.player.remove_item(parts[0])
        ally = self._ally(parts[1])
        ally.add_item(item)
        return f"Das {item.name} a {ally.name}."

    def cmd_intercambiar(self, parts: list[str]) -> str:
        player_item = self.game.player.remove_item(parts[0])
        ally = self._ally(parts[2])
        ally_item = ally.remove_item(parts[1])
        ally.add_item(player_item)
        self.game.player.add_item(ally_item)
        return f"Intercambio completado con {ally.name}."

    def _ally(self, name: str) -> Ally:
        ally = next((ally for ally in self.game.allies if ally.name.lower() == name.lower()), None)
        if not ally:
            raise ValueError(f"aliado no encontrado: {name}")
        return ally

    def cmd_abrir(self, _: list[str]) -> str:
        element = self._adjacent_element(InteractiveType.DOOR)
        if element.state is InteractiveState.LOCKED and not any(element.reference in item.tags or item.name == element.reference for item in self.game.player.inventory):
            return "La puerta está bloqueada y no tienes credencial."
        element.state = InteractiveState.OPEN
        return "Puerta abierta."

    def cmd_cerrar(self, _: list[str]) -> str:
        self._adjacent_element(InteractiveType.DOOR).state = InteractiveState.CLOSED
        return "Puerta cerrada."

    def cmd_hackear(self, _: list[str]) -> str:
        element = self._adjacent_element(InteractiveType.TERMINAL)
        skill = self.game.player.level + (5 if self.game.player.character_class == "zapador" else 0)
        if skill >= element.difficulty:
            element.state = InteractiveState.ACTIVE
            return "Terminal hackeado."
        return "Hackeo fallido."

    def cmd_activar(self, _: list[str]) -> str:
        element = self._adjacent_element(InteractiveType.SWITCH)
        element.state = InteractiveState.ACTIVE if element.state is not InteractiveState.ACTIVE else InteractiveState.INACTIVE
        return f"Interruptor ahora {element.state.value}."

    def cmd_inspeccionar(self, parts: list[str]) -> str:
        radius = 1 if parts and parts[0].lower() == "trampa" else self.game.player.vision
        self.game.inspected.update(positions_in_radius(self.game.grid, self.game.player.position, radius))
        return "Inspeccionas trampas cercanas." if radius == 1 else "Inspeccionas el entorno."

    def cmd_desactivar(self, _: list[str]) -> str:
        element = self._adjacent_element(InteractiveType.TRAP)
        skill = self.game.player.level + (8 if self.game.player.character_class == "zapador" else 0)
        if skill >= element.difficulty:
            element.state = InteractiveState.DISARMED
            self.game.statistics.traps_disarmed += 1
            return "Trampa desactivada."
        damage = self.game.player.receive_damage(4)
        element.state = InteractiveState.DISARMED
        return f"La trampa se dispara durante la desactivación: -{damage} vida."

    def _adjacent_element(self, kind: InteractiveType):
        for pos in positions_in_radius(self.game.grid, self.game.player.position, 1):
            element = self.game.grid.cell(pos).element
            if element.kind is kind:
                return element
        raise ValueError(f"no hay {kind.value} adyacente")

    def cmd_recetas(self, _: list[str]) -> str:
        return "\n".join(f"{recipe.result}: {' + '.join(recipe.ingredients)}" for recipe in RECIPES)

    def cmd_fabricar(self, parts: list[str]) -> str:
        result = parts[0].lower()
        recipe = next((recipe for recipe in RECIPES if recipe.result == result), None)
        if not recipe:
            raise ValueError(f"receta desconocida: {result}")
        removed: list[Item] = []
        try:
            for ingredient in recipe.ingredients:
                removed.append(self.game.player.remove_item(ingredient))
            self.game.player.add_item(recipe.item.clone())
            self.game.statistics.crafted_items += 1
            return f"Fabricas {recipe.item.name}."
        except Exception:
            self.game.player.inventory.extend(removed)
            raise

    def cmd_guardar(self, parts: list[str]) -> str:
        target = Path(parts[0]) if parts else Path("savegame_tecla.json")
        save_game(self.game, target)
        return f"Partida guardada en {target}."

    def cmd_cargar(self, parts: list[str]) -> str:
        target = Path(parts[0]) if parts else Path("savegame_tecla.json")
        loaded = load_game(target)
        for name in Game.__dataclass_fields__:
            setattr(self.game, name, getattr(loaded, name))
        return f"Partida cargada desde {target}."

    def cmd_estadisticas(self, _: list[str]) -> str:
        return "\n".join(f"{key}: {value}" for key, value in asdict(self.game.statistics).items())

    def cmd_logros(self, _: list[str]) -> str:
        return "\n".join(f"[{'x' if achievement.unlocked else ' '}] {achievement.title}: {achievement.description}" for achievement in self.game.achievements.values())


def positions_in_radius(grid: MapGrid, center: Position, radius: int) -> set[Position]:
    result: set[Position] = set()
    for row in range(center.row - radius, center.row + radius + 1):
        for col in range(center.col - radius, center.col + radius + 1):
            pos = Position(row, col)
            if grid.inside(pos) and center.distance_to(pos) <= radius:
                result.add(pos)
    return result


def nearest(origin: Position, characters: Iterable[Character]) -> Character | None:
    candidates = [character for character in characters if character.alive and not character.evacuated]
    return min(candidates, key=lambda character: origin.distance_to(character.position), default=None)


def choose_enemy_target(enemy: Enemy, humans: list[Character], squad_mode: bool) -> Character:
    if not squad_mode:
        return min(humans, key=lambda human: enemy.position.distance_to(human.position))
    medics = [human for human in humans if isinstance(human, Ally) and human.medic]
    vulnerable = min(humans, key=lambda human: (human.hp / max(1, human.max_hp), enemy.position.distance_to(human.position)))
    if medics and enemy.role in {"sanitario", "mando", "explorador"}:
        return min(medics, key=lambda human: enemy.position.distance_to(human.position))
    return vulnerable


def default_achievements() -> dict[str, Achievement]:
    return {
        "primer_paso": Achievement("primer_paso", "Primer paso", "Ejecuta el primer turno."),
        "primer_botin": Achievement("primer_botin", "Botín localizado", "Recoge un objeto."),
        "primer_eliminado": Achievement("primer_eliminado", "Contacto neutralizado", "Elimina un enemigo."),
        "sin_bajas": Achievement("sin_bajas", "Nadie queda atrás", "Gana sin bajas aliadas."),
        "artesano": Achievement("artesano", "Artesano", "Fabrica un objeto."),
    }


def make_character_stats(level: int, base_hp: int, base_energy: int) -> tuple[int, int, int, int]:
    level = max(1, min(100, level))
    hp = base_hp + level * 2
    energy = base_energy + level * 2
    vision = 4 + level // 25
    capacity = 20 + level // 5
    return hp, energy, vision, capacity


def create_game(config: GameConfig) -> Game:
    rng = random.Random(config.seed if config.seed is not None else config.variant)
    grid = create_grid(config, rng)
    hp, energy, vision, capacity = make_character_stats(config.player_level, 28, 25)
    player = Player(config.player_name, grid.start, hp, hp, energy, energy, vision, capacity, config.player_level, character_class=config.player_class)
    player.add_item(make_item("botiquin", "botiquin_inicial"))
    player.add_item(make_item("torito", "torito_inicial"))
    player.weapon = make_item("rifle_asalto" if config.player_class == "marine" else "rifle_precision" if config.player_class == "francotirador" else "escopeta")
    player.armor = make_item("chaleco_ligero")
    enemies = create_enemies(grid, config, rng)
    allies = create_allies(grid, config, rng)
    distribute_supplies(grid, config, rng, len(allies), len(enemies))
    return Game(grid, player, enemies, allies, config.difficulty, config.victory_condition, rng_seed=config.seed)


def create_grid(config: GameConfig, rng: random.Random) -> MapGrid:
    mode = config.mode.lower()
    if mode == "ficheros" and config.data_dir:
        return load_scenario(config.data_dir)
    if mode == "grande":
        return large_grid(config.variant, config.dimensions or (50, 50), rng)
    if mode == "procedural":
        return procedural_grid(config.dimensions or (18, 28), rng)
    rows, cols = config.dimensions or (6, 6)
    grid = MapGrid(rows, cols, Position(0, 0), Position(rows - 1, cols - 1))
    if rows > 3 and cols > 3:
        grid.cell(Position(2, 2)).dark = True
        grid.cell(Position(2, 2)).wood = True
        grid.cell(Position(2, 2)).wall_torch = True
        grid.cell(Position(3, 1)).water_source = True
        grid.cell(Position(1, 3)).element.kind = InteractiveType.TRAP
        grid.cell(Position(1, 3)).element.state = InteractiveState.ARMED
        grid.cell(Position(1, 3)).element.difficulty = 4
        if cols > 4:
            grid.cell(Position(0, min(4, cols - 1))).element.kind = InteractiveType.DOOR
            grid.cell(Position(0, min(4, cols - 1))).element.state = InteractiveState.CLOSED
    return grid


def large_grid(variant: int, dimensions: tuple[int, int], rng: random.Random) -> MapGrid:
    rows, cols = dimensions
    grid = MapGrid(rows, cols, Position(0, 0), Position(rows - 1, cols - 1))
    local = random.Random(variant)
    for r in range(rows):
        for c in range(cols):
            pos = Position(r, c)
            if pos in {grid.start, grid.goal}:
                continue
            if local.random() < 0.08:
                grid.cell(pos).walkable = False
            elif local.random() < 0.06:
                grid.cell(pos).dark = True
            elif local.random() < 0.04:
                grid.cell(pos).wood = True
    r = c = 0
    grid.cell(Position(r, c)).walkable = True
    while (r, c) != (rows - 1, cols - 1):
        if r < rows - 1:
            r += 1
        if c < cols - 1:
            c += 1
        grid.cell(Position(r, c)).walkable = True
    return grid


def procedural_grid(dimensions: tuple[int, int], rng: random.Random) -> MapGrid:
    rows, cols = dimensions
    grid = MapGrid(rows, cols, Position(0, 0), Position(rows - 1, cols - 1))
    for r in range(rows):
        for c in range(cols):
            pos = Position(r, c)
            if pos in {grid.start, grid.goal}:
                continue
            roll = rng.random()
            if roll < 0.10:
                grid.cell(pos).walkable = False
            elif roll < 0.16:
                grid.cell(pos).dark = True
            elif roll < 0.21:
                grid.cell(pos).wood = True
            elif roll < 0.23:
                grid.cell(pos).water_source = True
    for pos in grid.shortest_path(grid.start, grid.goal) or []:
        grid.cell(pos).walkable = True
    return grid


def load_scenario(directory: Path) -> MapGrid:
    json_path = directory / "escenario.json"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return MapGrid.from_dict(data.get("mapa", data))
    map_path = directory / "mapa.txt"
    if not map_path.exists():
        raise ValueError(f"no existe escenario en {directory}")
    lines = [line.strip() for line in map_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    rows, cols = (int(part) for part in lines[0].lower().split("x", 1))
    start = Position(*(int(part) for part in lines[1].split(",", 1)))
    goal = Position(*(int(part) for part in lines[2].split(",", 1)))
    grid = MapGrid(rows, cols, start, goal)
    for line in lines[3:]:
        kind, row, col = line.split(";")[:3]
        cell = grid.cell(Position(int(row), int(col)))
        if kind == "oscura":
            cell.dark = True
        elif kind == "madera":
            cell.wood = True
        elif kind == "antorcha":
            cell.wall_torch = True
        elif kind == "fuente":
            cell.water_source = True
    obj_path = directory / "objetos.txt"
    if obj_path.exists():
        for line in obj_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, kind, row, col, *rest = line.split(";")
            value = int(rest[0]) if rest and rest[0].isdigit() else None
            grid.place_item(Position(int(row), int(col)), make_item(kind, name, value))
    return grid


def create_enemies(grid: MapGrid, config: GameConfig, rng: random.Random) -> list[Enemy]:
    reachable = [pos for pos in grid.reachable_positions() if pos.distance_to(grid.start) > max(3, min(grid.rows, grid.cols) // 8)]
    base = max(1, int((len(reachable) ** 0.5) * config.difficulty.enemy_ratio / 2))
    allies_count = config.allies if config.allies > 0 else max(0, base // 2 if config.allies == -1 else 0)
    count = min(5000, max(base, int(max(1, allies_count + 1) * config.difficulty.enemy_ratio)))
    if allies_count:
        count = min(count, allies_count + 1)
    rng.shuffle(reachable)
    archetypes = ["sectoid", "floater", "heavyfloater", "muton", "cyberdisc", "jefe_psi"]
    roles = ["soldado", "sanitario", "explorador", "mando", "protector", "francotirador"]
    enemies: list[Enemy] = []
    for idx, pos in enumerate(reachable[:count]):
        hp = 18 + idx % 12
        enemy = Enemy(f"alien_{idx + 1}", pos, hp, hp, 18, 18, 4, 20, 1 + idx // 20, archetype=archetypes[idx % len(archetypes)], role=roles[idx % len(roles)])
        weapon_kind = "fusil_xeno" if idx % 4 else "sable_xeno"
        enemy.weapon = make_item(weapon_kind, f"{weapon_kind}_{idx + 1}")
        enemy.armor = make_item("coraza_xeno", f"coraza_xeno_{idx + 1}")
        enemies.append(enemy)
    return enemies


def create_allies(grid: MapGrid, config: GameConfig, rng: random.Random) -> list[Ally]:
    if config.allies == 0:
        return []
    reachable = [pos for pos in grid.reachable_positions() if pos != grid.start and pos.distance_to(grid.start) <= 3]
    count = config.allies if config.allies > 0 else max(1, min(8, len(grid.reachable_positions()) // 20))
    count = min(4999, count)
    level = config.ally_level or max(1, config.player_level)
    allies: list[Ally] = []
    for idx in range(count):
        hp, energy, vision, capacity = make_character_stats(level, 22, 22)
        pos = reachable[idx % len(reachable)] if reachable else grid.start
        role = "medico" if idx % 4 == 0 else "combatiente"
        ally = Ally(f"aliado_{idx + 1}", pos, hp, hp, energy, energy, vision, capacity, level, role=role)
        ally.weapon = make_item("pistola_9mm", f"pistola_aliado_{idx + 1}")
        if role == "medico":
            ally.add_item(make_item("botiquin", f"botiquin_medico_{idx + 1}"))
            ally.add_item(make_item("torito_rojo", f"torito_rojo_medico_{idx + 1}"))
        allies.append(ally)
    return allies


def distribute_supplies(grid: MapGrid, config: GameConfig, rng: random.Random, allies: int, enemies: int) -> None:
    reachable = list(grid.reachable_positions())
    rng.shuffle(reachable)
    loot = LootCycle()
    supply_count = max(4, min(len(reachable), 4 + allies // 2 + enemies // 3))
    for idx, pos in enumerate(reachable[:supply_count]):
        if idx % 5 == 0:
            grid.place_item(pos, loot.next_weapon())
        else:
            template = BASIC_ITEMS[idx % len(BASIC_ITEMS)]
            grid.place_item(pos, template.clone(f"{template.name}_{idx}"))


def character_to_dict(character: Character) -> dict:
    return {
        "nombre": character.name,
        "fila": character.position.row,
        "columna": character.position.col,
        "vida": character.hp,
        "vidaMaxima": character.max_hp,
        "energia": character.energy,
        "energiaMaxima": character.max_energy,
        "vision": character.vision,
        "capacidad": character.capacity,
        "nivel": character.level,
        "inventario": [item_to_dict(item) for item in character.inventory],
        "arma": item_to_dict(character.weapon) if character.weapon else None,
        "armadura": item_to_dict(character.armor) if character.armor else None,
        "vivo": character.alive,
        "evacuado": character.evacuated,
    }


def hydrate_character(raw: dict, cls: type[Character]) -> Character:
    character = cls(
        raw["nombre"],
        Position(int(raw["fila"]), int(raw["columna"])),
        int(raw["vida"]),
        int(raw["vidaMaxima"]),
        int(raw["energia"]),
        int(raw["energiaMaxima"]),
        int(raw.get("vision", 4)),
        int(raw.get("capacidad", 20)),
        int(raw.get("nivel", 1)),
    )
    character.inventory = [item_from_dict(item) for item in raw.get("inventario", [])]
    character.weapon = item_from_dict(raw["arma"]) if raw.get("arma") else None
    character.armor = item_from_dict(raw["armadura"]) if raw.get("armadura") else None
    character.alive = bool(raw.get("vivo", True))
    character.evacuated = bool(raw.get("evacuado", False))
    return character


def player_from_dict(raw: dict) -> Player:
    player = hydrate_character(raw, Player)
    assert isinstance(player, Player)
    player.character_class = raw.get("clase", raw.get("character_class", "marine"))
    return player


def ally_from_dict(raw: dict) -> Ally:
    ally = hydrate_character(raw, Ally)
    assert isinstance(ally, Ally)
    ally.role = raw.get("rol", raw.get("role", "combatiente"))
    ally.score = int(raw.get("score", 0))
    return ally


def enemy_from_dict(raw: dict) -> Enemy:
    enemy = hydrate_character(raw, Enemy)
    assert isinstance(enemy, Enemy)
    enemy.archetype = raw.get("arquetipo", "sectoid")
    enemy.role = raw.get("rol", "soldado")
    enemy.alert = AlertState(raw.get("alerta", AlertState.IDLE.value))
    return enemy


def save_game(game: Game, path: Path) -> None:
    path.write_text(json.dumps(game.to_save_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_game(path: Path) -> Game:
    try:
        return Game.from_save_dict(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise ValueError("savegame JSON corrupto") from exc
