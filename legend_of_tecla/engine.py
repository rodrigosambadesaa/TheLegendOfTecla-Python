"""Servicios de motor desacoplados.

Este modulo reconstruye parte de la arquitectura del paquete Java ``engine``:
movimiento, combate, inventario, trampas, fuego y avance de turnos como sistemas
separados que pueden ser usados por CLI, GUI, tests o un futuro motor mas fiel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .events import BusEventos, TipoEvento
from .exceptions import AccionInvalidaError, EnergiaInsuficienteError, MovimientoInvalidoError
from .model import Character, CharacterState, Direction, Item, ItemType, Position
from .world import InteractiveState, InteractiveType, MapGrid


@dataclass(frozen=True, slots=True)
class ResultadoAccion:
    ok: bool
    mensaje: str
    coste_energia: int = 0
    datos: dict[str, object] = field(default_factory=dict)

    @classmethod
    def exito(cls, mensaje: str, coste_energia: int = 0, **datos: object) -> "ResultadoAccion":
        return cls(True, mensaje, coste_energia, datos)

    @classmethod
    def fallo(cls, mensaje: str, **datos: object) -> "ResultadoAccion":
        return cls(False, mensaje, 0, datos)


class SistemaMovimiento:
    def __init__(self, mapa: MapGrid) -> None:
        self.mapa = mapa

    def coste(self, personaje: Character, destino: Position) -> int:
        celda = self.mapa.cell(destino)
        coste = 1
        if celda.dark:
            coste += 1
        if celda.fire > 0:
            coste += 1
        if personaje.load > personaje.capacity * 0.75:
            coste += 1
        return coste

    def mover(self, personaje: Character, direccion: Direction) -> ResultadoAccion:
        destino = personaje.position.moved(direccion)
        if not self.mapa.inside(destino):
            raise MovimientoInvalidoError("No puedes salir del mapa.")
        if not self.mapa.is_walkable(destino):
            raise MovimientoInvalidoError("La posicion esta bloqueada.")
        coste = self.coste(personaje, destino)
        if personaje.energy < coste:
            raise EnergiaInsuficienteError("Energia insuficiente para moverse.")
        personaje.spend_energy(coste)
        personaje.position = destino
        celda = self.mapa.cell(destino)
        mensajes = [f"{personaje.name} se mueve a {destino.row},{destino.col}."]
        if celda.fire > 0:
            personaje.apply_effect(CharacterState.BURNING, turns=2, power=celda.fire)
            mensajes.append(f"{personaje.name} atraviesa fuego.")
        return ResultadoAccion.exito(" ".join(mensajes), coste, destino=destino)


class SistemaCombate:
    def atacar(self, atacante: Character, objetivo: Character) -> ResultadoAccion:
        distancia = atacante.position.distance_to(objetivo.position)
        if distancia > atacante.attack_range:
            raise AccionInvalidaError("Objetivo fuera de alcance.")
        coste = 2 if atacante.weapon else 1
        if atacante.energy < coste:
            raise EnergiaInsuficienteError("Energia insuficiente para atacar.")
        atacante.spend_energy(coste)
        penetracion = atacante.weapon.penetration if atacante.weapon else 0
        danio = objetivo.receive_damage(atacante.attack_damage, penetracion)
        mensaje = f"{atacante.name} causa {danio} de dano a {objetivo.name}."
        if not objetivo.alive:
            mensaje += f" {objetivo.name} cae derrotado."
        return ResultadoAccion.exito(mensaje, coste, danio=danio, derrotado=not objetivo.alive)


class SistemaInventario:
    def recoger_todo(self, personaje: Character, mapa: MapGrid) -> ResultadoAccion:
        objetos = mapa.take_items(personaje.position)
        if not objetos:
            return ResultadoAccion.fallo("No hay objetos que recoger.")
        recogidos: list[str] = []
        rechazados: list[Item] = []
        for objeto in objetos:
            if personaje.can_carry(objeto):
                personaje.add_item(objeto)
                recogidos.append(objeto.name)
            else:
                rechazados.append(objeto)
        for objeto in rechazados:
            mapa.place_item(personaje.position, objeto)
        if not recogidos:
            return ResultadoAccion.fallo("La mochila esta llena.")
        return ResultadoAccion.exito("Recogido: " + ", ".join(recogidos), recogidos=recogidos)

    def usar(self, personaje: Character, nombre: str) -> ResultadoAccion:
        objeto = personaje.remove_item(nombre)
        if objeto.item_type is ItemType.MEDKIT:
            curado = personaje.heal(objeto.value or 10)
            return ResultadoAccion.exito(f"{personaje.name} recupera {curado} de salud.", curado=curado)
        if objeto.item_type in {ItemType.ENERGY, ItemType.TORITO_RED}:
            energia = personaje.recover_energy(objeto.value or 10)
            return ResultadoAccion.exito(f"{personaje.name} recupera {energia} de energia.", energia=energia)
        if objeto.item_type is ItemType.LANTERN:
            personaje.inventory.append(objeto)
            personaje.apply_effect(CharacterState.INSPIRED, 2, 1)
            return ResultadoAccion.exito(f"{personaje.name} enciende {objeto.name}.")
        personaje.inventory.append(objeto)
        raise AccionInvalidaError(f"{objeto.name} no se puede usar directamente.")

    def equipar(self, personaje: Character, nombre: str) -> ResultadoAccion:
        mensaje = personaje.equip(nombre)
        return ResultadoAccion.exito(mensaje)


class SistemaTrampas:
    def resolver_entrada(self, personaje: Character, mapa: MapGrid) -> ResultadoAccion | None:
        celda = mapa.cell(personaje.position)
        elemento = celda.element
        if elemento.kind is not InteractiveType.TRAP or elemento.state is not InteractiveState.ARMED:
            return None
        danio = personaje.receive_damage(max(1, elemento.difficulty or 4))
        elemento.state = InteractiveState.DISARMED
        return ResultadoAccion.exito(f"{personaje.name} activa una trampa y recibe {danio} de dano.", danio=danio)

    def desarmar(self, personaje: Character, mapa: MapGrid) -> ResultadoAccion:
        celda = mapa.cell(personaje.position)
        elemento = celda.element
        if elemento.kind is not InteractiveType.TRAP:
            raise AccionInvalidaError("No hay trampa en esta posicion.")
        if elemento.state is InteractiveState.DISARMED:
            return ResultadoAccion.fallo("La trampa ya estaba desarmada.")
        coste = max(1, elemento.difficulty // 2 or 1)
        if personaje.energy < coste:
            raise EnergiaInsuficienteError("Energia insuficiente para desarmar la trampa.")
        personaje.spend_energy(coste)
        elemento.state = InteractiveState.DISARMED
        return ResultadoAccion.exito("Trampa desarmada.", coste)


class SistemaFuego:
    def extinguir(self, personaje: Character, mapa: MapGrid, posiciones: Iterable[Position] | None = None) -> ResultadoAccion:
        posiciones = list(posiciones or [personaje.position])
        apagadas = 0
        for posicion in posiciones:
            if not mapa.inside(posicion):
                continue
            celda = mapa.cell(posicion)
            if celda.fire > 0:
                celda.fire = 0
                apagadas += 1
        if apagadas == 0:
            return ResultadoAccion.fallo("No hay fuego que extinguir.")
        return ResultadoAccion.exito(f"Fuego extinguido en {apagadas} casilla(s).", apagadas=apagadas)

    def propagar(self, mapa: MapGrid) -> list[str]:
        return mapa.tick_environment()


@dataclass(slots=True)
class MotorTurnos:
    mapa: MapGrid
    bus: BusEventos = field(default_factory=BusEventos)
    turno: int = 0

    def publicar_resultado(self, resultado: ResultadoAccion, tipo: TipoEvento, origen: str | None = None) -> None:
        self.bus.publicar(self.turno, tipo, resultado.mensaje, origen=origen, datos=resultado.datos)

    def avanzar(self, personajes: Iterable[Character] = ()) -> list[str]:
        self.turno += 1
        mensajes = list(self.mapa.tick_environment())
        for personaje in personajes:
            mensajes.extend(personaje.tick_effects())
        for mensaje in mensajes:
            self.bus.publicar(self.turno, TipoEvento.TURNO, mensaje, origen="motor")
        return mensajes
