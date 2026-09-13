#!/usr/bin/env python3
"""Validador estático del anteproyecto MIAAD-UACJ (sin dependencias; Python 3.9+).

Uso:  python3 validar.py <archivo.tex> [--figures Figures]

Comprueba lo que un compilador NO reporta pero sí rompe la entrega:
  * balance \\begin{}/\\end{} (ignorando comentarios)
  * citas \\cita{N}: numeradas por orden de primera aparición, sin huecos,
    cada una con su \\label{bib:N} y sin entradas bib huérfanas
    (los rangos \\cita{X}\\textendash\\cita{Y} cuentan como citas de X..Y)
  * figuras y tablas: cada \\label{fig:...}/\\label{tab:...} referenciado con \\ref,
    cada \\caption con \\label, y cada \\includegraphics con nombre de archivo
    (sin ruta) que exista en Figures/
  * prohibiciones que rompen babel-spanish o el formato: \\shorthandoff{.},
    «shorten <=»/«shorten >=» en TikZ, \\doublespacing, \\% dentro de $...$,
    \\begin{table} dentro de \\begin{landscape}
  * paleta: todo color usado está definido con \\definecolor y no hay códigos sueltos en el cuerpo
Salida: lista de hallazgos con severidad; código de salida 1 si hay ERROR.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ERR, WARN = "ERROR", "AVISO"

try:  # Windows con consola cp1252: no reventar por ✓/✗/–
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def sin_comentarios(texto: str) -> str:
    out = []
    for linea in texto.splitlines():
        # quita comentarios pero conserva \% (porcentaje escapado)
        i, escapado = 0, False
        res = []
        while i < len(linea):
            c = linea[i]
            if c == "\\":
                escapado = not escapado
                res.append(c)
            elif c == "%" and not escapado:
                break
            else:
                escapado = False
                res.append(c)
            i += 1
        out.append("".join(res))
    return "\n".join(out)


def validar(ruta: Path, figures: Path) -> list[tuple[str, str]]:
    raw = ruta.read_text(encoding="utf-8")
    txt = sin_comentarios(raw)
    # \verb|...| se descarta antes de cualquier regla: su contenido es literal, no LaTeX
    txt = re.sub(r"\\verb(.)(.*?)\1", "", txt)
    txt = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", txt, flags=re.S)
    hall: list[tuple[str, str]] = []

    # 1. begin/end
    b = len(re.findall(r"\\begin\{", txt))
    e = len(re.findall(r"\\end\{", txt))
    (hall.append((ERR, f"\\begin/\\end desbalanceados: {b} begin vs {e} end")) if b != e
     else hall.append(("OK", f"\\begin/\\end balanceados ({b}/{e})")))

    # 2. citas
    cuerpo = txt.split("\\chapter{Referencias}")[0] if "\\chapter{Referencias}" in txt else txt
    orden: list[int] = []
    linea_de: dict[int, int] = {}
    for m in re.finditer(r"\\cita\{(\d+)\}(?:\\textendash\\cita\{(\d+)\})?", cuerpo):
        a = int(m.group(1))
        z = int(m.group(2)) if m.group(2) else a
        for n in range(a, z + 1):
            if n not in orden:
                orden.append(n)
                linea_de[n] = cuerpo.count("\n", 0, m.start()) + 1
    labels = sorted({int(x) for x in re.findall(r"\\label\{bib:(\d+)\}", txt)})
    if orden:
        esperado = list(range(1, len(orden) + 1))
        if orden != esperado:
            i = next((i for i, (x, y) in enumerate(zip(orden, esperado)) if x != y), len(esperado) - 1)
            hall.append((ERR, f"citas fuera de orden de primera aparición: en la línea {linea_de[orden[i]]} aparece "
                              f"\\cita{{{orden[i]}}} cuando la siguiente nueva debía ser [{esperado[i]}] "
                              f"(las {i} anteriores van bien)"))
        else:
            hall.append(("OK", f"{len(orden)} citas en orden [1]–[{len(orden)}]"))
        faltan = sorted(set(orden) - set(labels))
        huerf = sorted(set(labels) - set(orden))
        if faltan:
            hall.append((ERR, f"citas sin entrada en Referencias (\\label{{bib:N}}): {faltan}"))
        if huerf:
            hall.append((WARN, f"entradas de Referencias nunca citadas: {huerf}"))
        if labels != list(range(1, len(labels) + 1)):
            hall.append((ERR, f"las etiquetas bib no son consecutivas desde 1: {labels}"))
    else:
        hall.append((WARN, "no hay citas \\cita{N} en el cuerpo"))

    # 3. figuras y tablas
    for tipo in ("fig", "tab"):
        defs = re.findall(r"\\label\{" + tipo + r":([^}]+)\}", txt)
        refs = set(re.findall(r"\\(?:ref|autoref|eqref)\{" + tipo + r":([^}]+)\}", txt))
        dup = {d for d in defs if defs.count(d) > 1}
        if dup:
            hall.append((ERR, f"labels {tipo}: duplicados: {sorted(dup)}"))
        sin_ref = sorted(set(defs) - refs)
        rotas = sorted(refs - set(defs))
        if sin_ref:
            hall.append((WARN, f"{tipo}: con label pero nunca referenciados con \\ref: {sin_ref}"))
        if rotas:
            hall.append((ERR, f"{tipo}: \\ref a labels inexistentes: {rotas}"))
        if not sin_ref and not rotas:
            hall.append(("OK", f"{len(defs)} {tipo}: todos con \\ref y sin rotos"))
    # caption sin label: se exige un \label entre el \caption y el cierre del flotante
    # (o en las 12 líneas siguientes si no hay cierre), porque los captions largos ocupan varias líneas
    lineas = txt.splitlines()
    for i, ln in enumerate(lineas):
        if "\\caption" in ln and "\\captionsetup" not in ln:
            ventana_lineas = []
            for sig in lineas[i : i + 13]:
                ventana_lineas.append(sig)
                if "\\end{figure}" in sig or "\\end{table}" in sig or "\\end{minipage}" in sig:
                    break
            if "\\label{" not in "\n".join(ventana_lineas):
                hall.append((ERR, f"línea {i + 1}: \\caption sin \\label antes del cierre del flotante"))
    # includegraphics
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", txt):
        nombre = m.group(1).strip()
        if "/" in nombre:
            hall.append((ERR, f"\\includegraphics con ruta ({nombre}): usar solo el nombre; las figuras van en Figures/"))
            continue
        candidatos = [figures / nombre] + [figures / (nombre + ext) for ext in (".png", ".pdf", ".jpg", ".jpeg")]
        if not any(c.exists() for c in candidatos):
            hall.append((ERR, f"figura no encontrada en {figures}/: {nombre}"))

    # 4. prohibiciones
    if "\\shorthandoff{." in txt:
        hall.append((ERR, "\\shorthandoff{.} rompe babel-spanish moderno: eliminar (es-nodecimaldot ya lo resuelve)"))
    if re.search(r"shorten\s*[<>]=", txt):
        hall.append((ERR, "TikZ «shorten <=»/«shorten >=» rompe con babel-spanish: usar [xshift=Npt]nodo.east -- [xshift=-Npt]nodo.west"))
    if "\\doublespacing" in txt:
        hall.append((ERR, "\\doublespacing prohibido: el documento usa \\setstretch{1.10} y spacing local"))
    # \% dentro de $...$ en la MISMA línea (se recorre la línea alternando el modo con cada $ no escapado)
    for i, ln in enumerate(lineas):
        en_math, j = False, 0
        while j < len(ln):
            if ln[j] == "\\" and j + 1 < len(ln):
                if ln[j + 1] == "%" and en_math:
                    hall.append((ERR, f"línea {i + 1}: \\% dentro de modo matemático (choca con babel) → escribir 12.5\\,\\% o $<$\\,0.5\\,\\%"))
                    break
                j += 2
                continue
            if ln[j] == "$":
                en_math = not en_math
            j += 1
    for m in re.finditer(r"\\begin\{landscape\}(.*?)\\end\{landscape\}", txt, re.S):
        bloque = m.group(1)
        if "\\begin{table}" in bloque:
            hall.append((ERR, "\\begin{table} dentro de landscape: el patrón del formato es \\captionof{table} en la minipage (un flotante ahí puede desplazar el cuadro o dejar una hoja en blanco)"))
        # cada fila del cuadro de actividades: 1 celda de actividad + 40 semanas = 40 '&' sin escapar
        tab = re.search(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", bloque, re.S)
        if tab:
            filas = re.split(r"\\\\", tab.group(1))
            malas = []
            for fila in filas:
                amps = len(re.findall(r"(?<!\\)&", fila))
                if amps == 0 or "multicolumn{41}" in fila:
                    continue
                esperado = 10 if fila.count("multicolumn{4}") >= 9 else 40
                if amps != esperado:
                    malas.append(f"{amps} '&' (esperados {esperado}) en «{fila.strip()[:40]}…»")
            if malas:
                hall.append((ERR, f"cronograma: {len(malas)} fila(s) con separadores de más o de menos: " + "; ".join(malas[:3])))
    babel = re.search(r"\\usepackage\[([^\]]*)\]\{babel\}", txt)
    if not babel or "spanish" not in babel.group(1):
        hall.append((ERR, "babel con opción spanish no detectado"))
    else:
        for opcion, efecto in (("es-nodecimaldot", "sin ella $3.14$ se imprime «3,14»"), ("es-tabla", "sin ella las tablas se llaman «Cuadro»")):
            if opcion not in babel.group(1):
                hall.append((ERR, f"babel sin la opción {opcion}: {efecto}"))
    for paquete in ("lmodern", "times", "fontspec", "helvet", "libertine", "newtxtext"):
        if re.search(r"\\usepackage(?:\[[^\]]*\])?\{" + paquete + r"\}", txt):
            hall.append((WARN, f"\\usepackage{{{paquete}}} altera la fuente del formato (Times por mathptmx); retirarlo salvo motivo documentado"))
    # Paleta: los colores se usan por NOMBRE definido con \definecolor (la plantilla trae cuatro);
    # un color con código suelto en el cuerpo (\rowcolor[HTML]{...}) escapa a cualquier recoloreo.
    definidos = set(re.findall(r"\\definecolor\{([A-Za-z0-9_]+)\}", txt))
    if len(definidos) < 4:
        hall.append((WARN, f"sólo {len(definidos)} \\definecolor: la plantilla define cuatro nombres de paleta"))
    estandar = {"white", "black", "gray", "grey", "darkgray", "lightgray", "red", "green", "blue", "cyan", "magenta", "yellow",
                "brown", "lime", "olive", "orange", "pink", "purple", "teal", "violet", "none"}
    usados = set()
    for m in re.finditer(r"\\(?:rowcolor|cellcolor|textcolor|color|arrayrulecolor)\{([A-Za-z0-9_]+)(?:![0-9]+)?\}", txt):
        usados.add(m.group(1))
    for m in re.finditer(r"(?:draw|fill|text)=([A-Za-z][A-Za-z0-9_]*)(?:![0-9]+)?", txt):
        usados.add(m.group(1))
    sin_def = sorted(usados - definidos - estandar)
    if sin_def:
        hall.append((ERR, f"colores usados sin \\definecolor: {sin_def}"))
    inline = re.findall(r"\\(?:rowcolor|cellcolor|textcolor|color)\[(?:HTML|rgb|RGB)\]\{", txt)
    if inline:
        hall.append((WARN, f"{len(inline)} color(es) con código suelto en el cuerpo (\\rowcolor[HTML]{{...}}): usar nombres de la paleta"))
    if "\\documentclass[12pt,letterpaper]{report}" not in txt:
        hall.append((ERR, "la clase debe ser \\documentclass[12pt,letterpaper]{report}"))
    if re.search(r"\\section\{\d", txt) is None:
        hall.append((WARN, "no se ven secciones con número embebido (\\section{1.1 …}); secnumdepth=0 no numera solo"))
    # rayas de inciso (— entre espacios) — estilo de la casa: paréntesis o comas
    rayas = [i + 1 for i, ln in enumerate(lineas) if re.search(r"\s—\s|—[^\s—]+—", ln)]
    if rayas:
        hall.append((WARN, f"rayas largas de inciso en {len(rayas)} líneas (p. ej. {rayas[:5]}); preferir paréntesis o comas"))
    return hall


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    ruta = Path(sys.argv[1])
    if "--figures" in sys.argv:
        idx = sys.argv.index("--figures")
        if idx + 1 >= len(sys.argv):
            print("uso: validar.py <archivo.tex> [--figures <carpeta>]")
            return 2
        figures = Path(sys.argv[idx + 1])
    else:
        figures = ruta.parent / "Figures"
    hall = validar(ruta, figures)
    errores = 0
    for sev, msg in hall:
        print(f"[{sev:5}] {msg}")
        errores += sev == ERR
    print(f"\n{'✗' if errores else '✓'} {ruta.name}: {errores} error(es)")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
