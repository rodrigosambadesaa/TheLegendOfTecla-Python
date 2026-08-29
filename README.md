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
- Tests unitarios de motor, comandos, persistencia y carga de escenarios.

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

## Diferencias deliberadas frente a Java

La GUI Swing/noVNC del repo Java no se replica como Swing, porque Python no tiene ese stack. Esta versión deja el núcleo listo para una futura GUI con Tkinter, Textual, PyGame o web, pero centra la reimplementación en el motor y la consola jugable, que es la parte portable y verificable.

El editor gráfico de escenarios queda sustituido por persistencia JSON clara y por compatibilidad con `escenario.json`; eso permite editar mapas manualmente o generar herramientas posteriores encima del mismo formato.
