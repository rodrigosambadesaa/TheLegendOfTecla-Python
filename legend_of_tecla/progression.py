"""Progresion persistente de personajes y campana."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .validation import entero_entre


class Habilidad(str, Enum):
    PUNTERIA = "punteria"
    RESISTENCIA = "resistencia"
    ZAPADOR = "zapador"
    LIDERAZGO = "liderazgo"
    SIGILO = "sigilo"
    MEDICINA = "medicina"


@dataclass(slots=True)
class ProgresionPersonaje:
    nivel: int = 1
    experiencia: int = 0
    habilidades: set[Habilidad] = field(default_factory=set)
    puntos_habilidad: int = 0

    def xp_para_siguiente(self) -> int:
        return self.nivel * 100

    def ganar_xp(self, cantidad: int) -> list[str]:
        entero_entre(cantidad, 0, 100_000, "Experiencia")
        mensajes: list[str] = []
        self.experiencia += cantidad
        while self.experiencia >= self.xp_para_siguiente() and self.nivel < 100:
            self.experiencia -= self.xp_para_siguiente()
            self.nivel += 1
            self.puntos_habilidad += 1
            mensajes.append(f"Sube al nivel {self.nivel}.")
        return mensajes

    def aprender(self, habilidad: Habilidad | str) -> None:
        habilidad = Habilidad(habilidad)
        if habilidad in self.habilidades:
            return
        if self.puntos_habilidad <= 0:
            raise ValueError("No quedan puntos de habilidad")
        self.habilidades.add(habilidad)
        self.puntos_habilidad -= 1

    def bonificador(self, habilidad: Habilidad | str) -> float:
        habilidad = Habilidad(habilidad)
        return 1.0 + (0.10 if habilidad in self.habilidades else 0.0)

    def to_dict(self) -> dict:
        return {
            "nivel": self.nivel,
            "experiencia": self.experiencia,
            "habilidades": sorted(h.value for h in self.habilidades),
            "puntos_habilidad": self.puntos_habilidad,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgresionPersonaje":
        return cls(
            nivel=int(data.get("nivel", 1)),
            experiencia=int(data.get("experiencia", 0)),
            habilidades={Habilidad(h) for h in data.get("habilidades", [])},
            puntos_habilidad=int(data.get("puntos_habilidad", 0)),
        )


@dataclass(slots=True)
class MisionCampania:
    codigo: str
    titulo: str
    descripcion: str
    completada: bool = False
    recompensa_xp: int = 50

    def completar(self, progresion: ProgresionPersonaje | None = None) -> list[str]:
        if self.completada:
            return []
        self.completada = True
        mensajes = [f"Mision completada: {self.titulo}."]
        if progresion:
            mensajes.extend(progresion.ganar_xp(self.recompensa_xp))
        return mensajes


@dataclass(slots=True)
class Campania:
    misiones: list[MisionCampania] = field(default_factory=lambda: [
        MisionCampania("evacuar", "Evacuacion", "Alcanza la salida.", recompensa_xp=50),
        MisionCampania("limpiar", "Zona segura", "Neutraliza los enemigos.", recompensa_xp=75),
        MisionCampania("rescate", "Nadie queda atras", "Evacua con aliados vivos.", recompensa_xp=100),
    ])
    indice: int = 0

    @property
    def actual(self) -> MisionCampania | None:
        if 0 <= self.indice < len(self.misiones):
            return self.misiones[self.indice]
        return None

    def avanzar_si_completada(self) -> bool:
        if self.actual and self.actual.completada:
            self.indice += 1
            return True
        return False

    @property
    def finalizada(self) -> bool:
        return self.indice >= len(self.misiones)
