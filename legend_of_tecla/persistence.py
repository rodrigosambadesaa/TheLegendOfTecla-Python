"""Persistencia versionada de partidas y perfiles."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import DEFAULTS
from .exceptions import CargaDatosError


@dataclass(frozen=True, slots=True)
class SaveMetadata:
    version: int = DEFAULTS.version_save
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def now(cls) -> "SaveMetadata":
        stamp = datetime.now(timezone.utc).isoformat()
        return cls(created_at=stamp, updated_at=stamp)

    def touched(self) -> "SaveMetadata":
        created = self.created_at or datetime.now(timezone.utc).isoformat()
        return SaveMetadata(self.version, created, datetime.now(timezone.utc).isoformat())


@dataclass(slots=True)
class SaveGame:
    metadata: SaveMetadata
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": {
                "version": self.metadata.version,
                "created_at": self.metadata.created_at,
                "updated_at": self.metadata.updated_at,
            },
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SaveGame":
        meta = data.get("metadata", {})
        version = int(meta.get("version", data.get("version", 1)))
        if version > DEFAULTS.version_save:
            raise CargaDatosError(f"Savegame de version futura: {version}")
        return cls(
            SaveMetadata(version, str(meta.get("created_at", "")), str(meta.get("updated_at", ""))),
            dict(data.get("payload", data.get("game", data))),
        )


def guardar_save(payload: dict[str, Any], path: str | Path, metadata: SaveMetadata | None = None) -> None:
    ruta = Path(path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    save = SaveGame((metadata or SaveMetadata.now()).touched(), payload)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(save.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ruta)


def cargar_save(path: str | Path) -> SaveGame:
    ruta = Path(path)
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CargaDatosError(f"No se pudo cargar la partida {ruta}") from exc
    return SaveGame.from_dict(data)


@dataclass(slots=True)
class GestorBackups:
    carpeta: Path
    max_backups: int = 5

    def crear_backup(self, save_path: str | Path) -> Path:
        origen = Path(save_path)
        if not origen.exists():
            raise FileNotFoundError(origen)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        destino = self.carpeta / f"{origen.stem}-{stamp}{origen.suffix}"
        shutil.copy2(origen, destino)
        self._purgar(origen.stem)
        return destino

    def _purgar(self, stem: str) -> None:
        backups = sorted(self.carpeta.glob(f"{stem}-*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for backup in backups[self.max_backups:]:
            backup.unlink(missing_ok=True)
