"""Sistema de logros.

Separa reglas de desbloqueo del motor principal, como el paquete
``achievements`` del Java.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .model import Achievement, Statistics


ReglaLogro = Callable[[Statistics], bool]


@dataclass(frozen=True, slots=True)
class DefinicionLogro:
    codigo: str
    titulo: str
    descripcion: str
    regla: ReglaLogro


def _sin_danio(stats: Statistics) -> bool:
    return stats.turns > 0 and stats.damage_taken == 0 and stats.enemies_killed > 0


LOGROS_BASE: tuple[DefinicionLogro, ...] = (
    DefinicionLogro("primer_enemigo", "Primer contacto", "Neutraliza tu primer enemigo.", lambda s: s.enemies_killed >= 1),
    DefinicionLogro("limpieza", "Zona limpia", "Neutraliza cinco enemigos.", lambda s: s.enemies_killed >= 5),
    DefinicionLogro("coleccionista", "Coleccionista", "Recoge diez objetos.", lambda s: s.items_collected >= 10),
    DefinicionLogro("zapador", "Manos firmes", "Desactiva tres trampas.", lambda s: s.traps_disarmed >= 3),
    DefinicionLogro("bombero", "Cortafuegos", "Extingue tres fuegos.", lambda s: s.fires_extinguished >= 3),
    DefinicionLogro("intocable", "Intocable", "Gana combates sin recibir dano.", _sin_danio),
)


@dataclass(slots=True)
class RegistroLogros:
    definiciones: tuple[DefinicionLogro, ...] = LOGROS_BASE
    logros: dict[str, Achievement] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for definicion in self.definiciones:
            self.logros.setdefault(
                definicion.codigo,
                Achievement(definicion.codigo, definicion.titulo, definicion.descripcion),
            )

    def evaluar(self, stats: Statistics) -> list[Achievement]:
        desbloqueados: list[Achievement] = []
        for definicion in self.definiciones:
            logro = self.logros[definicion.codigo]
            if not logro.unlocked and definicion.regla(stats):
                logro.unlocked = True
                desbloqueados.append(logro)
        return desbloqueados

    def desbloqueados(self) -> list[Achievement]:
        return [logro for logro in self.logros.values() if logro.unlocked]

    def to_dict(self) -> dict:
        return {codigo: logro.unlocked for codigo, logro in self.logros.items()}

    @classmethod
    def from_dict(cls, data: dict[str, bool]) -> "RegistroLogros":
        registro = cls()
        for codigo, desbloqueado in data.items():
            if codigo in registro.logros:
                registro.logros[codigo].unlocked = bool(desbloqueado)
        return registro
