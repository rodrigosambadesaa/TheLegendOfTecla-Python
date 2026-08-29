"""Infraestructura de eventos del motor.

El Java original separa eventos, logros, audio, motor y GUI. Este modulo aporta
un bus observable sencillo para que consola, GUI, logros o audio puedan escuchar
lo que ocurre sin acoplarse al nucleo del juego.
"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TipoEvento(str, Enum):
    TURNO = "turno"
    MOVIMIENTO = "movimiento"
    COMBATE = "combate"
    INVENTARIO = "inventario"
    ENTORNO = "entorno"
    IA = "ia"
    LOGRO = "logro"
    SISTEMA = "sistema"


@dataclass(frozen=True, slots=True)
class EventoJuego:
    turno: int
    tipo: TipoEvento
    mensaje: str
    origen: str | None = None
    datos: dict[str, Any] = field(default_factory=dict)

    def formato_consola(self) -> str:
        prefijo = f"[{self.turno:04d}] {self.tipo.value}"
        if self.origen:
            prefijo += f"/{self.origen}"
        return f"{prefijo}: {self.mensaje}"


ObservadorEvento = Callable[[EventoJuego], None]


@dataclass(slots=True)
class RegistroEventos:
    """Log acotado y consultable de eventos recientes."""

    limite: int = 300
    _eventos: deque[EventoJuego] = field(default_factory=deque)

    def agregar(self, evento: EventoJuego) -> None:
        self._eventos.append(evento)
        while len(self._eventos) > self.limite:
            self._eventos.popleft()

    def ultimos(self, limite: int | None = None) -> list[EventoJuego]:
        eventos = list(self._eventos)
        if limite is None:
            return eventos
        return eventos[-limite:]

    def texto(self, limite: int = 30) -> str:
        return "\n".join(evento.formato_consola() for evento in self.ultimos(limite))


@dataclass(slots=True)
class BusEventos:
    """Publicador/suscriptor minimo para desacoplar sistemas."""

    registro: RegistroEventos = field(default_factory=RegistroEventos)
    _observadores: dict[TipoEvento | None, list[ObservadorEvento]] = field(default_factory=lambda: defaultdict(list))

    def suscribir(self, observador: ObservadorEvento, tipo: TipoEvento | None = None) -> None:
        self._observadores[tipo].append(observador)

    def publicar(
        self,
        turno: int,
        tipo: TipoEvento,
        mensaje: str,
        *,
        origen: str | None = None,
        datos: dict[str, Any] | None = None,
    ) -> EventoJuego:
        evento = EventoJuego(turno=turno, tipo=tipo, mensaje=mensaje, origen=origen, datos=datos or {})
        self.registro.agregar(evento)
        for observador in self._observadores.get(tipo, []):
            observador(evento)
        for observador in self._observadores.get(None, []):
            observador(evento)
        return evento

    def extender(self, eventos: Iterable[EventoJuego]) -> None:
        for evento in eventos:
            self.registro.agregar(evento)
