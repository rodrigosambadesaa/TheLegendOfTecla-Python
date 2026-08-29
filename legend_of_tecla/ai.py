"""IA tactica del juego.

Aporta equivalentes compactos de ``PercepcionIA``, ``ContextoIA``,
``AccionIA`` y ``ControladorIA``. No sustituye al motor completo, pero ya deja
modelado el patron State/Strategy que el repo Java usa para enemigos tacticos.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .model import AlertState, Character, Direction, Position


class TipoAccionIA(str, Enum):
    ESPERAR = "esperar"
    ACERCARSE = "acercarse"
    ATACAR = "atacar"
    BUSCAR = "buscar"
    PROTEGER = "proteger"
    RETIRARSE = "retirarse"
    USAR_HABILIDAD = "usar_habilidad"


@dataclass(frozen=True, slots=True)
class AccionIA:
    tipo: TipoAccionIA
    objetivo: Position | None = None
    direccion: Direction | None = None
    motivo: str = ""


@dataclass(frozen=True, slots=True)
class PercepcionIA:
    ve_jugador: bool
    oye_jugador: bool
    distancia_jugador: int
    posicion_jugador: Position
    aliados_cercanos: int = 0
    enemigos_cercanos: int = 0
    salud_baja: bool = False


@dataclass(frozen=True, slots=True)
class ContextoIA:
    enemigo: Character
    jugador: Character
    percepcion: PercepcionIA
    coordinacion_activa: bool = False

    @property
    def posicion_objetivo(self) -> Position:
        return self.percepcion.posicion_jugador

    @property
    def distancia_jugador(self) -> int:
        return self.percepcion.distancia_jugador


class EstrategiaIA(Protocol):
    def decidir(self, contexto: ContextoIA) -> AccionIA: ...


class EstrategiaAgresiva:
    def decidir(self, contexto: ContextoIA) -> AccionIA:
        if contexto.distancia_jugador <= contexto.enemigo.attack_range:
            return AccionIA(TipoAccionIA.ATACAR, contexto.posicion_objetivo, motivo="objetivo en alcance")
        return AccionIA(
            TipoAccionIA.ACERCARSE,
            contexto.posicion_objetivo,
            direccion=direccion_hacia(contexto.enemigo.position, contexto.posicion_objetivo),
            motivo="presion ofensiva",
        )


class EstrategiaCauta:
    def decidir(self, contexto: ContextoIA) -> AccionIA:
        if contexto.percepcion.salud_baja:
            return AccionIA(
                TipoAccionIA.RETIRARSE,
                contexto.enemigo.position,
                direccion=direccion_hacia(contexto.posicion_objetivo, contexto.enemigo.position),
                motivo="salud baja",
            )
        if contexto.percepcion.ve_jugador:
            return EstrategiaAgresiva().decidir(contexto)
        if contexto.percepcion.oye_jugador:
            return AccionIA(TipoAccionIA.BUSCAR, contexto.posicion_objetivo, motivo="ruido detectado")
        return AccionIA(TipoAccionIA.ESPERAR, motivo="sin contacto")


class EstrategiaCoordinador:
    def __init__(self) -> None:
        self.orden_emitida = False

    def decidir(self, contexto: ContextoIA) -> AccionIA:
        if contexto.coordinacion_activa and not self.orden_emitida:
            self.orden_emitida = True
            return AccionIA(TipoAccionIA.PROTEGER, contexto.enemigo.position, motivo="coordinacion de escuadra")
        return EstrategiaAgresiva().decidir(contexto)


class EstrategiaBerserker:
    def decidir(self, contexto: ContextoIA) -> AccionIA:
        if contexto.distancia_jugador <= 1:
            return AccionIA(TipoAccionIA.ATACAR, contexto.posicion_objetivo, motivo="furia cuerpo a cuerpo")
        return AccionIA(
            TipoAccionIA.ACERCARSE,
            contexto.posicion_objetivo,
            direccion=direccion_hacia(contexto.enemigo.position, contexto.posicion_objetivo),
            motivo="carga berserker",
        )


@dataclass(slots=True)
class ControladorIA:
    estrategia: EstrategiaIA
    estado: AlertState = AlertState.IDLE
    ultima_posicion_jugador: Position | None = None

    def percibir(self, enemigo: Character, jugador: Character, *, aliados_cercanos: int = 0) -> PercepcionIA:
        distancia = enemigo.position.distance_to(jugador.position)
        ve = distancia <= enemigo.vision
        oye = distancia <= max(enemigo.vision + 2, 6)
        if ve or oye:
            self.ultima_posicion_jugador = jugador.position
        return PercepcionIA(
            ve_jugador=ve,
            oye_jugador=oye,
            distancia_jugador=distancia,
            posicion_jugador=jugador.position,
            aliados_cercanos=aliados_cercanos,
            salud_baja=enemigo.hp <= max(1, enemigo.max_hp // 3),
        )

    def decidir(self, enemigo: Character, jugador: Character, *, coordinacion_activa: bool = False) -> AccionIA:
        percepcion = self.percibir(enemigo, jugador)
        if percepcion.ve_jugador:
            self.estado = AlertState.ENGAGING
        elif percepcion.oye_jugador:
            self.estado = AlertState.SEARCHING
        else:
            self.estado = AlertState.IDLE
        return self.estrategia.decidir(ContextoIA(enemigo, jugador, percepcion, coordinacion_activa))


def direccion_hacia(origen: Position, destino: Position) -> Direction | None:
    delta_fila = destino.row - origen.row
    delta_col = destino.col - origen.col
    if abs(delta_fila) >= abs(delta_col) and delta_fila != 0:
        return Direction.SOUTH if delta_fila > 0 else Direction.NORTH
    if delta_col != 0:
        return Direction.EAST if delta_col > 0 else Direction.WEST
    return None


def controlador_para(arquetipo: str) -> ControladorIA:
    normalizado = arquetipo.strip().lower()
    if normalizado in {"commander", "commanderprime", "commander_prime"}:
        return ControladorIA(EstrategiaCoordinador())
    if normalizado == "berserker":
        return ControladorIA(EstrategiaBerserker())
    if normalizado in {"sectoid", "floater", "heavyfloater", "heavy_floater"}:
        return ControladorIA(EstrategiaAgresiva())
    return ControladorIA(EstrategiaCauta())
