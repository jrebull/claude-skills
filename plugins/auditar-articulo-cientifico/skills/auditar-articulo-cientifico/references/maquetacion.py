"""Defectos de maquetación del PDF entregable que el ojo pasa por alto.

Se ejecuta sobre el PDF ya compilado, no sobre el .tex. Dos defectos reales de
la Semana 5 que sobrevivieron varias revisiones humanas y una auditoría ciega:

- un `longtable` emitiendo su encabezado **suelto arriba de una página**, con
  filete, títulos de columna y ninguna fila debajo, encima del rótulo de la
  sección siguiente;
- una nota partida entre dos páginas con una figura flotante en medio, de modo
  que la cola aparece después de la figura, desconectada de su cabeza.

    python3 maquetacion.py main.pdf
    python3 maquetacion.py main.pdf "Dato Contenido" "Tipo Contenido"

Requiere pdfinfo y pdftotext (poppler).
"""
import re, subprocess, sys

__all__ = ['paginas', 'texto', 'huerfanos', 'huecos']

# Encabezados típicos: primera palabra de la fila de títulos de cada longtable.
POR_DEFECTO = ('Dato Contenido', 'Tipo Contenido', 'Dimensión Evidencia',
               'Verificación Resultado', 'Punto de la consigna')


def paginas(pdf):
    s = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
    return int(re.search(r'^Pages:\s+(\d+)', s, re.M).group(1))


def texto(pdf, p):
    return subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'],
                          capture_output=True, text=True).stdout


def huerfanos(pdf, encabezados=POR_DEFECTO, encabezado_pagina='Ficha de auditoría'):
    """Páginas que ABREN con un encabezado de tabla y siguen con otra cosa.

    Si el encabezado aparece arriba y luego viene un rótulo de sección, ese
    encabezado no gobierna ninguna fila: es basura tipográfica.

    Causa habitual: un `longtable` que abre justo después de un macro de
    sección con `\\needspace`. No se arregla quitando `\\nopagebreak`. Se arregla
    dando al `\\needspace` sitio para el rótulo, el título, el encabezado de la
    tabla y su primera fila, y aplicándolo SOLO a los bloques que abren con
    tabla: hacerlo global desperdicia páginas.
    """
    malas = []
    for p in range(1, paginas(pdf) + 1):
        L = [l.strip() for l in texto(pdf, p).split('\n') if l.strip()]
        L = [l for l in L if l != encabezado_pagina]
        if not L: continue
        cabeza, resto = ' '.join(L[:2]), ' '.join(L[2:8])
        if any(h in cabeza for h in encabezados) and re.search(r'Apartado|Anexo|Secci', resto):
            malas.append((p, cabeza[:70]))
    return malas


def huecos(pdf, umbral=0.33):
    """Páginas cuyo texto ocupa menos de `umbral` de las líneas de la más llena.

    Aproximación deliberadamente burda: cuenta líneas de texto, así que una
    página con una figura grande sale como hueco. Sirve para señalar candidatas
    y mirarlas, no para decidir.
    """
    n = paginas(pdf)
    cuenta = [len([l for l in texto(pdf, p).split('\n') if l.strip()]) for p in range(1, n + 1)]
    tope = max(cuenta) or 1
    return [(p + 1, c, round(c / tope, 2)) for p, c in enumerate(cuenta) if c / tope < umbral]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    pdf = sys.argv[1]
    enc = tuple(sys.argv[2:]) or POR_DEFECTO
    n = paginas(pdf)
    h = huerfanos(pdf, enc)
    print(f'{pdf}: {n} páginas')
    print(f'encabezados huérfanos: {len(h)}')
    for p, c in h: print(f'   página {p} -> {c}')
    print('páginas poco llenas (revisar a ojo):')
    for p, c, f in huecos(pdf): print(f'   página {p}: {c} líneas ({f:.0%} de la más llena)')
