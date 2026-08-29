"""Servicios de audio.

La version Python ofrece una implementacion nula por defecto para mantener el
motor testeable en CI/headless. Una GUI puede sustituirla por otra implementacion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class ServicioAudio(Protocol):
    def reproducir(self, evento: str) -> None: ...
    def musica(self, pista: str, repetir: bool = True) -> None: ...
    def parar(self) -> None: ...


@dataclass(slots=True)
class AudioNulo:
    eventos: list[str] = field(default_factory=list)
    pista_actual: str | None = None

    def reproducir(self, evento: str) -> None:
        self.eventos.append(evento)

    def musica(self, pista: str, repetir: bool = True) -> None:
        self.pista_actual = pista
        self.eventos.append(f"musica:{pista}:{'loop' if repetir else 'once'}")

    def parar(self) -> None:
        self.eventos.append("stop")
        self.pista_actual = None
