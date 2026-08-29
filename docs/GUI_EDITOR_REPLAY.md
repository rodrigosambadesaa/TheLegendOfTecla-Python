# GUI, editor y replay

## GUI táctica

La GUI se encuentra en `legend_of_tecla.gui` y se abre con:

```bash
python -m legend_of_tecla --gui
```

Características:

- mapa ASCII en una zona monoespaciada;
- panel de estado del jugador y aliados;
- botones de movimiento, ataque, inspección, descanso, ayuda, recarga, logros y estadísticas;
- entrada libre de comandos, por lo que cualquier comando soportado por el motor funciona también en GUI;
- guardar/cargar savegames JSON.

La decisión de diseño es importante: la ventana no duplica reglas, solo ejecuta comandos sobre `Game.execute()`. Así, la consola, la GUI y los tests comparten el mismo núcleo.

## Editor de escenarios

El editor se encuentra en `legend_of_tecla.editor`:

```bash
python -m legend_of_tecla --editor
```

También puede crear escenarios en modo headless:

```bash
tecla-editor --crear data/mi_escenario/escenario.json --filas 12 --columnas 20
```

Herramientas incluidas:

- suelo;
- muro;
- inicio;
- objetivo;
- oscuridad;
- madera;
- antorcha mural;
- fuente;
- fuego;
- puerta;
- trampa;
- terminal;
- interruptor;
- limpiar elemento.

El resultado se guarda como JSON compatible con:

```bash
python -m legend_of_tecla --modo ficheros --datos data/mi_escenario
```

## Replay determinista

El módulo `legend_of_tecla.replay` graba:

- configuración inicial;
- comandos ejecutados;
- SHA-256 inicial;
- SHA-256 final;
- salidas textuales de cada comando.

Ejemplo:

```bash
tecla-replay grabar replays/demo.json "inspeccionar" "mover este" "estado"
tecla-replay validar replays/demo.json
```

El replay se considera válido si el estado inicial esperado coincide y, tras repetir los comandos, el estado final tiene el mismo SHA-256.

## Validación automatizada

La suite cubre:

- creación y renderizado del juego;
- movimiento, recogida, equipamiento y combate;
- guardado/carga;
- escenarios TXT y JSON;
- reproducibilidad procedural;
- escalado de aliados/enemigos;
- crafting;
- rechazo de savegames corruptos;
- herramientas del editor;
- replays válidos y manipulados.
