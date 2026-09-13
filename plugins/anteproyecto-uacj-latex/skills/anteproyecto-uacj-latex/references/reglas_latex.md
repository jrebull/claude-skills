# Reglas y trampas del formato (con su motivo)

Catálogo completo de lo que la plantilla ya resuelve y de lo que rompe la compilación o el formato.
Cada regla nace de un fallo reproducido al compilar con pdfLaTeX y babel-spanish.

## A. Preámbulo (no tocar)

| Elemento | Valor | Motivo |
|---|---|---|
| Clase | `\documentclass[12pt,letterpaper]{report}` | el formato exige `report` (capítulos), no `article` |
| Fuente | `mathptmx` | Times Roman en texto y matemáticas |
| Márgenes | `geometry` 1.25 in laterales, 1 in arriba/abajo | lineamiento del curso |
| Idioma | `babel[spanish,es-tabla,es-nodecimaldot]` | `es-tabla` → «Tabla»; `es-nodecimaldot` → punto decimal |
| Interlineado | `\setstretch{1.10}` + `\parskip 0.4em` | interlineado del formato; portada `spacing{1.2}`, firma `spacing{2.0}` |
| Títulos | `titlesec`: capítulo centrado 16 pt, secciones en negritas sin número | `\@chapapp` vacío quita «Capítulo» |
| Índices | `tocloft` con `\cftfigpresnum{Figura~}` y `\cfttabpresnum{Tabla~}` | los índices muestran «Figura N:» y «Tabla N:», no sólo el número |
| Folio | `fancyhdr` sólo pie centrado | sin encabezados |
| Contadores | `chngcntr`: `\counterwithout{figure/table/equation}{chapter}` | Figura 1, 2, 3… y ecuaciones (1), (2), sin `1.1` |
| Secciones | `\setcounter{secnumdepth}{0}` | el número va escrito en el título |
| Citas | `\newcommand{\cita}[1]{\hyperref[bib:#1]{[#1]}}` | IEEE clicable |
| Hipervínculos | `hyperref` con `colorlinks=false, pdfborder={0 0 0}`; `pageanchor=false` sólo en la portada | sin recuadros; evita el aviso «destination with the same identifier (page.1)» |
| URLs | `url[hyphens]` + `\g@addto@macro{\UrlBreaks}{\UrlOrds}` | quiebre en cualquier carácter |
| Cronograma | `pdflscape` | hoja apaisada sin girar el resto |

Paquetes que se han añadido sin conflicto en documentos del mismo formato: `booktabs`
(`\toprule/\midrule/\bottomrule`), `algorithm` + `algpseudocode` (con `\floatname{algorithm}{Algoritmo}`).
Cualquier otro se documenta en el preámbulo antes de usarse. Los paquetes de fuentes (`lmodern`, `times`,
`fontspec`) cambian la tipografía en silencio: `validar.py` los avisa.

## B. Trampas de babel-spanish

1. **`\%` en modo matemático**: babel redefine `\%` y con el espacio fino da `$12.5\,\%$` →
   `! Incompatible glue units` (en `\es@sppercent`). `$12.5\%$` a secas compila, pero se prohíbe igual
   para no depender de ese detalle. Escribir siempre `12.5\,\%` y `$<$\,0.5\,\%` en modo texto.
2. **`\shorthandoff{.}`** rompe babel moderno (≥ v5) con `! Package babel Error: I can't switch '.' on
   or off--not a shorthand`; basta `es-nodecimaldot`.
3. **`<` y `>` son caracteres activos**: en TikZ, `shorten <=`/`shorten >=` produce
   `Argument of \language@active@arg< has an extra }`. Solución: `([xshift=2pt]a.east) --
   ([xshift=-2pt]b.west)`. En math (`$<$`) están protegidos.
4. Comillas: ``texto'' (dos acentos graves y dos apóstrofos), no `"texto"`.

## C. Figuras y tablas

- Toda figura: `\begin{figure}[H]` + `\centering` + `\caption[corto]{largo}` + `\label{fig:x}` y al
  menos un `\ref{fig:x}` en el texto. Igual las tablas con `tab:`.
- `\includegraphics{nombre.png}` sin ruta: `\graphicspath{{Figures/}}` ya la resuelve (con ruta también
  compila, pero el formato la prohíbe y `validar.py` la marca).
