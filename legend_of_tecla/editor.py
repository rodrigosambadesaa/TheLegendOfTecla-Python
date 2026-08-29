"""Editor de escenarios JSON para The Legend of Tecla.

Incluye dos capas:
- funciones puras para crear, modificar, guardar y cargar escenarios;
- una GUI Tkinter sencilla para pintar mapas sin tocar JSON a mano.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import Position
from .world import InteractiveElement, InteractiveState, InteractiveType, MapGrid


BRUSHES = {
    "suelo",
    "muro",
    "inicio",
    "objetivo",
    "oscura",
    "madera",
    "antorcha",
    "fuente",
    "fuego",
    "puerta",
    "trampa",
    "terminal",
    "interruptor",
    "limpiar_elemento",
}


@dataclass(slots=True)
class EditorState:
    grid: MapGrid
    selected_brush: str = "suelo"


def make_blank_scenario(rows: int = 10, cols: int = 14) -> MapGrid:
    if rows < 2 or cols < 2:
        raise ValueError("el escenario necesita al menos 2x2 celdas")
    return MapGrid(rows, cols, Position(0, 0), Position(rows - 1, cols - 1))


def apply_brush(grid: MapGrid, pos: Position, brush: str) -> None:
    """Aplica una herramienta de edición a una celda."""
    if brush not in BRUSHES:
        raise ValueError(f"herramienta desconocida: {brush}")
    grid.validate_position(pos)
    cell = grid.cell(pos)

    if brush == "suelo":
        cell.walkable = True
    elif brush == "muro":
        if pos in {grid.start, grid.goal}:
            raise ValueError("inicio y objetivo no pueden ser muro")
        cell.walkable = False
    elif brush == "inicio":
        if not cell.walkable:
            cell.walkable = True
        grid.start = pos
    elif brush == "objetivo":
        if not cell.walkable:
            cell.walkable = True
        grid.goal = pos
    elif brush == "oscura":
        cell.dark = not cell.dark
    elif brush == "madera":
        cell.wood = not cell.wood
    elif brush == "antorcha":
        cell.wall_torch = not cell.wall_torch
    elif brush == "fuente":
        cell.water_source = not cell.water_source
    elif brush == "fuego":
        cell.fire = 0 if cell.fire else 3
    elif brush == "puerta":
        cell.walkable = True
        cell.element = InteractiveElement(InteractiveType.DOOR, "puerta", InteractiveState.CLOSED)
    elif brush == "trampa":
        cell.walkable = True
        cell.element = InteractiveElement(InteractiveType.TRAP, "trampa", InteractiveState.ARMED, difficulty=5)
    elif brush == "terminal":
        cell.walkable = True
        cell.element = InteractiveElement(InteractiveType.TERMINAL, "terminal", InteractiveState.INACTIVE, difficulty=5)
    elif brush == "interruptor":
        cell.walkable = True
        cell.element = InteractiveElement(InteractiveType.SWITCH, "interruptor", InteractiveState.INACTIVE)
    elif brush == "limpiar_elemento":
        cell.element = InteractiveElement()


def scenario_document(grid: MapGrid, con_aliados: bool = False) -> dict:
    return {
        "nombre": "Escenario editado",
        "conAliados": con_aliados,
        "mapa": grid.to_dict(),
    }


def save_scenario(grid: MapGrid, path: Path, con_aliados: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario_document(grid, con_aliados), ensure_ascii=False, indent=2), encoding="utf-8")


def load_editor_scenario(path: Path) -> MapGrid:
    data = json.loads(path.read_text(encoding="utf-8"))
    return MapGrid.from_dict(data.get("mapa", data))


def _load_tk():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception as exc:  # pragma: no cover - depende del sistema gráfico
        raise RuntimeError(
            "El editor necesita Tkinter y un entorno de escritorio. "
            "En Debian/Ubuntu instala python3-tk."
        ) from exc
    return tk, ttk, filedialog, messagebox


class ScenarioEditor:
    def __init__(self, grid: MapGrid | None = None):
        tk, ttk, filedialog, messagebox = _load_tk()
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.state = EditorState(grid or make_blank_scenario())
        self.root = tk.Tk()
        self.root.title("Editor de escenarios - The Legend of Tecla Python")
        self.root.geometry("980x720")
        self.cell_size = 32
        self._build()
        self.draw()

    def _build(self) -> None:
        tk = self.tk
        ttk = self.ttk
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(container)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Nuevo", command=self.new_map).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Abrir…", command=self.open_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Guardar…", command=self.save_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Validar ruta", command=self.validate_route).pack(side=tk.LEFT, padx=2)

        body = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=8)
        body.add(left, weight=4)
        body.add(right, weight=1)

        self.canvas = tk.Canvas(left, background="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

        self.brush_var = tk.StringVar(value=self.state.selected_brush)
        for brush in sorted(BRUSHES):
            ttk.Radiobutton(
                right,
                text=brush,
                value=brush,
                variable=self.brush_var,
                command=self.set_brush,
            ).pack(anchor="w")

        self.info_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.info_var, wraplength=240).pack(fill=tk.X, pady=(12, 0))

    def set_brush(self) -> None:
        self.state.selected_brush = self.brush_var.get()

    def on_click(self, event) -> None:
        row = event.y // self.cell_size
        col = event.x // self.cell_size
        pos = Position(row, col)
        if not self.state.grid.inside(pos):
            return
        try:
            apply_brush(self.state.grid, pos, self.state.selected_brush)
            self.info_var.set(f"{self.state.selected_brush} aplicado en {row},{col}")
        except ValueError as exc:
            self.messagebox.showerror("Edición inválida", str(exc))
        self.draw()

    def draw(self) -> None:
        grid = self.state.grid
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, grid.cols * self.cell_size, grid.rows * self.cell_size))
        colors = {
            "#": "#222222",
            ".": "#f8f8f8",
            "?": "#777777",
            "=": "#d7b98e",
            "T": "#ffd27a",
            "U": "#9dd7ff",
            "F": "#ff9a66",
            "+": "#a46a3f",
            "^": "#d97a7a",
            "X": "#98e08d",
        }
        for row in range(grid.rows):
            for col in range(grid.cols):
                pos = Position(row, col)
                cell = grid.cell(pos)
                symbol = "X" if pos == grid.goal else cell.symbol(True, True)
                if pos == grid.start:
                    symbol = "J"
                color = "#b7e1ff" if symbol == "J" else colors.get(symbol, "#f8f8f8")
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#999999")
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=symbol, font=("Consolas", 12, "bold"))

    def new_map(self) -> None:
        self.state.grid = make_blank_scenario()
        self.draw()

    def open_dialog(self) -> None:
        path = self.filedialog.askopenfilename(
            title="Abrir escenario JSON",
            filetypes=[("Escenario JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.state.grid = load_editor_scenario(Path(path))
            self.draw()

    def save_dialog(self) -> None:
        path = self.filedialog.asksaveasfilename(
            title="Guardar escenario JSON",
            defaultextension=".json",
            filetypes=[("Escenario JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if path:
            save_scenario(self.state.grid, Path(path))
            self.messagebox.showinfo("Escenario guardado", path)

    def validate_route(self) -> None:
        path = self.state.grid.shortest_path(self.state.grid.start, self.state.grid.goal)
        if path:
            self.info_var.set(f"Ruta válida: {len(path)} pasos.")
        else:
            self.info_var.set("No hay ruta transitable entre inicio y objetivo.")

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_editor(path: Path | None = None) -> int:
    grid = load_editor_scenario(path) if path else None
    return ScenarioEditor(grid).run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Editor de escenarios JSON para The Legend of Tecla")
    parser.add_argument("archivo", nargs="?", type=Path, help="Escenario JSON opcional para abrir")
    parser.add_argument("--crear", type=Path, help="Crea un escenario vacío sin abrir GUI")
    parser.add_argument("--filas", type=int, default=10)
    parser.add_argument("--columnas", type=int, default=14)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.crear:
        save_scenario(make_blank_scenario(args.filas, args.columnas), args.crear)
        print(f"Escenario creado en {args.crear}")
        return 0
    return run_editor(args.archivo)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
