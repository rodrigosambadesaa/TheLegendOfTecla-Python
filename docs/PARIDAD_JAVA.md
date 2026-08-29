# Paridad con el repositorio Java original

Este documento reconoce explicitamente que la reimplementacion Python no era aun una
traduccion completa del repo Java `TheLegendOfTecla`. El objetivo pasa a ser una
migracion por paquetes, manteniendo el motor jugable existente y acercando la
arquitectura al diseno Java/PDF.

## Paquetes Java detectados

El repo Java original contiene, entre otros, estos paquetes bajo
`src/main/java/com/legendoftecla`:

- `achievements`
- `ai`
- `audio`
- `commands`
- `config`
- `console`
- `constants`
- `effects`
- `engine`
- `events`
- `exceptions`
- `gui`
- `inventory`
- `io`
- `model`
- `persistence`
- `progression`
- `replay`
- `validation`

## Estado actual en Python

| Area | Estado | Notas |
| --- | --- | --- |
| Modelo base | Parcial/funcional | `model.py`, `world.py`, `hierarchy.py` |
| Jerarquia POO canonica | Incorporada | `Personaje`, `Jugador`, `Marine`, `Francotirador`, `Zapador`, `Enemigo`, etc. |
| Comandos | Incorporado parcial | `commands.py` con patron Command y parser textual |
| IA | Incorporado parcial | `ai.py` con percepcion, contexto, acciones y estrategias |
| Motor modular | Incorporado parcial | `engine.py` con movimiento, combate, inventario, fuego y trampas |
| Eventos | Incorporado parcial | `events.py` con bus observable y registro |
| Efectos | Incorporado parcial | `effects.py` con gestor de estados temporales |
| Validaciones | Incorporado parcial | `validation.py` con limites y fachada `Validaciones` |
| Excepciones | Incorporado parcial | `exceptions.py` con excepciones de dominio |
| Replay | Incorporado parcial | `replay.py` determinista |
| GUI | Incorporado parcial | Tkinter, no Swing 1:1 |
| Editor | Incorporado parcial | Tkinter/JSON, no editor Java 1:1 |
| Audio | Pendiente | Debe quedar desacoplado por eventos |
| Persistencia avanzada | Pendiente parcial | Guardado existe, falta paridad completa de campana/equipamiento/estados |
| Progresion/campana | Pendiente parcial | Hay campana basica, falta `progression` equivalente |
| Inventario avanzado | Pendiente parcial | Hay inventario basico; falta armeria/reglas de armamento completas |
| IO/carga de datos completa | Pendiente parcial | Falta cargar todos los formatos y enemigos/objetos como en Java |

## Criterio de avance

1. No crear stubs vacios: cada modulo nuevo debe compilar y tener tests.
2. Mantener el motor actual funcionando mientras se sustituyen piezas internas.
3. Priorizar paridad estructural antes que detalles visuales.
4. Migrar reglas de gameplay en paquetes pequenos y verificables.
5. Conservar ampliaciones modernas: aliados, fuego, puertas, trampas, replay, editor y GUI.

## Siguiente bloque recomendado

- Reemplazar en `game.py` la creacion generica de `Player`/`Enemy` por factorias
  de `hierarchy.py` o adaptadores compatibles.
- Migrar `inventory` y `io` para cargar enemigos, armas, objetos y escenarios con
  la misma semantica que el Java.
- Anadir `progression.py`, `persistence.py` y logros como servicios separados.