- Captions describen **contenido**, no estilo («paleta institucional», «borde azul» no van) y cierran
  con «Fuente: elaboración propia.» o la fuente real.
- Tablas con `p{}`: desbordan si `suma(anchos) + 2·ncols·\tabcolsep > \textwidth` (15.24 cm = 6 in);
  con `\tabcolsep=4pt` y 3 columnas, el margen para anchos es ≈ 14.4 cm.
- Tablas: `\arrayrulecolor{colorprimario}`, cabecera `\rowcolor{colorprimario!90}` con texto blanco,
  filas alternas `\rowcolor{colorprimario!8}`, y `\arrayrulecolor{black}` al cerrar.
- Figuras TikZ de objetivos: número en círculo del color primario, bloque de texto y etiqueta de
  producto en el secundario, pie gris itálico; **mismo `minimum width`/`minimum height` en todas**, `inner sep=0pt, outer sep=0pt`,
  y la geometría (anchos, separación, centros) escrita en un comentario al inicio del bloque. La suma
  de anchos y separaciones no puede superar 15.24 cm (el overfull aparece en el log).
- Fotos circulares (opcional, no incluido en la plantilla): `\clip (0,0) circle (r); \node at (0,0)
  {\includegraphics[width=2r]{foto}}` dentro de un `tikzpicture`.

## D. Cronograma apaisado

- `\begin{landscape}` + `\thispagestyle{empty}` + `\noindent\begin{minipage}[c][\textheight][c]{\linewidth}`
  (centrado vertical en una sola hoja; `\vfill` lo parte en tres).
- **Nunca** `\begin{table}[H]` dentro de `landscape`: un flotante ahí puede desplazar el cuadro o dejar
  una hoja apaisada en blanco según el contexto; el patrón del formato es `\captionof{table}` con
  `\captionsetup{hypcap=false}` dentro de la minipage.
- Tabular `|p{4.6cm}|*{10}{cccc|}` = 41 columnas; cada fila de actividad tiene exactamente **40 `&`**
  (con menos, la fila pierde el borde derecho sin ningún error; `validar.py` los cuenta); la fila de
  meses son 10 `\multicolumn{4}`; las bandas `\multicolumn{41}`.
- Celdas: `\cellcolor{colorprimario!60}` activas, `\cellcolor{colorsecundario!85}` hitos,
  `\cellcolor{colorgris!25}` receso. `\resizebox{\linewidth}{!}{…}` evita el desborde.

## E. Citas y referencias (IEEE)

- Numeradas por **orden de primera aparición** en el cuerpo; sin huecos; nunca reciclar.
- Rangos: `\cita{3}\textendash\cita{6}` → [3]–[6]; al auditar, expandir el rango antes de buscar
  huérfanas (las intermedias sí están citadas).
- Cada `\item` de Referencias lleva `\label{bib:N}`; el Resumen no cita.
- Formato: autores con iniciales, título entre comillas, revista en itálicas, vol., n.º, pp., año,
  doi; para web «[En línea]. Disponible en: \url{…}».

## F. Estilo del documento

- Tono profesionalizante: desarrollar, implementar, construir, entregar. Sin «contribución
  metodológica», sin umbrales numéricos comprometidos en hipótesis, preguntas abiertas.
- Acrónimos: una sola definición, patrón `término (\textit{English term}, ACR)`.
- Métricas con fórmula **una sola vez** (Marco Teórico); el resto nombra y remite.
- Decimales con punto, millares con coma (12,345). La portada dice «Anteproyecto de investigación
  presentado por», que es el texto literal del formato institucional.
- Incisos con paréntesis o comas; sin rayas largas de inciso ni `--` tipográfico en prosa.
- Resumen autocontenido: sin citas ni referencias cruzadas, ~200 palabras, en futuro.

## G. Verificación mecánica

```bash
python3 validar.py archivo.tex          # begin/end, citas, labels, prohibiciones
bash compilar.sh archivo.tex            # 3 pasadas + censo: errores, overfull, underfull, indefinidas
```

Gate de entrega: `compilar.sh` sale con 1 si hay errores, overfull o indefinidas; underfull sólo es
cosmético (tablas estrechas, URLs). Y siempre abrir el PDF: lo encimado no lo reporta ningún log.
