"""Catálogo de objetos, armas y recetas.

Incluye más de treinta armas diferenciadas, munición, armaduras y objetos de
utilidad. El botín rota por el catálogo para no repetir modelo hasta completar
una vuelta.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import Item, ItemType


WEAPON_CATALOG: tuple[Item, ...] = (
    Item("espada_corta", ItemType.WEAPON, 3, 5, 1),
    Item("espada_larga", ItemType.WEAPON, 5, 8, 1),
    Item("mandoble", ItemType.WEAPON, 8, 12, 1, penetration=1),
    Item("cuchillo", ItemType.WEAPON, 1, 3, 1),
    Item("daga_arrojadiza", ItemType.WEAPON, 1, 4, 3),
    Item("hacha", ItemType.WEAPON, 6, 9, 1, penetration=1),
    Item("lanza", ItemType.WEAPON, 4, 6, 2),
    Item("arco_corto", ItemType.WEAPON, 3, 6, 5, ammo_type="flecha", magazine_size=1),
    Item("arco_largo", ItemType.WEAPON, 4, 8, 6, ammo_type="flecha", magazine_size=1),
    Item("ballesta", ItemType.WEAPON, 5, 10, 5, ammo_type="virote", magazine_size=1, penetration=2),
    Item("pistola_9mm", ItemType.WEAPON, 3, 9, 6, ammo_type="9mm", magazine_size=12, ammo_loaded=12, penetration=1),
    Item("pistola_pesada", ItemType.WEAPON, 4, 12, 5, ammo_type="45acp", magazine_size=7, ammo_loaded=7, penetration=2),
    Item("revolver", ItemType.WEAPON, 4, 13, 5, ammo_type="357", magazine_size=6, ammo_loaded=6, penetration=2),
    Item("subfusil", ItemType.WEAPON, 5, 10, 5, ammo_type="9mm", magazine_size=30, ammo_loaded=30),
    Item("escopeta", ItemType.WEAPON, 7, 16, 3, ammo_type="cartucho", magazine_size=8, ammo_loaded=8, penetration=1),
    Item("rifle_asalto", ItemType.WEAPON, 7, 14, 7, ammo_type="556", magazine_size=30, ammo_loaded=30, penetration=2),
    Item("carabina", ItemType.WEAPON, 6, 12, 7, ammo_type="556", magazine_size=20, ammo_loaded=20, penetration=1),
    Item("rifle_precision", ItemType.WEAPON, 8, 24, 10, ammo_type="762", magazine_size=5, ammo_loaded=5, penetration=5),
    Item("ametralladora", ItemType.WEAPON, 12, 18, 7, ammo_type="762", magazine_size=100, ammo_loaded=100, penetration=3),
    Item("lanzacohetes", ItemType.WEAPON, 14, 35, 8, ammo_type="cohete", magazine_size=1, ammo_loaded=1, penetration=10),
    Item("rifle_plasma", ItemType.WEAPON, 8, 22, 8, ammo_type="celda", magazine_size=20, ammo_loaded=20, penetration=6),
    Item("granada_frag", ItemType.WEAPON, 1, 20, 4, tags={"explosiva"}),
    Item("granada_humo", ItemType.WEAPON, 1, 0, 4, tags={"humo"}),
    Item("granada_incendiaria", ItemType.WEAPON, 1, 12, 4, tags={"fuego"}),
    Item("martillo_guerra", ItemType.WEAPON, 7, 11, 1, penetration=3),
    Item("sable_xeno", ItemType.WEAPON, 4, 14, 1, penetration=4, tags={"xeno"}),
    Item("fusil_xeno", ItemType.WEAPON, 6, 18, 7, ammo_type="plasma_xeno", magazine_size=24, ammo_loaded=24, penetration=5, tags={"xeno"}),
    Item("aguijon_xeno", ItemType.WEAPON, 2, 9, 2, penetration=3, tags={"xeno"}),
    Item("canon_psi", ItemType.WEAPON, 8, 21, 6, ammo_type="psi", magazine_size=8, ammo_loaded=8, penetration=8, tags={"xeno"}),
    Item("laser_ligero", ItemType.WEAPON, 5, 15, 7, ammo_type="celda", magazine_size=30, ammo_loaded=30, penetration=4),
    Item("hoja_energia", ItemType.WEAPON, 3, 17, 1, penetration=7),
    Item("rifle_gauss", ItemType.WEAPON, 9, 28, 9, ammo_type="gauss", magazine_size=10, ammo_loaded=10, penetration=9),
)

ARMOR_CATALOG: tuple[Item, ...] = (
    Item("chaleco_ligero", ItemType.ARMOR, 4, 2),
    Item("armadura_tactica", ItemType.ARMOR, 7, 5),
    Item("exotraje", ItemType.ARMOR, 12, 8),
    Item("coraza_xeno", ItemType.ARMOR, 7, 7, tags={"xeno"}),
)

BASIC_ITEMS: tuple[Item, ...] = (
    Item("botiquin", ItemType.MEDKIT, 1, 20),
    Item("torito", ItemType.ENERGY, 1, 18),
    Item("torito_rojo", ItemType.TORITO_RED, 1, 35),
    Item("linterna", ItemType.LANTERN, 2, 4, reusable=True),
    Item("cubo_agua", ItemType.WATER_BUCKET, 3, 1, reusable=True),
    Item("granada", ItemType.EXPLOSIVE, 1, 18, range=4),
    Item("tarjeta_reactor", ItemType.CREDENTIAL, 1, 0, tags={"reactor"}),
    Item("chatarra", ItemType.COMPONENT, 1, 0),
    Item("polvora", ItemType.COMPONENT, 1, 0),
)

AMMO_TYPES = ("flecha", "virote", "9mm", "45acp", "357", "cartucho", "556", "762", "cohete", "celda", "plasma_xeno", "psi", "gauss")


@dataclass
class LootCycle:
    counter: int = 0

    def next_weapon(self) -> Item:
        template = WEAPON_CATALOG[self.counter % len(WEAPON_CATALOG)]
        self.counter += 1
        return template.clone(f"{template.name}_{self.counter}")


def make_item(kind: str, name: str | None = None, value: int | None = None) -> Item:
    normalized = kind.strip().lower()
    catalog = list(WEAPON_CATALOG) + list(ARMOR_CATALOG) + list(BASIC_ITEMS)
    for template in catalog:
        if normalized in {template.name.lower(), template.item_type.value, template.name.lower().replace("_", "")}:
            item = template.clone(name or template.name)
            if value is not None:
                item.value = value
            return item
    if normalized in AMMO_TYPES or normalized == "municion":
        ammo_type = normalized if normalized != "municion" else "9mm"
        return Item(name or f"municion_{ammo_type}", ItemType.AMMO, 1, int(value or 10), ammo_type=str(ammo_type))
    raise ValueError(f"tipo de objeto no reconocido: {kind}")


@dataclass(frozen=True)
class Recipe:
    result: str
    ingredients: tuple[str, ...]
    item: Item


RECIPES: tuple[Recipe, ...] = (
    Recipe("granada", ("chatarra", "polvora"), Item("granada_casera", ItemType.EXPLOSIVE, 1, 16, range=4)),
    Recipe("botiquin", ("venda", "alcohol"), Item("botiquin_improvisado", ItemType.MEDKIT, 1, 14)),
    Recipe("linterna", ("chatarra", "celda"), Item("linterna_reciclada", ItemType.LANTERN, 2, 3, reusable=True)),
)
