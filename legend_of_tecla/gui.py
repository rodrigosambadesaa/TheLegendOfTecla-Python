"""Interfaz gráfica Tkinter para The Legend of Tecla.

La GUI es deliberadamente ligera: reutiliza el mismo motor de consola y envía
comandos de texto al núcleo. Así conserva compatibilidad con los comandos
históricos y permite probar la reimplementación Python sin duplicar reglas de
juego en la capa visual.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _load_tk():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception as exc:  # pragma: no cover - depende del sistema gráfico
        raise RuntimeError(
            "La GUI necesita Tkinter y un entorno de escritorio. "
            "En Debian/Ubuntu instala python3-tk; en Windows y macOS suele venir incluido."
        ) from exc
    return tk, ttk, filedialog, messagebox


class TacticalGUI:
    """Ventana táctica jugable basada en el motor `Game`.

    No replica Swing: reimplementa la experiencia como una ventana nativa Python
    con mapa ASCII, panel de estado, botones de acción y entrada de comandos.
    """

    def __init__(self, game):
        tk, ttk, filedialog, messagebox = _load_tk()
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.game = game
        self.root = tk.Tk()
        self.root.title("The Legend of Tecla - Python")
        self.root.geometry("1120x720")
        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        tk = self.tk
        ttk = self.ttk

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, padding=8)
        right = ttk.Frame(main, padding=8)
        main.add(left, weight=3)
        main.add(right, weight=2)

        self.map_text = tk.Text(left, width=80, height=38, font=("Consolas", 13), wrap="none")
        self.map_text.pack(fill=tk.BOTH, expand=True)

        command_bar = ttk.Frame(left)
        command_bar.pack(fill=tk.X, pady=(8, 0))
        self.command_var = tk.StringVar()
        entry = ttk.Entry(command_bar, textvariable=self.command_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", lambda _event: self.run_command())
        ttk.Button(command_bar, text="Ejecutar", command=self.run_command).pack(side=tk.LEFT, padx=(6, 0))

        self.status_text = tk.Text(right, width=52, height=12, font=("Consolas", 10), wrap="word")
        self.status_text.pack(fill=tk.X)

        buttons = ttk.LabelFrame(right, text="Acciones rápidas", padding=8)
        buttons.pack(fill=tk.X, pady=8)
        for row, actions in enumerate(
            (
                (("↑", "mover norte"), ("↓", "mover sur"), ("←", "mover oeste"), ("→", "mover este")),
                (("Recoger", "recoger"), ("Inspeccionar", "inspeccionar"), ("Estado", "estado"), ("Ayuda", "ayuda")),
                (("Atacar N", "atacar norte"), ("Atacar S", "atacar sur"), ("Atacar O", "atacar oeste"), ("Atacar E", "atacar este")),
                (("Descansar", "descansar"), ("Pedir ayuda", "pedir ayuda"), ("Reagrupar", "reagrupar defensiva"), ("Recargar", "recargar")),
                (("Logros", "logros"), ("Stats", "estadisticas"), ("Turbo", "turbo"), ("Recetas", "recetas")),
            )
        ):
            for col, (label, command) in enumerate(actions):
                ttk.Button(buttons, text=label, command=lambda c=command: self.run_command(c)).grid(
                    row=row, column=col, padx=2, pady=2, sticky="ew"
                )
        for col in range(4):
            buttons.columnconfigure(col, weight=1)

        file_frame = ttk.LabelFrame(right, text="Partida", padding=8)
        file_frame.pack(fill=tk.X, pady=8)
        ttk.Button(file_frame, text="Guardar…", command=self.save_dialog).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(file_frame, text="Cargar…", command=self.load_dialog).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(file_frame, text="Nueva", command=self.new_default_game).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.events_text = tk.Text(right, width=52, height=18, font=("Consolas", 10), wrap="word")
        self.events_text.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            right,
            text="Leyenda: J jugador · A aliado · E enemigo · X objetivo · o objeto · F fuego · ? oscuridad",
        ).pack(fill=tk.X, pady=(8, 0))

    def refresh(self) -> None:
        self._set_text(self.map_text, self.game.render())
        status = self.game.status()
        if self.game.allies:
            status += "\n\n" + self.game.allies_status()
        self._set_text(self.status_text, status)
        events = self.game.bus.drain_text(40) or "Sin eventos todavía."
        if self.game.finished:
            events += "\n\n" + ("VICTORIA HUMANA" if self.game.victory else "VICTORIA ENEMIGA")
        self._set_text(self.events_text, events)

    def _set_text(self, widget, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", self.tk.END)
        widget.insert(self.tk.END, text)
        widget.configure(state="disabled")

    def run_command(self, command: str | None = None) -> None:
        command = command if command is not None else self.command_var.get()
        command = command.strip()
        if not command:
            return
        self.command_var.set("")
        result = self.game.execute(command)
        self.game.bus.publish(self.game.statistics.turns, "gui", f"> {command}\n{result}")
        self.refresh()

    def save_dialog(self) -> None:
        from .game import save_game

        path = self.filedialog.asksaveasfilename(
            title="Guardar partida",
            defaultextension=".json",
            filetypes=[("Savegame JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        save_game(self.game, Path(path))
        self.messagebox.showinfo("Partida guardada", f"Guardado en:\n{path}")

    def load_dialog(self) -> None:
        from .game import load_game

        path = self.filedialog.askopenfilename(
            title="Cargar partida",
            filetypes=[("Savegame JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        self.game = load_game(Path(path))
        self.refresh()

    def new_default_game(self) -> None:
        from .game import GameConfig, create_game

        self.game = create_game(GameConfig())
        self.refresh()

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_gui(game) -> int:
    """Abre la GUI para una partida ya creada."""
    return TacticalGUI(game).run()


def main(argv: Iterable[str] | None = None) -> int:
    from .cli import build_parser, game_from_args

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_gui(game_from_args(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
