"""Excepciones de dominio equivalentes al paquete ``exceptions`` del Java.

El proyecto original distingue entre errores de accion del jugador, carga de datos,
estado invalido del motor y errores de configuracion. Mantener excepciones propias
facilita que la consola, la GUI y los tests no dependan de ``ValueError`` genericos.
"""
from __future__ import annotations


class TeclaError(Exception):
    """Raiz de las excepciones controladas del juego."""


class AccionInvalidaError(TeclaError):
    """Una accion del jugador no puede ejecutarse en el estado actual."""


class EnergiaInsuficienteError(AccionInvalidaError):
    """El personaje no tiene energia suficiente para la accion solicitada."""


class InventarioError(AccionInvalidaError):
    """Operacion invalida sobre mochila, inventario o equipamiento."""


class MovimientoInvalidoError(AccionInvalidaError):
    """Movimiento fuera del mapa, bloqueado o tacticamente imposible."""


class CargaDatosError(TeclaError):
    """Los ficheros de escenario o configuracion no son validos."""


class ConfiguracionError(TeclaError):
    """La configuracion de partida contiene valores incompatibles."""


class EstadoJuegoError(TeclaError):
    """El motor ha detectado un estado interno inconsistente."""


class PersistenciaError(TeclaError):
    """Guardado, carga o replay no se pudo completar de forma segura."""


# Alias con nombres cercanos al Java para facilitar la lectura cruzada.
AccionInvalidaException = AccionInvalidaError
CargaDatosException = CargaDatosError
EstadoJuegoException = EstadoJuegoError
