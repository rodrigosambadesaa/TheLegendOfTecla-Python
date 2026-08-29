# Jerarquía POO canónica

Esta versión Python mantiene dos capas:

1. El núcleo idiomático usado por el motor (`Character`, `Player`, `Enemy`, `Ally`, `Item`).
2. La jerarquía canónica de las prácticas P1/P2/P3/P4 y del repositorio Java original (`Personaje`, `Jugador`, `Marine`, `Francotirador`, `Zapador`, `Enemigo`, `Sectoid`, etc.).

La segunda capa está implementada en `legend_of_tecla/hierarchy.py` mediante clases reales, no como simples cadenas de texto.

## Personajes

```text
Personaje
├── Jugador
│   ├── Marine
│   ├── Francotirador
│   └── Zapador
├── Enemigo
│   ├── Sectoid
│   ├── Floater
│   │   └── HeavyFloater
│   ├── Commander
│   │   └── CommanderPrime
│   ├── Berserker
│   └── Jefe
└── AliadoEscuadron
```

### Reglas trasladadas

- `Jugador` conserva el recorrido histórico de posiciones.
- `Marine` arranca con 120 salud y 90 energía. Duplica daño cuerpo a cuerpo y penaliza daño lejano.
- `Francotirador` arranca con 100 salud, 100 energía y +1 visión base. Su daño escala con distancia.
- `Zapador` arranca con 105 salud y 95 energía. Es especialista en trampas y explosivos.
- `Enemigo` conserva multiplicador global de daño y rango de audición.
- `Sectoid` arranca con 70 salud y 70 energía.
- `HeavyFloater` hereda de `Floater`, arranca con 110 salud y 60 energía, y tiene movimiento más pesado.
- `Commander` arranca con 125 salud y 120 energía y mantiene bonificación táctica de escuadra.
- `Berserker` arranca con 170 salud y 110 energía.
- `Jefe` conserva fase de jefe.

## Objetos

```text
Objeto
├── Arma
├── Armadura
├── Botiquin
├── Linterna
├── Binocular
├── CuboAgua
├── Explosivo
│   └── Granada
├── Municion
├── Credencial
└── Componente
```

Todos estos tipos heredan de `Item`, por lo que siguen funcionando con el inventario, la mochila, el equipamiento, el guardado/carga y los comandos existentes.

## Compatibilidad con ampliaciones

La jerarquía no sustituye las ampliaciones modernas: las acompaña. El motor sigue soportando aliados, médicos, fuego, fuentes, cubos de agua, puertas, terminales, interruptores, trampas, barricadas, cobertura, armas modernas, munición, crafting, estadísticas, logros, replay y GUI/editor.

## Tests de contrato

`tests/test_hierarchy.py` valida que:

- La relación `Personaje -> Jugador -> Marine/Francotirador/Zapador` existe realmente.
- La relación `Personaje -> Enemigo -> Sectoid/Floater/HeavyFloater/...` existe realmente.
- Las estadísticas base coinciden con la versión Java.
- Los objetos canónicos son subclases reales de `Item`.
- Las factorías `crear_jugador` y `crear_enemigo` devuelven el subtipo correcto.
