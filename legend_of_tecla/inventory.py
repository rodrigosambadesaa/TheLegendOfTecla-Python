"""Inventario y reglas de equipamiento.

Complementa la clase ligera ``Character.inventory`` con servicios de mochila
similares a los del Java original: capacidad, busqueda, apilado simple,
equipamiento y transferencia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .exceptions import AccionInvalidaError
from .model import Item, ItemType


class ResultadoInventario(str, Enum):
    ANADIDO = "anadido"
    RETIRADO = "retirado"
    EQUIPADO = "equipado"
    USADO = "usado"


@dataclass(slots=True)
class EntradaInventario:
    item: Item
    cantidad: int = 1

    def __post_init__(self) -> None:
        if self.cantidad < 1:
            raise ValueError("La cantidad debe ser positiva")

    @property
    def peso_total(self) -> int:
        return self.item.weight * self.cantidad


@dataclass(slots=True)
class Mochila:
    capacidad: int
    entradas: list[EntradaInventario] = field(default_factory=list)

    @property
    def peso(self) -> int:
        return sum(entrada.peso_total for entrada in self.entradas)

    @property
    def libre(self) -> int:
        return self.capacidad - self.peso

    def objetos(self) -> list[Item]:
        salida: list[Item] = []
        for entrada in self.entradas:
            salida.extend(entrada.item.clone() for _ in range(entrada.cantidad))
        return salida

    def puede_anadir(self, item: Item, cantidad: int = 1) -> bool:
        return self.peso + item.weight * cantidad <= self.capacidad

    def anadir(self, item: Item, cantidad: int = 1) -> ResultadoInventario:
        if cantidad < 1:
            raise AccionInvalidaError("La cantidad debe ser positiva")
        if not self.puede_anadir(item, cantidad):
            raise AccionInvalidaError("La mochila no tiene capacidad suficiente")
        entrada = self.buscar_entrada(item.name)
        if entrada and entrada.item.item_type is item.item_type and item.item_type is not ItemType.WEAPON:
            entrada.cantidad += cantidad
        else:
            self.entradas.append(EntradaInventario(item.clone(), cantidad))
        return ResultadoInventario.ANADIDO

    def buscar_entrada(self, nombre: str) -> EntradaInventario | None:
        normalizado = nombre.strip().lower()
        return next((entrada for entrada in self.entradas if entrada.item.name.lower() == normalizado), None)

    def contiene(self, nombre: str) -> bool:
        return self.buscar_entrada(nombre) is not None

    def retirar(self, nombre: str, cantidad: int = 1) -> Item:
        if cantidad < 1:
            raise AccionInvalidaError("La cantidad debe ser positiva")
        entrada = self.buscar_entrada(nombre)
        if entrada is None or entrada.cantidad < cantidad:
            raise AccionInvalidaError(f"No hay suficientes unidades de {nombre}")
        entrada.cantidad -= cantidad
        item = entrada.item.clone()
        if entrada.cantidad == 0:
            self.entradas.remove(entrada)
        return item

    def transferir_a(self, destino: "Mochila", nombre: str, cantidad: int = 1) -> None:
        item = self.retirar(nombre, cantidad)
        try:
            destino.anadir(item, cantidad)
        except Exception:
            self.anadir(item, cantidad)
            raise


@dataclass(slots=True)
class Equipamiento:
    arma_principal: Item | None = None
    arma_secundaria: Item | None = None
    armadura: Item | None = None
    binocular: Item | None = None
    linterna: Item | None = None

    def equipar(self, item: Item) -> ResultadoInventario:
        if item.item_type is ItemType.WEAPON:
            if self.arma_principal is None:
                self.arma_principal = item
            else:
                self.arma_secundaria = item
            return ResultadoInventario.EQUIPADO
        if item.item_type is ItemType.ARMOR:
            self.armadura = item
            return ResultadoInventario.EQUIPADO
        if item.item_type is ItemType.LANTERN:
            self.linterna = item
            return ResultadoInventario.EQUIPADO
        if item.name.lower().startswith("binocular"):
            self.binocular = item
            return ResultadoInventario.EQUIPADO
        raise AccionInvalidaError(f"{item.name} no se puede equipar")

    @property
    def defensa(self) -> int:
        return self.armadura.value if self.armadura else 0

    @property
    def danio(self) -> int:
        return sum(item.value for item in (self.arma_principal, self.arma_secundaria) if item)
