# Plantilla del Anteproyecto MIAAD (UACJ) — guía rápida

Formato del *Anteproyecto de Innovación Tecnológica* (clase `report`, carta, 12 pt, Times, márgenes
1.25 in / 1 in, portada con logo UACJ, índices con «Figura N:» y «Tabla N:», citas IEEE clicables,
cronograma semanal apaisado, glosario a dos columnas). Ya compila limpia: 0 errores, 0 overfull.

## 1. Qué copiar

```text
plantilla_anteproyecto.tex
Figures/logouacj.png        (no lo renombres; la portada lo busca por ese nombre)
validar.py                  (opcional, Python 3)
compilar.sh                 (opcional, si compilas en tu máquina)
```

## 2. En Overleaf

1. New Project → Upload Project → sube un ZIP con los archivos de arriba (la carpeta `Figures/`
   dentro).
2. Menu → **Compiler: pdfLaTeX** (no XeLaTeX ni LuaLaTeX).
3. Compila **tres veces** la primera vez (índices y referencias cruzadas).
4. Edita el bloque `DATOS DEL PROYECTO` al inicio del `.tex`: título, nombre, matrícula, asesor,
   instituto, departamento, ciudad y fecha. El resto del preámbulo no se toca; si un día hace falta
   un paquete más, se añade con un comentario que diga para qué.

## 3. Cómo escribir sin romperla

| Quiero… | Escribo… | Nunca… |
|---|---|---|
| citar | `\cita{4}` (y en Referencias `\item \label{bib:4} …`) | `[4]` a mano, números salteados, reciclar un número |
| un porcentaje | `12.5\,\%` o `$<$\,0.5\,\%` | `$0.5\,\%$` (rompe: `Incompatible glue units`); `$0.5\%$` compila pero se prohíbe por estilo |
| un decimal | `3.14` | `3,14` |
| una figura | archivo en `Figures/`, `\includegraphics[width=…]{nombre.png}` | rutas (`Figures/nombre.png`): compilan, pero `validar.py` las rechaza por estilo |
| caption | `\caption[corto]{largo}` + `\label{fig:algo}` y `\ref{fig:algo}` en el texto | figuras sin `\ref` |
| una sección | `\section{1.2 Descripción del problema}` (el número va en el título) | esperar numeración automática |
| flecha corta en TikZ | `([xshift=2pt]a.east) -- ([xshift=-2pt]b.west)` | `shorten <=` / `shorten >=` |
| colores | `colorprimario`, `colorsecundario`, `colorgris`, `colortexto` | códigos HTML sueltos |
| interlineado | nada (ya está en 1.10) | `\doublespacing` |
| tabla en el cronograma | la que ya está (40 `&` por fila; `validar.py` los cuenta) | `\begin{table}` dentro de `landscape` (el formato usa `\captionof`) |
| acrónimo | «aprendizaje automático (\textit{Machine Learning}, ML)» la primera vez | definirlo dos veces |

## 4. Antes de entregar

```bash
python3 validar.py plantilla_anteproyecto.tex   # 0 errores
bash compilar.sh plantilla_anteproyecto.tex     # sale con 1 si hay errores, overfull o indefinidas
```

Y abre el PDF: las leyendas encimadas y las tablas que se salen del margen sólo se ven renderizadas.

## 5. Si no compila

- Mira el **primer** `!` del log; lo demás suele ser consecuencia.
- `Argument of \language@active@arg< has an extra }` → hay un `shorten <=` en TikZ.
- `Incompatible glue units` (en `\es@sppercent`) → hay `\,\%` dentro de `$…$`; sacar el porcentaje de la fórmula.
- `I can't switch '.' on or off--not a shorthand` → alguien añadió `\shorthandoff{.}`; quitarlo.
- «Cuadro 1» en vez de «Tabla 1» → falta `es-tabla` en babel. `3,14` con coma dentro de una fórmula → falta `es-nodecimaldot`.
- `File 'x.png' not found` → el archivo no está en `Figures/` (o el nombre no coincide, mayúsculas incluidas).
- Toda la fuente cambió → se añadió `lmodern` u otro paquete de fuentes; el formato usa Times (`mathptmx`).
- Una fila del cronograma pierde el borde derecho → le faltan `&` (deben ser 40); `validar.py` lo cuenta.
- `pdfTeX warning: destination with the same identifier` → benigno si aparece; la plantilla ya lo evita con `pageanchor=false` en la portada.
