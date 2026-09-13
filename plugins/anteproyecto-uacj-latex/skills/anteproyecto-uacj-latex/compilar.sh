#!/usr/bin/env bash
# Compila el anteproyecto tres veces (índices y referencias cruzadas) y aplica el gate de entrega:
# 0 errores, 0 overfull, 0 referencias/citas indefinidas. Sale con 1 si el gate no pasa.
# Uso: bash compilar.sh [archivo.tex]   (por defecto plantilla_anteproyecto.tex junto al script)
# Requiere pdflatex (Overleaf o TeX Live) con: titlesec tocloft fancyhdr hyperref tocbibind chngcntr
# pdflscape mathptmx microtype ragged2e enumitem caption tikz. Necesita bash y grep (Git Bash en Windows).
set -uo pipefail
TEX="${1:-$(dirname "$0")/plantilla_anteproyecto.tex}"
if [ ! -f "$TEX" ]; then
  echo "✗ no existe el archivo: $TEX" >&2
  exit 2
fi
cd "$(dirname "$TEX")" || exit 2
TEX="$(basename "$TEX")"
BASE="${TEX%.tex}"
LOG="$BASE.log"
for i in 1 2 3; do
  if ! pdflatex -interaction=nonstopmode -halt-on-error "$TEX" > /dev/null 2>&1; then
    echo "✗ pdflatex falló en la pasada $i. Primer error del log:"
    grep -a -n -m1 -A3 '^!' "$LOG"
    exit 1
  fi
done
errores=$(grep -a -c '^!' "$LOG")
overfull=$(grep -a -c 'Overfull' "$LOG")
underfull=$(grep -a -c 'Underfull' "$LOG")
indef=$(grep -a -c 'undefined' "$LOG")
paginas=$(grep -a -oE 'Output written on .*\(([0-9]+) pages' "$LOG" | grep -oE '[0-9]+ pages' | head -1)
echo "$BASE.pdf · $paginas · errores=$errores · overfull=$overfull · underfull=$underfull · indefinidas=$indef"
rc=0
if [ "$indef" -gt 0 ]; then
  echo "  ✗ referencias o citas indefinidas (\\ref o \\cita a algo que no existe):"
  grep -a 'undefined' "$LOG" | head -5
  rc=1
fi
if [ "$overfull" -gt 0 ]; then
  echo "  ✗ overfull: texto o tabla que se sale del margen (revisar en el PDF):"
  grep -a 'Overfull' "$LOG" | head -5
  rc=1
fi
[ "$underfull" -gt 0 ] && echo "  · underfull=$underfull (cosmético: líneas o columnas con espacio de más; no bloquea)"
[ "$rc" -eq 0 ] && echo "✓ gate de entrega superado" || echo "✗ gate de entrega NO superado"
exit "$rc"
