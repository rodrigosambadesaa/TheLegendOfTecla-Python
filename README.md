# The Legend of Tecla (Python)

Reimplementación en Python del repositorio Java [`TheLegendOfTecla`](https://github.com/rodrigosambadesaa/TheLegendOfTecla).

Esta versión conserva la orientación del proyecto original —POO, mapa ASCII, inventario, combate, enemigos, aliados, cargadores de escenarios, roguelike táctico y persistencia— pero usa una arquitectura Python idiomática basada en `dataclasses`, módulos pequeños y tests automatizados.

## Funcionalidades implementadas

- Mapa ASCII con celdas transitables/no transitables, objetivo, oscuridad, fuego, madera, antorchas murales y fuentes de agua.
- Jugador, aliados, enemigos, inventario con peso/capacidad, equipamiento, armaduras, armas y consumibles.
- Consola interactiva con comandos históricos y tácticos: `mover`, `recoger`, `usar`, `tirar`, `equipar`, `desequipar`, `atacar`, `descansar`, `lanzar`, `pedir ayuda`, `reagrupar`, `recargar`, `dar`, `pedir`, `intercambiar`, `abrir`, `cerrar`, `hackear`, `activar`, `inspeccionar`, `desactivar`, `recetas`, `fabricar`, `guardar`, `cargar`, `estadisticas`, `logros`.
- Modo `default`, modo `grande` con variantes deterministas, modo `procedural` reproducible con `--seed` y modo `ficheros` compatible con `escenario.json` o `mapa.txt`/`objetos.txt`.
- Aliados opcionales: ninguno, `auto` o cantidad exacta hasta 4.999. Uno de cada cuatro es médico.
- Condiciones de victoria `solo_jugador` y `jugador_y_aliados`.
- IA enemiga con memoria, ruido y estados de alerta básicos; coordinación distinta cuando hay escuadrón aliado.
- Catálogo de más de 30 armas, con alcance, daño, cargador, munición, penetración y botín rotatorio sin repetición hasta completar vuelta.
- Arsenal xeno exclusivo para enemigos: queda marcado como incompatible por `tags`.
- Daño ambiental, fuego propagable sobre madera, cubos de agua, trampas, puertas, terminales, interruptores, barricadas/cobertura como elementos de mapa.
- Estadísticas, logros, campaña/misiones ligeras y eventos deterministas.
- Savegames JSON versionados con validación de versión y rechazo de JSON corrupto.
- GUI táctica Tkinter que reutiliza el mismo motor de comandos.
- Editor Tkinter de escenarios JSON con herramientas de mapa y validación de ruta.
- Replays deterministas con validación SHA-256 del estado final.
- Tests unitarios de motor, comandos, persistencia, carga de escenarios, editor y replay.

## Ejecutar

```bash
python -m legend_of_tecla --rapido
```

Partida interactiva por defecto:

```bash
python -m legend_of_tecla
```

Mapa grande, variante 7, con aliados automáticos:

```bash
python -m legend_of_tecla --modo grande --variante 7 --aliados auto
```

Mapa procedural reproducible:

```bash
python -m legend_of_tecla --modo procedural --seed 12345 --dimensiones 18x28
```

Cargar escenario desde ficheros:

```bash
python -m legend_of_tecla --modo ficheros --datos data/escenario_basico
```

Guardar/cargar dentro de la partida:

```text
guardar savegame_tecla.json
cargar savegame_tecla.json
```

## GUI

Ventana jugable con mapa ASCII, estado, eventos, entrada de comandos y botones de acción:

```bash
python -m legend_of_tecla --gui
```

También está disponible como script instalable:

```bash
tecla-gui --modo grande --variante 3 --aliados auto
```

La GUI usa Tkinter. En Windows y macOS suele venir incluido. En Debian/Ubuntu puede requerir:

```bash
sudo apt install python3-tk
```

## Editor de escenarios

Abrir el editor gráfico:

```bash
python -m legend_of_tecla --editor
```

Crear un escenario JSON vacío sin abrir ventana:

```bash
tecla-editor --crear data/mi_escenario/escenario.json --filas 12 --columnas 20
```

El editor guarda JSON compatible con `--modo ficheros --datos <directorio>`.

## Replays

Grabar un replay mínimo:

```bash
tecla-replay grabar replays/demo.json "inspeccionar" "mover este" "estado"
```

Validarlo posteriormente:

```bash
tecla-replay validar replays/demo.json
```

El replay comprueba que el estado inicial y el estado final coinciden mediante SHA-256.

## Desarrollo

No hay dependencias de ejecución fuera de la biblioteca estándar. Para tests:

```bash
python -m pip install -e .[dev]
pytest
```

Calidad rápida:

```bash
python -m compileall legend_of_tecla
pytest -q
```

## Arquitectura

- `model.py`: entidades, objetos, estados, dificultad y condiciones de victoria.
- `world.py`: mapa, celdas, elementos interactivos y serialización.
- `catalog.py`: catálogo de objetos, armas, armaduras y recetas.
- `game.py`: motor, turnos, comandos, IA, guardado/carga y logros.
- `cli.py`: consola y argumentos.
- `gui.py`: ventana táctica Tkinter.
- `editor.py`: editor de escenarios JSON.
- `replay.py`: grabación y validación de partidas reproducibles.

## Diferencias deliberadas frente a Java

La GUI Swing/noVNC del repo Java no se replica como Swing; se reemplaza por una GUI nativa Tkinter que invoca el mismo motor de comandos. Esto mantiene la reimplementación portable y evita duplicar lógica de juego en la capa visual.

El editor gráfico también se reimplementa con Tkinter y guarda el mismo formato JSON que puede cargar el modo `ficheros`. No pretende clonar píxel a píxel el editor Java, sino cubrir la misma función práctica: crear, abrir, modificar, guardar y validar escenarios.

El sistema de replay usa JSON y SHA-256 del estado serializado. Es suficiente para regresiones y partidas documentadas, aunque no intenta reproducir el formato interno exacto del Java.
