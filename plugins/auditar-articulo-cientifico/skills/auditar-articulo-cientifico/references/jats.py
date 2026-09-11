"""Texto completo y tablas de un artículo, en XML JATS, desde Europe PMC.

El PDF de un artículo sirve para leerlo; el XML JATS sirve para auditarlo,
porque trae las tablas como celdas y no como una imagen de texto. Sin esto no
hay auditoría celda por celda.

    python3 jats.py PMC11728780 art.xml     # descarga
    python3 jats.py art.xml                 # inspecciona lo descargado

Endpoint:
    https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML

Si el artículo no está en Europe PMC (no es de acceso abierto), no hay atajo:
transcribir las tablas a mano y verificar la transcripción con un segundo pase.
"""
import html, re, sys, urllib.request

__all__ = ['descargar', 'cargar', 'tablas', 'texto_plano', 'num', 'buscar']

URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/{}/fullTextXML'


def descargar(pmcid, destino):
    with urllib.request.urlopen(URL.format(pmcid), timeout=60) as r:
        datos = r.read()
    open(destino, 'wb').write(datos)
    return datos.decode('utf-8', 'replace')


def cargar(ruta):
    return open(ruta, encoding='utf-8').read()


def _txt(x):
    x = re.sub(r'</?(italic|sup|sub|bold|underline)>', '', x)
    x = re.sub(r'<[^>]+>', ' ', x)
    return html.unescape(x).replace(' ', ' ').strip()


def tablas(xml):
    """{etiqueta: [[celda, ...], ...]} con una lista de filas por tabla.

    Ojo con los rowspan y colspan: esta función NO los expande, devuelve las
    celdas tal como vienen. Antes de mapear filas a variables, imprime las
    primeras filas de cada tabla y cuenta columnas.
    """
    out = {}
    for m in re.finditer(r'<table-wrap.*?</table-wrap>', xml, re.S):
        t = m.group(0)
        lab = re.search(r'<label>(.*?)</label>', t, re.S)
        lab = _txt(lab.group(1)) if lab else f'tabla-{len(out) + 1}'
        filas = []
        for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', t, re.S):
            filas.append([_txt(c) for c in
                          re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row.group(1), re.S)])
        out[lab] = filas
    return out


def texto_plano(xml):
    """Todo el texto en una sola línea, para afirmaciones de ausencia."""
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', xml)))


_MILES = re.compile(r'^-?\d{1,3}(,\d{3})+(\.\d+)?$')
_DUROS = '\u00a0\u2007\u202f\u2009'          # espacios que no son el espacio


def num(s, coma='miles'):
    """Float de una celda, normalizando el menos tipográfico.

    ⚠️ El fallo más caro de esta auditoría: los artículos imprimen U+2212
    (MINUS SIGN) y no el guion ASCII. `float()` lo rechaza en silencio y un
    barrido de contradicciones de signo devuelve cero hallazgos sin avisar.

    ⚠️ La coma. Con `coma='miles'` (el caso de un artículo en inglés) solo se
    quita cuando separa millares de verdad: «1,500» es 1500, pero «0,05» NO se
    convierte en 5, se devuelve None para que el fallo se vea. Si el artículo
    escribe decimales con coma, pásale `coma='decimal'` a propósito.
    """
    if s is None:
        return None
    for ch in ('\u2212', '\u2013', '\u2014'):
        s = s.replace(ch, '-')
    for ch in _DUROS:
        s = s.replace(ch, ' ')
    s = s.strip()
    if ',' in s:
        if coma == 'decimal':
            s = s.replace(',', '.')
        elif _MILES.match(s):
            s = s.replace(',', '')
        else:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def buscar(xml, *terminos):
    """Cuenta apariciones en TODO el XML: cuerpo, pies, leyendas, suplementario.

    Una afirmación de ausencia («el artículo nunca reporta residuos») es
    falsable y barata de refutar. Comprobarla sobre el texto completo, nunca
    sobre el cuerpo recortado.
    """
    t = texto_plano(xml).lower()
    return {k: t.count(k.lower()) for k in terminos}


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0].upper().startswith('PMC'):
        xml = descargar(a[0], a[1]); print(f'{len(xml)} caracteres -> {a[1]}')
    elif len(a) == 1:
        xml = cargar(a[0])
    else:
        print(__doc__); sys.exit(0)
    T = tablas(xml)
    print(f'\n{len(T)} tablas')
    for lab, filas in T.items():
        print(f'\n=== {lab}: {len(filas)} filas, {max(len(f) for f in filas)} columnas max')
        for f in filas[:3]:
            print('   ', f)
