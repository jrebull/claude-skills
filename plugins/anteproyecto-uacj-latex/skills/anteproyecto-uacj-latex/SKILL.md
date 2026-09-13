---
name: anteproyecto-uacj-latex
description: Plantilla LaTeX genérica y reglas de compilación del Anteproyecto de Innovación Tecnológica de la MIAAD (UACJ), lista para compartir con otros estudiantes. Invocar al crear un anteproyecto nuevo desde cero, al adaptar el formato a otro proyecto, al auditar por qué un .tex del formato no compila en Overleaf, o al revisar que un documento cumpla el formato (portada con logo, índices con «Figura N:», numeración continua, citas IEEE clicables, cronograma apaisado, glosario). Incluye la plantilla compilable con el logo UACJ, las trampas conocidas de babel-spanish y TikZ, un validador estático y el compilador de tres pasadas con censo del log.
---

# Anteproyecto MIAAD · UACJ — plantilla LaTeX genérica

Carpeta del skill (todo lo que hay que copiar a un proyecto nuevo o a Overleaf):

```text
plantilla_anteproyecto.tex   ← documento completo compilable (17 págs. con texto de ejemplo)
Figures/logouacj.png         ← logo institucional UACJ (640×640 RGBA); NO renombrar
validar.py                   ← auditoría estática (stdlib): begin/end, citas, labels, prohibiciones
compilar.sh                  ← pdflatex ×3 + censo del log (errores/overfull/underfull/indefinidas)
ejemplo_compilado.pdf        ← la plantilla ya compilada (17 págs.) para ver cómo debe quedar
LEEME_companeros.md          ← guía humana para quien no usa este asistente
references/reglas_latex.md   ← catálogo completo de reglas y trampas con su motivo
```

La plantilla reproduce el **formato** del anteproyecto (clase, paquetes, títulos, índices, folios,
contadores, macro `\cita`, cronograma apaisado) con contenido genérico de guía y una paleta propia
(verde/ámbar, nombres neutros) distinta de cualquier entregable concreto.
Lo verificado: compila con pdfLaTeX en tres pasadas con **0 errores, 0 overfull, 0 underfull, 0
referencias indefinidas**, sin `missfont`, y `validar.py` la aprueba. La v1.0.1 incorpora una auditoría
ciega (20 roturas sembradas, controles benignos, portabilidad).

## Flujo para un anteproyecto nuevo

1. Copiar `plantilla_anteproyecto.tex`, `Figures/` (con el logo), `validar.py` y `compilar.sh`.
2. Editar **sólo** el bloque `DATOS DEL PROYECTO` (título, autor, matrícula, asesor, instituto,
   departamento, ciudad, fecha). Todo lo demás del preámbulo está resuelto; un paquete nuevo sólo
   entra con un comentario que diga para qué.
3. Sustituir el texto guía capítulo por capítulo conservando la estructura:
   Resumen (autocontenido, sin citas) → Introducción → I. Planteamiento (1.1 Antecedentes,
   1.2 Descripción, 1.3 Objetivos, 1.4 Justificación, 1.5 Hipótesis/Preguntas) → II. Marco
   teórico y tecnológico → III. Producto esperado y validación → IV. Metodología →
   Cronograma → Referencias → Apéndices → Glosario.
4. Figuras: archivo en `Figures/`, `\includegraphics{nombre.png}` **sin ruta**, siempre con
   `\caption[corto]{largo}` + `\label{fig:x}` y al menos un `\ref`. Igual para tablas (`tab:`).
5. Citas: `\cita{N}` en el cuerpo, numeradas por **orden de primera aparición**, y cada `N` con su
   `\item \label{bib:N}` en Referencias. Nunca reciclar un número ni citar sin entrada.
6. Antes de entregar: `python3 validar.py archivo.tex` (sale 0) y `bash compilar.sh archivo.tex`
   (sale 0: sin errores, overfull ni indefinidas). En Overleaf: compilador **pdfLaTeX**, y mirar el PDF:
   los solapamientos de leyendas y los desbordes de tablas sólo se ven renderizados.

