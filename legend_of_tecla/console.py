"""Adaptadores de consola desacoplados del motor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .commands import ParserComandos


Entrada = Callable[[str], str]
Salida = Callable[[str], None]


@dataclass(slots=True)
class ConsolaJuego:
    parser: ParserComandos = field(default_factory=ParserComandos)
    entrada: Entrada = input
    salida: Salida = print
    prompt: str = "> "

    def ejecutar_lineas(self, motor, lineas: Iterable[str]) -> list[str]:
        respuestas: list[str] = []
        for linea in lineas:
            comando = self.parser.parse(linea)
            respuesta = comando.ejecutar(motor)
            respuestas.append(respuesta)
        return respuestas

    def bucle(self, motor) -> None:
        self.salida("The Legend of Tecla - consola")
        while True:
            linea = self.entrada(self.prompt)
            if linea.strip().lower() in {"salir", "exit", "quit"}:
                self.salida("Fin de la partida.")
                return
            try:
                comando = self.parser.parse(linea)
                self.salida(comando.ejecutar(motor))
            except Exception as exc:
                self.salida(f"Error: {exc}")
