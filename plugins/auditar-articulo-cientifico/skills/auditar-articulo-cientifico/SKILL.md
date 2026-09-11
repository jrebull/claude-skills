---
name: auditar-articulo-cientifico
description: Método para auditar un artículo científico aplicado que usa regresión lineal, y producir una ficha de auditoría defendible. Invocar cuando haya que evaluar cómo un artículo justifica y diagnostica su modelo, dictaminar si su evidencia diagnóstica es suficiente, parcial o no documentada, o localizar evidencia por dimensión (ajuste, inferencia, forma funcional, homocedasticidad, independencia, normalidad, influencia, multicolinealidad, validación). El principio es que un artículo que publica coeficientes, R² y valores p está sobredeterminado y puede recalcularse entero desde sus propias tablas: cubre la extracción del XML JATS, la reconstrucción del tamaño de muestra, los barridos algebraicos que descubren erratas, las colas exactas en Python puro sin scipy, la nula exacta de Spearman por permutación, la digitalización de figuras con banda de error declarada, el diagnóstico de influencia que el artículo no hizo, la disciplina de verificar cada hallazgo antes de escribirlo, y las trampas de maquetación del entregable en LaTeX.
---

# Auditar un artículo científico con regresión lineal

La tesis operativa: **un artículo que publica coeficiente, R² y valores p está
sobredeterminado**. Esas cifras satisfacen identidades exactas entre sí, así que
se puede reconstruir su tamaño de muestra, recalcular sus pruebas y demostrar
qué falta, sin acceso a los datos originales y sin opinar.

La diferencia entre una ficha mediocre y una buena no es el vocabulario: es que
la buena **ejecuta el diagnóstico que el artículo omitió** y enseña el resultado.

---

## 0. La disciplina, antes que el método

Estas cuatro reglas se rompieron al menos una vez cada una y todas costaron una
ronda entera.

**Nunca trates una cifra redondeada como puntual.** Todo hallazgo se propaga por
la caja de redondeo. `0.03` no es 0.03, es `[0.025, 0.035)`. Un barrido de la
cota algebraica marcó ocho celdas imposibles; al propagar la caja quedó **una**.
Las otras siete habrían sido siete acusaciones falsas.

**Verifica cada hallazgo ajeno antes de aplicarlo.** Los agentes auditores se
contradicen. En la Semana 5, un agente dijo que dos celdas de Spearman cambiaban
de veredicto, lo apliqué sin comprobar, otro lo contradijo, y la enumeración de
las 40,320 permutaciones le dio la razón al primero: mi «corrección» había
metido una afirmación falsa que sobrevivió una ronda. Recalcula. Y separa
«acepto la conclusión» de «acepto el razonamiento», porque a veces solo lo
primero es cierto.

**Escribe el archivo antes de comprobarlo.** Un script de correcciones con un
`assert` después de los `replace` y antes del `write` falló en el assert: el log
imprimió «ok» línea por línea y **no se escribió nada**. Cualquier script de
edición acumula fallos en una lista y escribe siempre; la comprobación va al
final y sobre el resultado en disco.

**No deduzcas la precisión de impresión desde `repr()`.** El artículo imprime
`0.90` y `float` devuelve `0.9`: la caja sale diez veces más ancha y el barrido
se vuelve permisivo en silencio. Pasa los decimales explícitos, leídos de la
tabla.

**Y audita el instrumental como auditas el artículo.** Estas herramientas se
escribieron para esta metodología y aun así, al probarlas una por una, la
función que agrupa los rótulos de un eje devolvía **el mismo centroide para
todos**: un `grupos.append(cur)` seguido de `cur.clear()` mete la misma lista en
todos los grupos y luego la vacía. No lanzaba ningún error; solo habría
calibrado mal cada eje, en silencio, para siempre. Ejecuta `probar.py` antes de
confiar en cualquier cifra que salga de aquí.

---

## 1. Elegir el artículo

Debe ser arbitrado, aplicado, con respuesta y predictores distinguibles, con
método y resultados suficientes, y con DOI o enlace estable. Y una condición que
no está escrita pero decide el resultado: **que publique suficientes cifras para
reconstruirlo**. Un artículo que solo dice «la regresión fue significativa» no
se puede auditar; uno que publica seis tablas de coeficientes se audita entero.

