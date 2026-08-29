"""Sistema de estados alterados.

Recrea el papel de ``effects.GestorEstados`` y clases de estado del Java, pero
en una forma Pythonica y desacoplada del motor principal. Funciona con cualquier
objeto que exponga metodos compatibles con ``Character``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .model import CharacterState
from .validation import LIMITES, entero_entre


class SoportaEstado(Protocol):
    name: str

    def receive_damage(self, raw_damage: int, penetration: int = 0) -> int: ...
    def heal(self, amount: int) -> int: ...
    def recover_energy(self, amount: int) -> int: ...


class PoliticaAcumulacion(str, Enum):
    REEMPLAZAR = "reemplazar"
    REFRESCAR = "refrescar"
    ACUMULAR_POTENCIA = "acumular_potencia"


@dataclass(slots=True)
class EfectoEstado:
    estado: CharacterState
    turnos: int
    potencia: int = 1
    politica: PoliticaAcumulacion = PoliticaAcumulacion.REFRESCAR

    def __post_init__(self) -> None:
        entero_entre(self.turnos, 1, LIMITES.TURNOS_MAXIMOS_EFECTO, "Turnos del efecto")
        entero_entre(self.potencia, 1, LIMITES.ESTADISTICA, "Potencia del efecto")

    def aplicar_inicio(self, objetivo: SoportaEstado) -> list[str]:
        return []

    def aplicar_turno(self, objetivo: SoportaEstado) -> list[str]:
        self.turnos -= 1
        return []

    @property
    def activo(self) -> bool:
        return self.turnos > 0

    def combinar(self, otro: "EfectoEstado") -> None:
        if self.politica is PoliticaAcumulacion.REEMPLAZAR:
            self.turnos = otro.turnos
            self.potencia = otro.potencia
        elif self.politica is PoliticaAcumulacion.ACUMULAR_POTENCIA:
            self.turnos = max(self.turnos, otro.turnos)
            self.potencia += otro.potencia
        else:
            self.turnos = max(self.turnos, otro.turnos)
            self.potencia = max(self.potencia, otro.potencia)


class Fuego(EfectoEstado):
    def __init__(self, turnos: int, potencia: int = 1) -> None:
        super().__init__(CharacterState.BURNING, turnos, potencia, PoliticaAcumulacion.ACUMULAR_POTENCIA)

    def aplicar_turno(self, objetivo: SoportaEstado) -> list[str]:
        danio = objetivo.receive_damage(self.potencia)
        self.turnos -= 1
        return [f"{objetivo.name} sufre {danio} de dano por fuego."]


class Mojado(EfectoEstado):
    def __init__(self, turnos: int, potencia: int = 1) -> None:
        super().__init__(CharacterState.WET, turnos, potencia, PoliticaAcumulacion.REFRESCAR)

    def aplicar_inicio(self, objetivo: SoportaEstado) -> list[str]:
        return [f"{objetivo.name} queda mojado y resiste mejor el fuego."]


class Aturdido(EfectoEstado):
    def __init__(self, turnos: int, potencia: int = 1) -> None:
        super().__init__(CharacterState.STUNNED, turnos, potencia, PoliticaAcumulacion.REFRESCAR)

    def aplicar_turno(self, objetivo: SoportaEstado) -> list[str]:
        self.turnos -= 1
        return [f"{objetivo.name} pierde el turno por aturdimiento."]


class Inspirado(EfectoEstado):
    def __init__(self, turnos: int, potencia: int = 1) -> None:
        super().__init__(CharacterState.INSPIRED, turnos, potencia, PoliticaAcumulacion.REFRESCAR)

    def aplicar_inicio(self, objetivo: SoportaEstado) -> list[str]:
        recuperada = objetivo.recover_energy(self.potencia)
        return [f"{objetivo.name} recupera {recuperada} de energia al inspirarse."]


@dataclass(slots=True)
class GestorEstados:
    """Colecciona y procesa efectos temporales de un personaje."""

    efectos: list[EfectoEstado] = field(default_factory=list)

    def aplicar(self, objetivo: SoportaEstado, efecto: EfectoEstado) -> list[str]:
        existente = self.buscar(efecto.estado)
        if existente:
            existente.combinar(efecto)
            return [f"{objetivo.name} prolonga {efecto.estado.value}."]
        self.efectos.append(efecto)
        return efecto.aplicar_inicio(objetivo)

    def buscar(self, estado: CharacterState) -> EfectoEstado | None:
        return next((efecto for efecto in self.efectos if efecto.estado is estado), None)

    def tiene(self, estado: CharacterState) -> bool:
        return self.buscar(estado) is not None

    def tick(self, objetivo: SoportaEstado) -> list[str]:
        mensajes: list[str] = []
        activos: list[EfectoEstado] = []
        for efecto in self.efectos:
            mensajes.extend(efecto.aplicar_turno(objetivo))
            if efecto.activo:
                activos.append(efecto)
            else:
                mensajes.append(f"{objetivo.name} deja de estar {efecto.estado.value}.")
        self.efectos = activos
        return mensajes

    def multiplicador_vision(self) -> float:
        if self.tiene(CharacterState.STUNNED):
            return 0.5
        if self.tiene(CharacterState.INSPIRED):
            return 1.15
        return 1.0
