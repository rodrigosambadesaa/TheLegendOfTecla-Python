from pathlib import Path

from legend_of_tecla.achievements import RegistroLogros
from legend_of_tecla.audio import AudioNulo
from legend_of_tecla.config import ConfiguracionJuego, cargar_configuracion, guardar_configuracion
from legend_of_tecla.inventory import Equipamiento, Mochila
from legend_of_tecla.io import cargar_escenario
from legend_of_tecla.model import Item, ItemType, Position, Statistics
from legend_of_tecla.persistence import cargar_save, guardar_save
from legend_of_tecla.progression import Habilidad, ProgresionPersonaje


def test_config_roundtrip_json(tmp_path: Path):
    path = tmp_path / "config.json"
    guardar_configuracion(ConfiguracionJuego(jugador_nombre="Rodrigo", filas=7, columnas=9), path)
    loaded = cargar_configuracion(path)
    assert loaded.jugador_nombre == "Rodrigo"
    assert loaded.dimensiones == (7, 9)


def test_inventory_and_equipment_rules():
    mochila = Mochila(10)
    pistola = Item("pistola", ItemType.WEAPON, weight=2, value=4)
    botiquin = Item("botiquin", ItemType.MEDKIT, weight=1, value=20)

    mochila.anadir(pistola)
    mochila.anadir(botiquin, 2)

    assert mochila.peso == 4
    assert mochila.contiene("botiquin")
    item = mochila.retirar("pistola")

    equipo = Equipamiento()
    equipo.equipar(item)
    assert equipo.danio == 4


def test_progression_and_achievements():
    progresion = ProgresionPersonaje()
    mensajes = progresion.ganar_xp(120)
    assert progresion.nivel == 2
    assert mensajes
    progresion.aprender(Habilidad.PUNTERIA)
    assert progresion.bonificador("punteria") > 1.0

    stats = Statistics(enemies_killed=5, items_collected=10, traps_disarmed=3, fires_extinguished=3, turns=10)
    registro = RegistroLogros()
    unlocked = registro.evaluar(stats)
    assert {logro.code for logro in unlocked} >= {"primer_enemigo", "limpieza", "coleccionista"}


def test_persistence_versioned_payload(tmp_path: Path):
    path = tmp_path / "save.json"
    guardar_save({"turno": 3, "jugador": {"nombre": "Tecla"}}, path)
    save = cargar_save(path)
    assert save.metadata.version >= 1
    assert save.payload["turno"] == 3


def test_io_loads_text_scenario(tmp_path: Path):
    scenario = tmp_path / "escenario"
    scenario.mkdir()
    (scenario / "mapa.txt").write_text("J..\n.#X\n", encoding="utf-8")
    (scenario / "objetos.txt").write_text("0,1,botiquin\n", encoding="utf-8")
    (scenario / "enemigos.txt").write_text("1,0,sectoid,Alien\n", encoding="utf-8")

    loaded = cargar_escenario(scenario)

    assert loaded.mapa.start == Position(0, 0)
    assert loaded.mapa.goal == Position(1, 2)
    assert loaded.mapa.cell(Position(0, 1)).items
    assert loaded.enemigos[0].tipo == "sectoid"


def test_null_audio_is_observable():
    audio = AudioNulo()
    audio.musica("tema")
    audio.reproducir("ataque")
    audio.parar()
    assert audio.eventos == ["musica:tema:loop", "ataque", "stop"]