Descarta antes de invertir: si el modelo lineal es una mención de paso, o si el
texto completo no es accesible, cambia de artículo. La consulta puede sesgarse a
propósito hacia trabajos auditables:

    "multiple linear regression" AND <tema> ("Durbin-Watson" OR "variance inflation factor") residuals

Meter términos de diagnóstico favorece artículos donde el modelo lineal es el
objeto, no el adorno.

---

## 2. Conseguir el texto como XML, no como PDF

El PDF sirve para leer; el **XML JATS** sirve para auditar, porque trae las
tablas como celdas. Sin esto no hay auditoría celda por celda.

    python3 "$SKILL_DIR/references/jats.py" PMC11728780 art.xml

Si el artículo no está en Europe PMC no hay atajo: transcribir a mano y
verificar la transcripción con un segundo pase independiente.

⚠️ **El menos tipográfico.** Los artículos imprimen U+2212, no el guion ASCII.
`float()` lo rechaza en silencio y un barrido de contradicciones de signo
devuelve cero hallazgos sin avisar de nada. `jats.num()` ya lo normaliza; si
escribes tu propio parser, normalízalo tú, junto con los espacios duros.

⚠️ **La coma.** En un artículo en inglés separa millares y hay que quitarla;
en uno en español puede ser el separador decimal, y quitarla convierte `0,05`
en `5`, cien veces mayor y sin ningún aviso. `jats.num()` solo la quita cuando
el número tiene forma de millares, y devuelve `None` en cualquier otro caso
para que el problema se vea. Con decimales por coma, pásale `coma='decimal'`
a propósito.

---

## 3. Reconstruir el tamaño de muestra

Casi ningún artículo de este tipo declara *n*, y **sin *n* no hay auditoría**:
ninguna cola se puede calcular. Se recupera por varias vías y se confirma cuando
coinciden:

1. **Del diseño** descrito en métodos (ventanas de agregación, estratos).
2. **De la F publicada**: `reconstruir_n(R2, F, k)` despeja *n* propagando las
   cajas de R² y F. Un solo F suele bastar para dejar un único entero posible.
3. **De las colas de cuatro decimales**, si el texto cita alguna. Es la vía más
   fuerte: comprueba que **todas** son compatibles con el *n* candidato y con
   ningún otro. Que trece cifras encajen con *n*=8 y **cero** con 7 o 9 es un
   argumento mucho más contundente que una coincidencia suelta.

---

## 4. Los barridos algebraicos

Aquí aparecen los hallazgos que nadie puede discutir. Todos en
`references/barridos.py`, todos con propagación de caja.

| Identidad | Qué significa si falla |
|---|---|
| `identidad_R2` — en regresión simple R² = r² | Una de las dos celdas es errata. El valor p que la acompaña dice cuál. |
| `signo` — b y r comparten signo siempre | Signo perdido. Si el Spearman va con b, el errado es el Pearson. |
| `p_redundante` — p(b) = p(modelo) = p(Pearson) | Misma prueba impresa con dos números. Diferencia en la última cifra, redondeo; que cruce el umbral, hallazgo. |
| `cota_t` — t_j² ≤ df·R²/(1−R²) | El R² total limita la significancia de cualquier coeficiente. Un p menor es **aritméticamente imposible**. |

La identidad R² = r² tiene un uso extra: si se cumple en todas las celdas de una
tabla, esa tabla **no es regresión múltiple** aunque el resumen la llame así.

---

## 5. Colas exactas, y la trampa de Spearman

`references/estadistica_pura.py` da t, F y Pearson por beta incompleta, sin
scipy. Con *n* pequeño hay que usar las colas exactas y no aproximaciones.

**Spearman no comparte el crítico de Pearson.** Su nula es discreta:
`spearman_exacto(n)` enumera las n! permutaciones y devuelve la retícula de
valores alcanzables, sus colas y el crítico real. Con *n*=8 el crítico es
**0.7381 con cola 0.0458**, no 0.05, y el valor inmediato inferior de la
retícula, 0.7143, ya deja 0.0576: entre uno y otro no hay nada.

Dos precauciones que decidieron el resultado la última vez:

