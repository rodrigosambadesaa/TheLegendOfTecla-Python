from legend_of_tecla.ai import TipoAccionIA, controlador_para
from legend_of_tecla.commands import ComandoAtacar, ComandoLanzarExplosivo, ParserComandos
from legend_of_tecla.effects import Fuego, GestorEstados, Inspirado
from legend_of_tecla.engine import SistemaCombate, SistemaFuego, SistemaInventario, SistemaMovimiento, SistemaTrampas
from legend_of_tecla.events import BusEventos, TipoEvento
from legend_of_tecla.exceptions import AccionInvalidaError, TeclaError
from legend_of_tecla.model import Character, Direction, Item, ItemType, Position
from legend_of_tecla.validation import ConfiguracionError, Validaciones
from legend_of_tecla.world import InteractiveElement, InteractiveState, InteractiveType, MapGrid


def make_character(name="Tecla", pos=Position(0, 0)):
    return Character(name, pos, hp=20, max_hp=20, energy=10, max_energy=10, vision=4, capacity=20)


def test_parser_returns_command_objects():
    parser = ParserComandos()

    mover = parser.parsear("mover norte")
    atacar = parser.parsear("atacar este")
    lanzar = parser.parsear("lanzar granada sur")

    assert mover.serializar() == "mover norte"
    assert isinstance(atacar, ComandoAtacar)
    assert isinstance(lanzar, ComandoLanzarExplosivo)
    assert lanzar.direccion is Direction.SOUTH


def test_event_bus_records_and_notifies():
    bus = BusEventos()
    seen = []
    bus.suscribir(seen.append, TipoEvento.COMBATE)

    bus.publicar(3, TipoEvento.COMBATE, "impacto", origen="test", datos={"danio": 4})

    assert seen[0].mensaje == "impacto"
    assert "combate/test" in bus.registro.texto()


def test_effect_manager_applies_fire_and_inspiration():
    personaje = make_character()
    gestor = GestorEstados()
    personaje.energy = 3

    gestor.aplicar(personaje, Inspirado(turnos=2, potencia=4))
    gestor.aplicar(personaje, Fuego(turnos=1, potencia=2))
    mensajes = gestor.tick(personaje)

    assert personaje.energy == 7
    assert personaje.hp == 18
    assert any("fuego" in mensaje for mensaje in mensajes)


def test_ai_controller_selects_expected_actions():
    enemigo = make_character("Sectoid", Position(0, 2))
    jugador = make_character("Tecla", Position(0, 0))

    accion = controlador_para("sectoid").decidir(enemigo, jugador)
    accion_berserker = controlador_para("berserker").decidir(enemigo, jugador)

    assert accion.tipo in {TipoAccionIA.ATACAR, TipoAccionIA.ACERCARSE}
    assert accion_berserker.tipo is TipoAccionIA.ACERCARSE


def test_engine_services_move_combat_inventory_fire_and_traps():
    mapa = MapGrid(3, 3)
    jugador = make_character("Tecla", Position(0, 0))
    enemigo = make_character("Sectoid", Position(0, 1))
    espada = Item("rifle", ItemType.WEAPON, value=5, range=1)
    mapa.place_item(jugador.position, espada)

    inventario = SistemaInventario()
    assert inventario.recoger_todo(jugador, mapa).ok is True
    assert inventario.equipar(jugador, "rifle").ok is True
    assert SistemaCombate().atacar(jugador, enemigo).datos["danio"] >= 1

    movimiento = SistemaMovimiento(mapa)
    assert movimiento.mover(jugador, Direction.SOUTH).ok is True

    mapa.cell(jugador.position).element = InteractiveElement(InteractiveType.TRAP, state=InteractiveState.ARMED, difficulty=3)
    resultado_trampa = SistemaTrampas().resolver_entrada(jugador, mapa)
    assert resultado_trampa is not None
    assert resultado_trampa.ok is True

    mapa.cell(jugador.position).fire = 3
    assert SistemaFuego().extinguir(jugador, mapa).datos["apagadas"] == 1


def test_validation_and_exception_exports():
    assert issubclass(AccionInvalidaError, TeclaError)
    try:
        Validaciones.texto_obligatorio("", "Nombre")
    except ConfiguracionError:
        pass
    else:
        raise AssertionError("Expected validation error")
