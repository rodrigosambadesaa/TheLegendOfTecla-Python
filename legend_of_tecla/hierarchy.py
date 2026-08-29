"""Jerarquia POO canonica de The Legend of Tecla.

Este modulo existe para que la version Python respete explicitamente la
jerarquia de clases exigida por las practicas P1/P2/P3/P4 y consolidada en la
version Java original. El motor Python conserva sus clases idiomaticas
`Character`, `Player`, `Enemy`, `Ally` e `Item`; aqui se exponen los nombres y
subtipos de dominio equivalentes al enunciado y al codigo Java:

    Personaje
      Jugador
        Marine
        Francotirador
        Zapador
      Enemigo
        Sectoid
        Floater
          HeavyFloater
        Commander
          CommanderPrime
        Berserker
        Jefe

Tambien se modela la familia de objetos como tipos reales, no solo como cadenas:
Objeto, Arma, Armadura, Botiquin, Linterna, Binocular, CuboAgua, Explosivo,
Granada, Municion, Credencial y Componente.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .model import Ally, Character, Enemy, Item, ItemType, Player, Position


# ---------------------------------------------------------------------------
# Personajes: nombres canonicos de la especificacion POO.
# ---------------------------------------------------------------------------
Personaje = Character


class Jugador(Player):
    """Base abstracta de los jugadores historicos.

    En Java es una clase abstracta que extiende `Personaje` y registra el
    recorrido. En Python se representa como subtipo real de `Player`, con el
    mismo campo `character_class` usado por el motor actual.
    """

    clase_canonica: ClassVar[str] = "jugador"

    def registrar_posicion(self) -> None:
        recorrido = getattr(self, "recorrido", [])
        recorrido.append(self.position)
        self.recorrido = recorrido


class Marine(Jugador):
    """Marine: 120 salud, 90 energia; fuerte en combate cercano."""

    clase_canonica: ClassVar[str] = "marine"

    def __init__(self, nombre: str, posicion: Position, nivel: int = 1, vision_base: int = 4) -> None:
        super().__init__(nombre, posicion, 120, 120, 90, 90, vision_base, 24, nivel, character_class="marine")
        self.recorrido = [posicion]

    def modificar_danio(self, base: int, objetivo: Character) -> int:
        distancia = self.position.distance_to(objetivo.position)
        if distancia <= 1:
            return base * 2
        if distancia > 2:
            return max(1, int((base * 0.05) + 0.999999))
        return base

    def coste_movimiento_estimado(self) -> int:
        coste = 2
        armas_dos_manos = sum(1 for arma in [self.weapon] if arma and "dos_manos" in arma.tags)
        return int(coste * 1.5 + 0.999999) if armas_dos_manos >= 2 else coste


class Francotirador(Jugador):
    """Francotirador: 100 salud, 100 energia, vision base +1."""

    clase_canonica: ClassVar[str] = "francotirador"

    def __init__(self, nombre: str, posicion: Position, nivel: int = 1, vision_base: int = 4) -> None:
        super().__init__(nombre, posicion, 100, 100, 100, 100, vision_base + 1, 22, nivel, character_class="francotirador")
        self.recorrido = [posicion]

    def modificar_danio(self, base: int, objetivo: Character) -> int:
        distancia = max(1, self.position.distance_to(objetivo.position))
        return int(base + distancia**1.2 + 0.999999)

    def coste_movimiento_estimado(self) -> int:
        return 1


class Zapador(Jugador):
    """Zapador: 105 salud, 95 energia; especialista tactico y trampas."""

    clase_canonica: ClassVar[str] = "zapador"

    def __init__(self, nombre: str, posicion: Position, nivel: int = 1, vision_base: int = 4) -> None:
        super().__init__(nombre, posicion, 105, 105, 95, 95, vision_base, 23, nivel, character_class="zapador")
        self.recorrido = [posicion]
        self.skills.add("trampas")
        self.skills.add("explosivos")

    def modificar_danio(self, base: int, objetivo: Character) -> int:
        return max(1, int((base * 0.05) + 0.999999)) if self.position.distance_to(objetivo.position) > 2 else base


class AliadoEscuadron(Ally):
    """Aliado tactico de las ampliaciones modernas del repo Java."""

    def __init__(self, nombre: str, posicion: Position, rol: str = "combatiente", nivel: int = 1) -> None:
        base_hp = 110 if rol == "medico" else 105
        base_energy = 105 if rol == "medico" else 100
        super().__init__(nombre, posicion, base_hp, base_hp, base_energy, base_energy, 4, 22, nivel, role=rol)


class Enemigo(Enemy):
    """Base abstracta de enemigos con multiplicador global de dano y audicion."""

    multiplicador_danio_global: ClassVar[float] = 1.0

    def __init__(
        self,
        nombre: str,
        salud: int,
        energia: int,
        posicion: Position,
        vision_base: int = 4,
        arquetipo: str = "enemigo",
        rol: str = "soldado",
        rango_audicion: int = 6,
    ) -> None:
        super().__init__(nombre, posicion, salud, salud, energia, energia, vision_base, 20, 1, archetype=arquetipo, role=rol)
        self.rango_audicion = rango_audicion

    @classmethod
    def set_multiplicador_danio_global(cls, multiplicador: float) -> None:
        if not 0.1 <= multiplicador <= 100.0:
            raise ValueError("Multiplicador de dano enemigo fuera de rango")
        cls.multiplicador_danio_global = multiplicador

    def modificar_danio(self, base: int, objetivo: Character) -> int:
        return max(1, round(base * self.multiplicador_danio_global))


class Sectoid(Enemigo):
    def __init__(self, nombre: str, posicion: Position, vision_base: int = 4) -> None:
        super().__init__(nombre, 70, 70, posicion, vision_base, "sectoid", "soldado")


class Floater(Enemigo):
    def __init__(self, nombre: str, salud: int, energia: int, posicion: Position, vision_base: int = 4) -> None:
        super().__init__(nombre, salud, energia, posicion, vision_base, "floater", "explorador")


class HeavyFloater(Floater):
    def __init__(self, nombre: str, posicion: Position, vision_base: int = 4) -> None:
        super().__init__(nombre, 110, 60, posicion, vision_base)
        self.archetype = "heavyfloater"
        self.role = "protector"

    def coste_movimiento_estimado(self) -> int:
        return 2


class Commander(Enemigo):
    def __init__(self, nombre: str, posicion: Position, vision_base: int = 4) -> None:
        super().__init__(nombre, 125, 120, posicion, vision_base, "commander", "mando")
        self.orden_emitida = False

    def bonificacion_aliados(self) -> float:
        return 1.15


class CommanderPrime(Commander):
    def __init__(self, nombre: str, posicion: Position, vision_base: int = 5) -> None:
        super().__init__(nombre, posicion, vision_base)
        self.max_hp = self.hp = 170
        self.max_energy = self.energy = 145
        self.archetype = "commander_prime"
        self.role = "jefe_mando"


class Berserker(Enemigo):
    def __init__(self, nombre: str, posicion: Position, vision_base: int = 4) -> None:
        super().__init__(nombre, 170, 110, posicion, vision_base, "berserker", "asalto")


class Jefe(Enemigo):
    def __init__(self, nombre: str, posicion: Position, fase: int = 1, vision_base: int = 5) -> None:
        super().__init__(nombre, 220, 160, posicion, vision_base, "jefe", "jefe")
        self.boss_phase = fase


# ---------------------------------------------------------------------------
# Objetos: clases canonicas del enunciado y del catalogo ampliado.
# ---------------------------------------------------------------------------
Objeto = Item


class Arma(Item):
    def __init__(
        self,
        nombre: str,
        peso: int,
        dano: int,
        alcance: int,
        municion_tipo: str | None = None,
        cargador: int = 0,
        municion_cargada: int = 0,
        penetracion: int = 0,
        tags: set[str] | None = None,
    ) -> None:
        super().__init__(nombre, ItemType.WEAPON, peso, dano, alcance, municion_tipo, cargador, municion_cargada, penetracion, False, tags or set())


class Armadura(Item):
    def __init__(self, nombre: str, peso: int, defensa: int, tags: set[str] | None = None) -> None:
        super().__init__(nombre, ItemType.ARMOR, peso, defensa, tags=tags or set())


class Botiquin(Item):
    def __init__(self, nombre: str = "botiquin", curacion: int = 20) -> None:
        super().__init__(nombre, ItemType.MEDKIT, 1, curacion)


class Linterna(Item):
    def __init__(self, nombre: str = "linterna", alcance: int = 4) -> None:
        super().__init__(nombre, ItemType.LANTERN, 2, alcance, reusable=True)


class Binocular(Item):
    def __init__(self, nombre: str = "binocular", alcance_extra: int = 4) -> None:
        super().__init__(nombre, ItemType.LANTERN, 1, alcance_extra, reusable=False, tags={"binocular"})


class CuboAgua(Item):
    def __init__(self, nombre: str = "cubo_agua", lleno: bool = True) -> None:
        super().__init__(nombre, ItemType.WATER_BUCKET, 3, 1 if lleno else 0, reusable=True)


class Explosivo(Item):
    def __init__(self, nombre: str = "explosivo", dano: int = 18, alcance: int = 4) -> None:
        super().__init__(nombre, ItemType.EXPLOSIVE, 1, dano, range=alcance)


class Granada(Explosivo):
    def __init__(self, nombre: str = "granada", dano: int = 18, alcance: int = 4) -> None:
        super().__init__(nombre, dano, alcance)
        self.tags.add("granada")


class Municion(Item):
    def __init__(self, nombre: str, tipo_municion: str, cantidad: int) -> None:
        super().__init__(nombre, ItemType.AMMO, 1, cantidad, ammo_type=tipo_municion)


class Credencial(Item):
    def __init__(self, nombre: str, referencia: str) -> None:
        super().__init__(nombre, ItemType.CREDENTIAL, 1, 0, tags={referencia})


class Componente(Item):
    def __init__(self, nombre: str) -> None:
        super().__init__(nombre, ItemType.COMPONENT, 1, 0)


@dataclass(frozen=True)
class HierarchyNode:
    name: str
    children: tuple["HierarchyNode", ...] = ()


JERARQUIA_CANONICA = HierarchyNode(
    "Personaje",
    (
        HierarchyNode("Jugador", (HierarchyNode("Marine"), HierarchyNode("Francotirador"), HierarchyNode("Zapador"))),
        HierarchyNode(
            "Enemigo",
            (
                HierarchyNode("Sectoid"),
                HierarchyNode("Floater", (HierarchyNode("HeavyFloater"),)),
                HierarchyNode("Commander", (HierarchyNode("CommanderPrime"),)),
                HierarchyNode("Berserker"),
                HierarchyNode("Jefe"),
            ),
        ),
        HierarchyNode("AliadoEscuadron"),
    ),
)


def crear_jugador(clase: str, nombre: str, posicion: Position, nivel: int = 1, vision_base: int = 4) -> Jugador:
    normalizada = clase.strip().lower()
    if normalizada == "marine":
        return Marine(nombre, posicion, nivel, vision_base)
    if normalizada == "francotirador":
        return Francotirador(nombre, posicion, nivel, vision_base)
    if normalizada == "zapador":
        return Zapador(nombre, posicion, nivel, vision_base)
    raise ValueError(f"clase de jugador no reconocida: {clase}")


def crear_enemigo(arquetipo: str, nombre: str, posicion: Position, vision_base: int = 4) -> Enemigo:
    normalizado = arquetipo.strip().lower()
    if normalizado == "sectoid":
        return Sectoid(nombre, posicion, vision_base)
    if normalizado in {"floater", "heavyfloater"}:
        return HeavyFloater(nombre, posicion, vision_base)
    if normalizado == "commander":
        return Commander(nombre, posicion, vision_base)
    if normalizado == "commander_prime":
        return CommanderPrime(nombre, posicion, vision_base)
    if normalizado == "berserker":
        return Berserker(nombre, posicion, vision_base)
    if normalizado in {"jefe", "boss"}:
        return Jefe(nombre, posicion, 1, vision_base)
    raise ValueError(f"arquetipo enemigo no reconocido: {arquetipo}")


__all__ = [
    "AliadoEscuadron",
    "Arma",
    "Armadura",
    "Berserker",
    "Binocular",
    "Botiquin",
    "Commander",
    "CommanderPrime",
    "Componente",
    "Credencial",
    "CuboAgua",
    "Enemigo",
    "Explosivo",
    "Floater",
    "Francotirador",
    "Granada",
    "HeavyFloater",
    "HierarchyNode",
    "JERARQUIA_CANONICA",
    "Jefe",
    "Jugador",
    "Linterna",
    "Marine",
    "Municion",
    "Objeto",
    "Personaje",
    "Sectoid",
    "Zapador",
    "crear_enemigo",
    "crear_jugador",
]