- **El redondeo va hacia abajo, no hacia arriba.** Un ρ impreso como `0.72` vale
  *menos* de 0.725, así que el mayor alcanzable compatible es 0.7143, que **no**
  rechaza. Razonar al revés («salta al siguiente valor posible») invierte el
  veredicto. Este error concreto llegó a estar impreso en el entregable.
- **Cuenta cuántos ρ caen fuera de la retícula.** Si muchos no son alcanzables
  sin empates, hay empates en los datos, la nula sin empates no los gobierna y
  ninguna celda queda resuelta. Esa cifra —37 de 104 en la Semana 5— es más
  informativa que los veredictos individuales, y además desmonta cualquier
  intento de atribuir la aproximación a un programa concreto.

---

## 6. La discrepancia Pearson–Spearman es la señal diagnóstica

Muchos artículos publican los dos coeficientes y creen que con eso «comprobaron»
algo. No: reportar dos estadísticos no es comprobar un supuesto. **Contrastarlos
sí lo habría sido.** Una brecha entre Pearson y Spearman apunta a no linealidad
o a una observación influyente, que es exactamente lo que la dimensión de forma
funcional pide.

`pearson_vs_spearman` cuenta las celdas donde los dos caen en lados opuestos del
alfa declarado y las de signos opuestos. En la Semana 5 fueron **21 de 104** y
**6** respectivamente, sin un solo comentario del artículo. Ese es el argumento
que derrota la defensa de «parcial»: el diagnóstico estaba impreso en sus
propias tablas y nadie lo miró.

---

## 7. Multiplicidad

Cuenta pruebas **distintas**, no celdas: en regresión simple p(b), p(modelo) y
p(Pearson) son la misma prueba impresa tres veces, y contarlas por separado
infla el denominador. `multiplicidad(n_pruebas, n_significativas)` da las
esperadas bajo nulo global y el umbral de Bonferroni.

Y no te pases de frenada. Si el exceso de significativas es enorme, la señal
supera al ruido y **lo criticable no es la ausencia de corrección**: es que el
artículo lea decenas de resultados significativos sin discutir en ningún momento
cuántos esperaba por azar. Bonferroni además es excesivamente conservador cuando
las pruebas comparten las mismas observaciones.

---

## 8. Digitalizar la figura: donde suele estar el mejor hallazgo

Si el artículo publica un diagrama de dispersión, casi seguro contiene el
diagnóstico de influencia que nunca hizo. `references/digitalizar.py` cubre el
proceso. Las reglas están en su docstring; la más importante:

**Digitaliza lo menos posible.** Si el texto publica las abscisas, úsalas y lee
del gráfico solo las ordenadas. En la Semana 5 eso redujo la digitalización a
ocho ordenadas más una abscisa, y el ajuste resultante dio pendiente 0.4188 y
R² 0.9126 frente a los 0.4185 y 0.912 impresos en la propia figura: la lectura
se valida sola.

El umbral de tinta con que separas los rótulos del fondo mueve la calibración,
así que **el residuo que devuelve `calibrar()` es el control de calidad**: por
encima de dos píxeles has emparejado mal los rótulos o uno se partió en dos
grupos.

Después, `influencia()` y `banda()`. Una cifra que no sobrevive a mover cada
lectura un píxel no se usa. Y al revés: si sobrevive, dilo, porque convierte una
estimación en una demostración.

⚠️ No sobredeclares la precisión. Escribir «reproduce con cuatro decimales» cuando
coincides en tres es exactamente el defecto que le imputas al artículo.

---

## 9. El dictamen

Tres categorías, y la frontera está en la palabra **localizable**:

- **Suficiente**: evidencia pertinente para los supuestos principales, con sus
  decisiones explicadas.
- **Parcial**: algunas comprobaciones relevantes, pero quedan dimensiones sin
  evaluar.
- **No documentada**: reporta ajuste y resultados sin evidencia localizable de
  evaluación diagnóstica.

Una declaración sin resultado **no es evidencia localizable**. «A temporal trend
analysis was performed» sin indicador, criterio ni resultado no documenta la
dimensión de independencia. Dilo así, y con esa precisión: no sostienes que no
se hiciera, sostienes que no aparece.

