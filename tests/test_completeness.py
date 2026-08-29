from legend_of_tecla.completeness import EQUIVALENCIAS, auditoria_paridad, paridad_cerrada


def test_parity_audit_has_no_pending_modules():
    informe = auditoria_paridad()

    assert informe["pendientes"] == []
    assert paridad_cerrada() is True
    assert len(informe["correctos"]) == len(EQUIVALENCIAS)


def test_parity_audit_covers_core_original_package_families():
    paquetes = {equivalencia.paquete_java for equivalencia in EQUIVALENCIAS}

    assert {
        "achievements",
        "ai",
        "audio",
        "commands",
        "config",
        "console",
        "constants",
        "effects",
        "engine",
        "events",
        "exceptions",
        "gui",
        "inventory",
        "io",
        "model",
        "model.characters",
        "model.items",
        "model.world",
        "persistence",
        "progression",
        "validation",
        "runtime",
        "application facade",
    } <= paquetes
