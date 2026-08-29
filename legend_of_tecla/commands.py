"""Capa de comandos.

El repo Java tiene un paquete ``commands`` con clases por accion. Este modulo
lleva ese patron a Python: comandos parseables, ejecutables y testeables sin
atar el dominio a la CLI textual.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .exceptions import AccionInvalidaError
from .model import Direction


class JuegoCompatible(Protocol):
    def execute(self, raw: str) -> str: ...


@dataclass(frozen=True, slots=True)
class Comando:
    nombre: str
    argumentos: tuple[str, ...] = ()

    def ejecutar(self, juego: JuegoCompatible) -> str:
        texto = " ".join((self.nombre, *self.argumentos)).strip()
        return juego.execute(texto)

    def serializar(self) -> str:
        return " ".join((self.nombre, *self.argumentos)).strip()


@dataclass(frozen=True, slots=True)
class ComandoMover(Comando):
    direccion: Direction | None = None

    def __init__(self, direccion: Direction) -> None:
        object.__setattr__(self, "nombre", "mover")
        object.__setattr__(self, "argumentos", (direccion.value[2],))
        object.__setattr__(self, "direccion", direccion)


@dataclass(frozen=True, slots=True)
class ComandoAtacar(Comando):
    direccion: Direction | None = None

    def __init__(self, direccion: Direction) -> None:
        object.__setattr__(self, "nombre", "atacar")
        object.__setattr__(self, "argumentos", (direccion.value[2],))
        object.__setattr__(self, "direccion", direccion)


@dataclass(frozen=True, slots=True)
class ComandoRecoger(Comando):
    def __init__(self) -> None:
        object.__setattr__(self, "nombre", "recoger")
        object.__setattr__(self, "argumentos", ())


@dataclass(frozen=True, slots=True)
class ComandoUsar(Comando):
    objeto: str = ""

    def __init__(self, objeto: str) -> None:
        object.__setattr__(self, "nombre", "usar")
        object.__setattr__(self, "argumentos", (objeto,))
        object.__setattr__(self, "objeto", objeto)


@dataclass(frozen=True, slots=True)
class ComandoEquipar(Comando):
    objeto: str = ""

    def __init__(self, objeto: str) -> None:
        object.__setattr__(self, "nombre", "equipar")
        object.__setattr__(self, "argumentos", (objeto,))
        object.__setattr__(self, "objeto", objeto)


@dataclass(frozen=True, slots=True)
class ComandoLanzarExplosivo(Comando):
    direccion: Direction | None = None

    def __init__(self, direccion: Direction, explosivo: str = "granada") -> None:
        object.__setattr__(self, "nombre", "lanzar")
        object.__setattr__(self, "argumentos", (explosivo, direccion.value[2]))
        object.__setattr__(self, "direccion", direccion)


class ParserComandos:
    """Parser pequeno, tolerante y compatible con la consola existente."""

    def parsear(self, texto: str) -> Comando:
        partes = texto.strip().split()
        if not partes:
            raise AccionInvalidaError("Comando vacio.")
        verbo = partes[0].lower()
        resto = tuple(partes[1:])
        if verbo in {"m", "mover"}:
            self._requiere(resto, verbo)
            return ComandoMover(Direction.parse(resto[0]))
        if verbo in {"a", "atacar"}:
            self._requiere(resto, verbo)
            return ComandoAtacar(Direction.parse(resto[0]))
        if verbo in {"r", "recoger", "coger"}:
            return ComandoRecoger()
        if verbo in {"usar", "u"}:
            self._requiere(resto, verbo)
            return ComandoUsar(" ".join(resto))
        if verbo in {"equipar", "e"}:
            self._requiere(resto, verbo)
            return ComandoEquipar(" ".join(resto))
        if verbo in {"lanzar", "granada"}:
            self._requiere(resto, verbo)
            if verbo == "granada":
                return ComandoLanzarExplosivo(Direction.parse(resto[0]))
            if len(resto) == 1:
                return ComandoLanzarExplosivo(Direction.parse(resto[0]))
            return ComandoLanzarExplosivo(Direction.parse(resto[-1]), " ".join(resto[:-1]))
        return Comando(verbo, resto)

    @staticmethod
    def _requiere(argumentos: tuple[str, ...], verbo: str) -> None:
        if not argumentos:
            raise AccionInvalidaError(f"El comando {verbo} requiere argumentos.")


class RegistroComandos:
    def __init__(self) -> None:
        self.parser = ParserComandos()

    def parsear(self, texto: str) -> Comando:
        return self.parser.parsear(texto)

    def ejecutar(self, juego: JuegoCompatible, texto: str) -> str:
        return self.parsear(texto).ejecutar(juego)
