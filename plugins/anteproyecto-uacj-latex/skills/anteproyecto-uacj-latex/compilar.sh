#!/usr/bin/env bash
# Compila el anteproyecto tres veces (índices y referencias cruzadas) y resume el log.
# Uso: bash compilar.sh [archivo.tex]   (por defecto plantilla_anteproyecto.tex)
# Requiere pdflatex con: titlesec tocloft fancyhdr hyperref tocbibind chngcntr pdflscape
# mathptmx microtype ragged2e enumitem caption tikz. En Overleaf ya están todos.
set -uo pipefail
TEX="${1:-plantilla_anteproyecto.tex}"
cd "$(dirname "$TEX")"
TEX="$(basename "$TEX")"
BASE="${TEX%.tex}"
for i in 1 2 3; do
  pdflatex -interaction=nonstopmode -halt-on-error "$TEX" > /dev/null 2>&1 || {
    echo "✗ pdflatex falló en la pasada $i. Primer error:"
    /usr/bin/grep -a -n -m1 -A3 '^!' "$BASE.log"
    exit 1
  }
done
LOG="$BASE.log"
errores=$(/usr/bin/grep -a -c '^!' "$LOG")
overfull=$(/usr/bin/grep -a -c 'Overfull' "$LOG")
underfull=$(/usr/bin/grep -a -c 'Underfull' "$LOG")
indef=$(/usr/bin/grep -a -c 'undefined' "$LOG")
paginas=$(/usr/bin/grep -a -oE 'Output written on .*\(([0-9]+) pages' "$LOG" | /usr/bin/grep -oE '[0-9]+ pages' | head -1)
echo "✓ $BASE.pdf · $paginas · errores=$errores · overfull=$overfull · underfull=$underfull · indefinidas=$indef"
[ "$indef" -gt 0 ] && { echo "  ⚠ referencias/citas indefinidas:"; /usr/bin/grep -a 'undefined' "$LOG" | head -5; }
[ "$overfull" -gt 0 ] && { echo "  ⚠ overfull (texto que se sale del margen):"; /usr/bin/grep -a 'Overfull' "$LOG" | head -5; }
exit 0