## Reglas que rompen la compilación o el formato (resumen; detalle en `references/reglas_latex.md`)

- **Clase y paquetes cerrados**: `\documentclass[12pt,letterpaper]{report}`; no añadir paquetes sin
  anotarlo en el preámbulo. `booktabs` y `algorithm/algpseudocode` son añadidos probados; los paquetes
  de fuentes (`lmodern`, `times`, `fontspec`) cambian la tipografía en silencio y el validador los avisa.
- **babel-spanish**: `es-nodecimaldot` mantiene el punto decimal y `es-tabla` nombra «Tabla»; **nunca**
  `\shorthandoff{.}` (`I can't switch '.' on or off`). `\%` va en modo texto: `$<$\,0.5\,\%`; dentro de
  una fórmula `\,\%` rompe con `Incompatible glue units`. Comillas: ``así''.
- **TikZ**: babel activa `<` y `>`; **nunca** `shorten <=` / `shorten >=`. Acortar flechas con
  `([xshift=2pt]a.east) -- ([xshift=-2pt]b.west)`. Geometría fija y comentada al inicio del
  `tikzpicture` (anchos, alturas, centros); la suma de anchos debe caber en `\textwidth` = 15.24 cm.
- **Numeración**: figuras, tablas y ecuaciones de corrido sin punto de capítulo `(1)`, `(2)`;
  `secnumdepth=0`, el número de sección va escrito en el título: `\section{1.1 Antecedentes}`.
- **Interlineado**: `\setstretch{1.10}` global; portada en `spacing{1.2}`, firma en `spacing{2.0}`;
  **nunca** `\doublespacing`.
- **Cronograma apaisado**: dentro de `\begin{landscape}` **no** usar `\begin{table}[H]` (un flotante
  ahí puede desplazar el cuadro o dejar hoja en blanco); usar `\captionof{table}` en una
  `minipage[c][\textheight][c]`. Cada fila lleva exactamente 40 `&` (1 actividad + 40 semanas; con
  menos, la fila pierde el borde sin error alguno, y `validar.py` los cuenta); las bandas usan
  `\multicolumn{41}`.
- **Tablas `p{}`**: desbordan si `suma(anchos) + 2·ncols·\tabcolsep > 15.24 cm`; calcularlo antes.
- **Captions** describen contenido, no estilo («borde azul» no va). Colores sólo por nombre:
  `colorprimario`, `colorsecundario`, `colorgris`, `colortexto` (paleta verde/ámbar por defecto; para
  otra basta cambiar los cuatro valores HTML del preámbulo).
- **Estilo de la casa**: verbos aplicados (desarrollar, implementar, construir); acrónimos una sola
  vez con `término (\textit{English}, ACR)`; métricas con fórmula una sola vez en el Marco Teórico;
  incisos con paréntesis o comas, no con rayas.

## Cómo auditar un .tex ajeno con este skill

1. `python3 validar.py su_archivo.tex --figures su/Figures` → lista de hallazgos con severidad.
2. `bash compilar.sh su_archivo.tex` → si falla, el primer `!` del log es el error real; si compila,
   revisar overfull (se sale del margen), underfull (cosmético) e indefinidas (citas o `\ref` rotos).
3. Comparar su preámbulo con el de la plantilla: casi todos los fallos vienen de cambiar la clase,
   quitar `es-nodecimaldot`, meter `\%` en math, usar `shorten` en TikZ o poner `table` en landscape.
4. No «arreglar» reescribiendo el contenido: el skill gobierna formato y compilación, no la prosa.

## Lo que este skill no incluye a propósito

- El bloque «Acerca del autor y del asesor»: no forma parte de la plantilla.
- Firma escaneada: cada quien añade la suya en `Figures/` (hay un comentario en la declaración).
- Contenido de ningún proyecto concreto: la plantilla es genérica y su paleta es propia.
