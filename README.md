# jrebull-skills

Marketplace de plugins para [Claude Code](https://claude.com/claude-code).

## Instalación

Dentro de Claude Code:

```
/plugin marketplace add jrebull/claude-skills
/plugin install auditar-articulo-cientifico@jrebull-skills
/plugin install anteproyecto-uacj-latex@jrebull-skills
```

Para traer cambios posteriores:

```
/plugin marketplace update jrebull-skills
```

## Skills

### `auditar-articulo-cientifico`

Método para auditar un artículo científico aplicado que usa regresión lineal y
producir una ficha de auditoría defendible.

La tesis operativa: un artículo que publica coeficientes, R² y valores p está
**sobredeterminado**. Esas cifras satisfacen identidades exactas entre sí, así que
se puede reconstruir el tamaño de muestra, recalcular las pruebas y demostrar qué
falta, sin acceso a los datos originales.

Cubre la extracción del XML JATS, la reconstrucción de *n*, los barridos
algebraicos que descubren erratas, las colas exactas en Python puro (sin scipy),
la nula exacta de Spearman por permutación, la digitalización de figuras con banda
de error declarada, el diagnóstico de influencia que el artículo no hizo, y las
trampas de maquetación del entregable en LaTeX.

Claude lo invoca solo cuando la conversación lo amerita. A mano, los skills de
un plugin se llaman con el nombre del plugin por delante:

```
/auditar-articulo-cientifico:auditar-articulo-cientifico
```

Incluye `references/preambulo.tex`, un preámbulo LaTeX para la ficha de
auditoría con las trampas de maquetación ya resueltas.

**Sin dependencias:** los scripts de `references/` son Python 3 de biblioteca
estándar. No necesitan numpy, scipy ni statsmodels. La batería de regresión
`references/probar.py` corre sin argumentos y devuelve código 1 si algo falla.

### `anteproyecto-uacj-latex`

Plantilla LaTeX **genérica** del *Anteproyecto de Innovación Tecnológica* (MIAAD, UACJ) con el
formato completo: clase `report` carta 12 pt, Times, portada con logo, declaración, índices con
«Figura N:» y «Tabla N:», numeración continua de figuras, tablas y ecuaciones, citas IEEE clicables
(`\cita{n}`), cronograma semanal apaisado, referencias, apéndice y glosario. Compila con pdfLaTeX en
tres pasadas con 0 errores y 0 overfull (`ejemplo_compilado.pdf`).

Trae además `validar.py` (auditoría estática sin dependencias: balance de entornos, orden de citas,
labels y figuras, y las trampas de babel-spanish y TikZ que rompen la compilación) y `compilar.sh`
(tres pasadas + censo del log). `LEEME_companeros.md` explica el uso sin necesidad de Claude:

```
/anteproyecto-uacj-latex:anteproyecto-uacj-latex
```

**Sin Claude:** basta copiar `plantilla_anteproyecto.tex`, `Figures/`, `validar.py` y `compilar.sh`
a un proyecto de Overleaf (compilador pdfLaTeX) y editar el bloque `DATOS DEL PROYECTO`.
