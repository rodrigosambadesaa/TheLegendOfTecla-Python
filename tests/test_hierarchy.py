from legend_of_tecla.hierarchy import (
    AliadoEscuadron,
    Arma,
    Armadura,
    Berserker,
    Binocular,
    Botiquin,
    Commander,
    CommanderPrime,
    Componente,
    Credencial,
    CuboAgua,
    Enemigo,
    Explosivo,
    Floater,
    Francotirador,
    Granada,
    HeavyFloater,
    JERARQUIA_CANONICA,
    Jefe,
    Jugador,
    Linterna,
    Marine,
    Municion,
    Objeto,
    Personaje,
    Sectoid,
    Zapador,
    crear_enemigo,
    crear_jugador,
)
from legend_of_tecla.model import Ally, Character, Enemy, Item, ItemType, Player, Position


def test_player_hierarchy_matches_original_specification():
    assert issubclass(Jugador, Player)
    assert issubclass(Jugador, Personaje)
    assert issubclass(Marine, Jugador)
    assert issubclass(Francotirador, Jugador)
    assert issubclass(Zapador, Jugador)

    marine = Marine("Marine", Position(0, 0))
    sniper = Francotirador("Sniper", Position(0, 0), vision_base=4)
    sapper = Zapador("Zapador", Position(0, 0))

    assert isinstance(marine, Player)
    assert isinstance(marine, Character)
    assert marine.max_hp == 120
    assert marine.max_energy == 90
    assert sniper.max_hp == 100
    assert sniper.max_energy == 100
    assert sniper.vision == 5
    assert sapper.max_hp == 105
    assert sapper.max_energy == 95
    assert "trampas" in sapper.skills


def test_enemy_hierarchy_matches_original_and_expanded_java():
    assert issubclass(Enemigo, Enemy)
    assert issubclass(Sectoid, Enemigo)
    assert issubclass(Floater, Enemigo)
    assert issubclass(HeavyFloater, Floater)
    assert issubclass(Commander, Enemigo)
    assert issubclass(CommanderPrime, Commander)
    assert issubclass(Berserker, Enemigo)
    assert issubclass(Jefe, Enemigo)

    sectoid = Sectoid("sectoid", Position(1, 1))
    heavy = HeavyFloater("heavy", Position(1, 1))
    commander = Commander("commander", Position(1, 1))
    berserker = Berserker("berserker", Position(1, 1))
    boss = Jefe("boss", Position(1, 1))

    assert sectoid.max_hp == 70
    assert sectoid.max_energy == 70
    assert heavy.max_hp == 110
    assert heavy.max_energy == 60
    assert commander.max_hp == 125
    assert commander.max_energy == 120
    assert commander.bonificacion_aliados() == 1.15
    assert berserker.max_hp == 170
    assert berserker.max_energy == 110
    assert boss.boss_phase == 1


def test_item_hierarchy_uses_real_subclasses_not_only_type_strings():
    objects = [
        Arma("espada", 3, 5, 1),
        Armadura("chaleco", 4, 2),
        Botiquin(),
        Linterna(),
        Binocular(),
        CuboAgua(),
        Explosivo(),
        Granada(),
        Municion("balas", "9mm", 12),
        Credencial("tarjeta", "reactor"),
        Componente("chatarra"),
    ]

    assert all(isinstance(obj, Item) for obj in objects)
    assert all(isinstance(obj, Objeto) for obj in objects)
    assert objects[0].item_type is ItemType.WEAPON
    assert objects[1].item_type is ItemType.ARMOR
    assert objects[2].item_type is ItemType.MEDKIT
    assert objects[5].item_type is ItemType.WATER_BUCKET
    assert objects[7].item_type is ItemType.EXPLOSIVE
    assert objects[8].ammo_type == "9mm"
    assert "reactor" in objects[9].tags


def test_factories_and_canonical_tree_are_consistent():
    assert isinstance(crear_jugador("marine", "Rodrigo", Position(0, 0)), Marine)
    assert isinstance(crear_jugador("francotirador", "Rodrigo", Position(0, 0)), Francotirador)
    assert isinstance(crear_jugador("zapador", "Rodrigo", Position(0, 0)), Zapador)
    assert isinstance(crear_enemigo("sectoid", "alien", Position(2, 2)), Sectoid)
    assert isinstance(crear_enemigo("heavyfloater", "alien", Position(2, 2)), HeavyFloater)
    assert isinstance(AliadoEscuadron("aliado", Position(0, 1), "medico"), Ally)

    assert JERARQUIA_CANONICA.name == "Personaje"
    assert [node.name for node in JERARQUIA_CANONICA.children] == ["Jugador", "Enemigo", "AliadoEscuadron"]
