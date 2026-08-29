"""Auditoria de cierre de paridad arquitectonica.

No pretende afirmar que el codigo Python sea una copia linea a linea del Java,
sino verificar que todos los paquetes funcionales relevantes del repo original
tienen un equivalente Python importable, testeable y conectado por fachada o
runtime cuando procede.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EquivalenciaModulo:
    paquete_java: str
    modulo_python: str
    responsabilidad: str
    simbolos_requeridos: tuple[str, ...] = ()


EQUIVALENCIAS: tuple[EquivalenciaModulo, ...] = (
    EquivalenciaModulo("achievements", "legend_of_tecla.achievements", "logros y reglas desbloqueables", ("RegistroLogros",)),
    EquivalenciaModulo("ai", "legend_of_tecla.ai", "controladores y estrategias IA", ("ControladorIA",)),
    EquivalenciaModulo("audio", "legend_of_tecla.audio", "servicio de audio sustituible", ("AudioNulo",)),
    EquivalenciaModulo("commands", "legend_of_tecla.commands", "patron Command y parser", ("ParserComandos", "RegistroComandos")),
    EquivalenciaModulo("config", "legend_of_tecla.config", "configuracion externa", ("ConfiguracionJuego",)),
    EquivalenciaModulo("console", "legend_of_tecla.console", "adaptador consola", ("ConsolaTexto",)),
    EquivalenciaModulo("constants", "legend_of_tecla.constants", "constantes y simbolos", ("DEFAULTS",)),
    EquivalenciaModulo("effects", "legend_of_tecla.effects", "estados alterados", ("GestorEstados",)),
    EquivalenciaModulo("engine", "legend_of_tecla.engine", "sistemas desacoplados de motor", ("SistemaMovimiento", "SistemaCombate")),
    EquivalenciaModulo("events", "legend_of_tecla.events", "bus y registro de eventos", ("BusEventos",)),
    EquivalenciaModulo("exceptions", "legend_of_tecla.exceptions", "excepciones de dominio", ("TeclaError",)),
    EquivalenciaModulo("gui", "legend_of_tecla.gui", "interfaz grafica Tkinter", ("run_gui",)),
    EquivalenciaModulo("inventory", "legend_of_tecla.inventory", "mochila y equipamiento", ("Mochila", "Equipamiento")),
    EquivalenciaModulo("io", "legend_of_tecla.io", "carga/exportacion escenarios", ("cargar_escenario",)),
    EquivalenciaModulo("model", "legend_of_tecla.model", "modelo de dominio", ("Character", "Player", "Enemy")),
    EquivalenciaModulo("model.characters", "legend_of_tecla.hierarchy", "jerarquia POO canonica", ("Marine", "Francotirador", "Zapador")),
    EquivalenciaModulo("model.items", "legend_of_tecla.hierarchy", "objetos tipados", ("Arma", "Botiquin", "Credencial")),
    EquivalenciaModulo("model.world", "legend_of_tecla.world", "mapa, celdas y elementos", ("MapGrid", "Cell")),
    EquivalenciaModulo("persistence", "legend_of_tecla.persistence", "savegames versionados", ("guardar_save", "cargar_save")),
    EquivalenciaModulo("progression", "legend_of_tecla.progression", "niveles, xp y campana", ("ProgresionPersonaje",)),
    EquivalenciaModulo("validation", "legend_of_tecla.validation", "validaciones y limites", ("Validaciones",)),
    EquivalenciaModulo("runtime", "legend_of_tecla.runtime", "sesion orquestadora CLI/GUI/replay", ("SesionJuego",)),
    EquivalenciaModulo("application facade", "legend_of_tecla.facade", "integracion config/io/persistence/logros", ("crear_partida", "guardar_partida", "cargar_partida")),
)


def auditoria_paridad() -> dict[str, list[str]]:
    """Devuelve un informe con modulos correctos y pendientes detectados."""

    correctos: list[str] = []
    pendientes: list[str] = []
    for equivalencia in EQUIVALENCIAS:
        try:
            modulo = importlib.import_module(equivalencia.modulo_python)
        except Exception as exc:  # pragma: no cover - fallo explicitado por tests
            pendientes.append(f"{equivalencia.paquete_java}: no importa {equivalencia.modulo_python}: {exc}")
            continue
        faltan = [simbolo for simbolo in equivalencia.simbolos_requeridos if not hasattr(modulo, simbolo)]
        if faltan:
            pendientes.append(f"{equivalencia.paquete_java}: faltan simbolos {', '.join(faltan)}")
        else:
            correctos.append(equivalencia.paquete_java)
    return {"correctos": correctos, "pendientes": pendientes}


def paridad_cerrada() -> bool:
    return not auditoria_paridad()["pendientes"]


__all__ = ["EQUIVALENCIAS", "EquivalenciaModulo", "auditoria_paridad", "paridad_cerrada"]
