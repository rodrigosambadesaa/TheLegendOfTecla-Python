"""Validaciones y limites de dominio.

Equivale al papel de ``validation.Validaciones`` y ``validation.Limites`` en el
repo Java: concentrar precondiciones, limites numericos y mensajes de error para
que las clases del modelo no repitan comprobaciones ad hoc.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from .exceptions import ConfiguracionError, CargaDatosError

T = TypeVar("T")


@dataclass(frozen=True)
class Limites:
    """Constantes de seguridad y equilibrio usadas por el dominio."""

    TEXTO_CORTO: int = 80
    TEXTO_MEDIO: int = 500
    ESTADISTICA: int = 10_000
    FILAS_MAXIMAS: int = 300
    COLUMNAS_MAXIMAS: int = 300
    PESO_MAXIMO_OBJETO: int = 1_000
    CAPACIDAD_MAXIMA: int = 10_000
    TURNOS_MAXIMOS_EFECTO: int = 10_000


LIMITES = Limites()


def no_nulo(valor: T | None, nombre: str) -> T:
    if valor is None:
        raise ConfiguracionError(f"{nombre} no puede ser nulo.")
    return valor


def texto_obligatorio(valor: str | None, nombre: str, maximo: int = LIMITES.TEXTO_CORTO) -> str:
    if valor is None:
        raise ConfiguracionError(f"{nombre} es obligatorio.")
    normalizado = valor.strip()
    if not normalizado:
        raise ConfiguracionError(f"{nombre} no puede estar vacio.")
    if len(normalizado) > maximo:
        raise ConfiguracionError(f"{nombre} supera el maximo de {maximo} caracteres.")
    return normalizado


def entero_entre(valor: int, minimo: int, maximo: int, nombre: str) -> int:
    if not isinstance(valor, int):
        raise ConfiguracionError(f"{nombre} debe ser entero.")
    if valor < minimo or valor > maximo:
        raise ConfiguracionError(f"{nombre} debe estar entre {minimo} y {maximo}.")
    return valor


def decimal_entre(valor: float, minimo: float, maximo: float, nombre: str) -> float:
    numero = float(valor)
    if numero < minimo or numero > maximo:
        raise ConfiguracionError(f"{nombre} debe estar entre {minimo} y {maximo}.")
    return numero


def secuencia_no_vacia(valores: Sequence[T], nombre: str) -> Sequence[T]:
    no_nulo(valores, nombre)
    if len(valores) == 0:
        raise ConfiguracionError(f"{nombre} no puede estar vacia.")
    return valores


def sin_nulos(valores: Iterable[T | None], nombre: str) -> list[T]:
    resultado: list[T] = []
    for indice, valor in enumerate(valores):
        if valor is None:
            raise ConfiguracionError(f"{nombre} contiene un valor nulo en la posicion {indice}.")
        resultado.append(valor)
    return resultado


def validar_matriz_rectangular(lineas: Sequence[str]) -> tuple[int, int]:
    """Valida un mapa textual y devuelve ``(filas, columnas)``."""

    if not lineas:
        raise CargaDatosError("El mapa no puede estar vacio.")
    ancho = len(lineas[0])
    if ancho == 0:
        raise CargaDatosError("El mapa debe tener al menos una columna.")
    for indice, linea in enumerate(lineas, start=1):
        if len(linea) != ancho:
            raise CargaDatosError(
                f"El mapa no es rectangular: linea {indice} mide {len(linea)} y se esperaba {ancho}."
            )
    entero_entre(len(lineas), 1, LIMITES.FILAS_MAXIMAS, "Filas del mapa")
    entero_entre(ancho, 1, LIMITES.COLUMNAS_MAXIMAS, "Columnas del mapa")
    return len(lineas), ancho


class Validaciones:
    """Fachada con nombres similares a la clase Java ``Validaciones``."""

    no_nulo = staticmethod(no_nulo)
    texto_obligatorio = staticmethod(texto_obligatorio)
    entero_entre = staticmethod(entero_entre)
    decimal_entre = staticmethod(decimal_entre)
    secuencia_no_vacia = staticmethod(secuencia_no_vacia)
    sin_nulos = staticmethod(sin_nulos)
    validar_matriz_rectangular = staticmethod(validar_matriz_rectangular)
