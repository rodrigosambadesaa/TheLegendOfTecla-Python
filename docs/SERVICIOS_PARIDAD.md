# Servicios de paridad añadidos

Esta tanda amplia la reimplementacion Python con una capa de servicios que faltaba frente al repositorio Java original.

## Modulos nuevos

- `constants.py`: simbolos, comandos canonicos y valores por defecto.
- `config.py`: carga/guardado de configuracion JSON/INI.
- `inventory.py`: mochila, entradas apilables y equipamiento.
- `progression.py`: progresion persistente, habilidades y campania.
- `achievements.py`: registro y reglas de logros.
- `persistence.py`: savegames versionados y backups.
- `io.py`: carga de escenarios `mapa.txt`, `objetos.txt`, `enemigos.txt` y JSON.
- `console.py`: adaptador de consola desacoplado del motor.
- `audio.py`: servicio de audio nulo para CI/headless.

## Objetivo

No sustituye todavia una migracion literal de cada clase Java, pero reduce la brecha de paquetes completos que no existian en Python y deja piezas testeables para integrarlas poco a poco en `game.py`.

## Siguiente paso recomendado

Integrar estos servicios dentro del flujo principal:

1. `GameConfig` deberia poder construirse desde `ConfiguracionJuego`.
2. `create_game()` deberia consumir `io.cargar_escenario()` para incluir enemigos y objetos del escenario original.
3. Los savegames de `game.py` deberian delegar en `persistence.py`.
4. El sistema de logros de `game.py` deberia delegar en `RegistroLogros`.
5. El inventario interno de `Character` deberia poder sincronizarse con `Mochila`/`Equipamiento`.