**Construye la mejor defensa posible de la categoría vecina y derrótala en el
documento.** Un dictamen que no se ha enfrentado a su objeción más fuerte no
está sustentado. Y cuidado con el argumento fácil: sostener que los p de
Spearman «no son libres de distribución» es **falso**, porque su nula depende
solo de los rangos. Lo que no es libre es el cálculo, no la distribución.

Cierra siempre con lo que el artículo **sí** hace bien y con qué habría bastado
para alcanzar la categoría superior. Una auditoría que solo acusa es más débil
que una que además mide la distancia al aprobado.

---

## 10. El entregable

El formato lo fija la consigna de la actividad, no la costumbre: léela primero.
Para el LaTeX, el preámbulo canónico y sus trampas ya pagadas están en
`references/preambulo.tex`, que viene con este skill.

Dos defectos de maquetación que sobrevivieron a varias revisiones humanas y a
una auditoría ciega, y que `references/maquetacion.py` detecta por script:

- **Encabezado de `longtable` huérfano**: filete, títulos de columna y ninguna
  fila, arriba de una página, encima del rótulo de la sección siguiente. Lo
  provoca un `longtable` que abre tras un macro de sección con `\needspace`. No
  se arregla quitando `\nopagebreak` ni con `\clearpage` bloque a bloque: hay
  que darle al `\needspace` sitio para rótulo, título, encabezado y primera
  fila (15 líneas bastaron), y hacerlo **selectivo**, porque aplicarlo a los
  bloques de texto desperdicia páginas enteras.
- **Retrato pisado por el texto**: `wrapfigure` deja de aplicar la sangría en
  cuanto termina el párrafo, y si el párrafo tiene menos líneas que las
  reservadas, el siguiente escribe encima de la foto. Usa dos `minipage`.

Antes de entregar: compila el ZIP **en un directorio vacío**, compara el md5 del
`.tex` del paquete contra el del fuente, y comprueba que el texto del PDF
reconstruido coincide con el entregado. Un ZIP desfasado produce en Overleaf un
documento distinto del que revisaste.

---

## Herramientas

Viven junto a este archivo, **no** en el directorio de trabajo. Antes del primer
comando, fija la ruta absoluta del directorio que contiene este `SKILL.md`:

    SKILL_DIR=<directorio de este SKILL.md>

Instalado como plugin queda bajo `plugins/cache/…`, no en el proyecto, así que
`python3 references/…` a secas falla.

| Archivo | Para qué |
|---|---|
| `references/estadistica_pura.py` | Colas de t, F y Pearson por beta incompleta; nula exacta de Spearman; cajas de redondeo. Sin scipy. |
| `references/jats.py` | Descarga y parseo del XML JATS de Europe PMC; tablas como celdas; normalización del menos tipográfico; afirmaciones de ausencia. |
| `references/barridos.py` | Identidades algebraicas, umbral exacto de Spearman, discrepancia Pearson–Spearman, multiplicidad, reconstrucción de *n*. |
| `references/digitalizar.py` | Calibración de ejes, marcadores, ajuste, apalancamiento, distancia de Cook y banda de error de un píxel. |
| `references/maquetacion.py` | Encabezados huérfanos y páginas poco llenas sobre el PDF compilado. |
| `references/probar.py` | Batería de regresión de las cinco anteriores. Ejecutarla antes de confiar en ninguna. |
| `references/preambulo.tex` | Preámbulo LaTeX con las trampas de maquetación ya resueltas. Rellena `\hypersetup` con tus datos. |

Todos se prueban contra la auditoría de `microorganisms-12-02661` (dengue en
México, MDPI 2024) y reproducen sus cifras: *n*=8, crítico de Spearman 0.7381
con cola 0.0458, 4 identidades rotas, 2 contradicciones de signo, 7 celdas con
dos valores p de las que 6 son redondeo, 37 coeficientes fuera de la retícula,
21 discrepancias Pearson–Spearman, h = 0.516 y D de Cook = 1.84.

    python3 "$SKILL_DIR/references/probar.py" <fulltext.xml> <raster_figura.png>

Sin argumentos comprueba lo que no necesita los archivos del artículo. Devuelve
código 1 si algo falla, así que sirve tal cual en un gancho o en CI.
