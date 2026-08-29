"""Sesion de ejecucion de alto nivel.

Une comandos parseables, fachada de aplicacion, audio observable e historial de
acciones. Es el punto de entrada recomendado para CLI/GUI/replays porque evita
que cada interfaz hable directamente con ``Game.execute``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .audio import AudioNulo, ServicioAudio
from .commands import Comando, ComandoLanzarExplosivo, RegistroComandos
from .exceptions import TeclaError
from .facade import cargar_partida, guardar_partida, sincronizar_logros
from .game import Game


@dataclass(slots=True)
class EntradaHistorial:
    turno: int
    comando: str
    normalizado: str
    salida: str


@dataclass(slots=True)
class SesionJuego:
    """Orquesta una partida con servicios externos al motor."""

    game: Game
    comandos: RegistroComandos = field(default_factory=RegistroComandos)
    audio: ServicioAudio = field(default_factory=AudioNulo)
    historial: list[EntradaHistorial] = field(default_factory=list)

    def ejecutar(self, texto: str) -> str:
        """Parsea, normaliza, ejecuta, sincroniza logros y registra historial."""

        try:
            comando = self.comandos.parsear(texto)
            normalizado = self._normalizar_para_motor(comando)
            salida = self.game.execute(normalizado)
            desbloqueados = sincronizar_logros(self.game)
            if desbloqueados:
                self.audio.reproducir("logro")
                salida += "\n" + "\n".join(f"Logro ampliado: {logro.title}" for logro in desbloqueados)
            else:
                self._audio_para_comando(comando)
        except TeclaError as exc:
            salida = f"Error: {exc}"
            normalizado = texto.strip()
            self.audio.reproducir("error")
        self.historial.append(EntradaHistorial(self.game.statistics.turns, texto, normalizado, salida))
        return salida

    def guardar(self, path: str | Path) -> None:
        guardar_partida(self.game, path)
        self.audio.reproducir("guardar")

    def cargar(self, path: str | Path) -> None:
        self.game = cargar_partida(path)
        self.audio.reproducir("cargar")

    def render(self) -> str:
        return self.game.render()

    def estado(self) -> str:
        return self.game.status()

    def eventos(self, limit: int = 8) -> str:
        return self.game.bus.drain_text(limit)

    def _normalizar_para_motor(self, comando: Comando) -> str:
        # El CommandDispatcher historico de game.py acepta ``lanzar norte``;
        # ParserComandos conserva tambien el nombre del explosivo. Adaptamos
        # aqui sin tocar el motor estable.
        if isinstance(comando, ComandoLanzarExplosivo) and comando.direccion is not None:
            return f"lanzar {comando.direccion.value[2]}"
        return comando.serializar()

    def _audio_para_comando(self, comando: Comando) -> None:
        if comando.nombre in {"atacar", "lanzar"}:
            self.audio.reproducir("combate")
        elif comando.nombre in {"mover", "recoger", "usar", "equipar"}:
            self.audio.reproducir(comando.nombre)
        if self.game.finished:
            self.audio.reproducir("victoria" if self.game.victory else "derrota")


__all__ = ["EntradaHistorial", "SesionJuego"]
