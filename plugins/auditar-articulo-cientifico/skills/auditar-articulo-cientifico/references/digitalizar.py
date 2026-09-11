"""Recuperar los datos de un diagrama de dispersión publicado, y diagnosticarlo.

El hallazgo más fuerte de una auditoría suele estar impreso en una figura que
nadie diagnosticó. Ocho puntos leídos de un gráfico bastan para calcular
apalancamiento y distancia de Cook y demostrar que una sola observación sostiene
el resultado estrella del artículo.

Reglas que hacen defendible una digitalización:

1. **Digitaliza lo menos posible.** Si el texto publica las abscisas, úsalas y
   lee del gráfico solo las ordenadas. Cada coordenada que no digitalizas es
   una fuente de error que desaparece.
2. **Calibra por mínimos cuadrados sobre TODOS los rótulos del eje**, no con
   dos extremos, y reporta el residuo máximo en píxeles.
3. **Valídala contra algo que el propio gráfico imprima**: la ecuación de la
   recta, el R², un valor citado en el texto. Sin esa comprobación no es
   evidencia.
4. **Declara la banda de error**: mueve cada lectura un píxel y reporta el
   rango de cada cifra. Una conclusión que no sobrevive a un píxel no se usa.

    python3 digitalizar.py extraer articulo.pdf 7 fig.png

Requiere numpy y Pillow; `extraer` requiere pdfimages (poppler).
"""
import subprocess, sys
import numpy as np

__all__ = ['extraer', 'mascara_color', 'componentes', 'centro', 'etiquetas',
           'calibrar', 'ajuste', 'influencia', 'banda']


def extraer(pdf, pagina, destino_prefijo):
    """Saca los rasters incrustados en una página. Mejor que rasterizar la
    página entera: recupera la imagen original, sin remuestreo."""
    subprocess.run(['pdfimages', '-f', str(pagina), '-l', str(pagina), '-png',
                    pdf, destino_prefijo], check=True)


def mascara_color(A, pred):
    """Máscara booleana según un predicado sobre los canales (R, G, B)."""
    return pred(A[:, :, 0].astype(int), A[:, :, 1].astype(int), A[:, :, 2].astype(int))


def componentes(mask, minimo=40):
    """Componentes conexas de 8 vecinos, de mayor a menor tamaño."""
    H, W = mask.shape
    visto = np.zeros((H, W), bool)
    out = []
    for i in range(H):
        for j in range(W):
            if mask[i, j] and not visto[i, j]:
                pila, px = [(i, j)], []
                visto[i, j] = True
                while pila:
                    y, x = pila.pop(); px.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            u, v = y + dy, x + dx
                            if 0 <= u < H and 0 <= v < W and mask[u, v] and not visto[u, v]:
                                visto[u, v] = True; pila.append((u, v))
                if len(px) >= minimo:
                    out.append(px)
    return sorted(out, key=len, reverse=True)


def centro(px, lado=None):
    """Centro robusto de un marcador. Con `lado`, la ventana lado×lado más
    densa: inmune a que un trazo de la recta se haya fundido con el punto."""
    ys = np.array([a for a, b in px]); xs = np.array([b for a, b in px])
    if lado is None:
        return float(xs.mean()), float(ys.mean())
    mejor = None
    for cx in range(xs.min(), max(xs.min() + 1, xs.max() - lado + 2)):
        for cy in range(ys.min(), max(ys.min() + 1, ys.max() - lado + 2)):
            m = ((xs >= cx) & (xs < cx + lado) & (ys >= cy) & (ys < cy + lado)).sum()
            if mejor is None or m > mejor[0]:
                mejor = (m, cx + lado / 2 - 0.5, cy + lado / 2 - 0.5)
    return mejor[1], mejor[2]


def etiquetas(tinta, banda, eje='x', hueco=20):
    """Centroides de los rótulos de un eje dentro de una banda de filas (eje
    'x') o de columnas (eje 'y'). `hueco` separa un rótulo del siguiente: si
    sale de más o de menos, ajústalo mirando la lista que devuelve."""
    sub = tinta[banda[0]:banda[1], :] if eje == 'x' else tinta[:, banda[0]:banda[1]]
    idx = np.where(sub.any(0 if eje == 'x' else 1))[0]
    if len(idx) == 0:
        return []
    # Agrupar por huecos. Sin atajos: `grupos.append(cur)` seguido de
    # `cur.clear()` mete la MISMA lista en todos los grupos y los vacía, y el
    # fallo no avisa: devuelve tantos centroides como rótulos, todos iguales.
    grupos, cur = [], [int(idx[0])]
    for v in idx[1:]:
        v = int(v)
        if v - cur[-1] <= hueco:
            cur.append(v)
        else:
            grupos.append(cur)
            cur = [v]
    grupos.append(cur)
    out = []
    for g in grupos:
        w = (sub[:, g[0]:g[-1] + 1].sum(0) if eje == 'x' else sub[g[0]:g[-1] + 1, :].sum(1))
        out.append(float((np.arange(g[0], g[-1] + 1) * w).sum() / w.sum()))
    return out


def calibrar(centros, valores):
    """Ajusta píxel = a + b·valor por mínimos cuadrados. Devuelve (a, b, resid_max).

    Un residuo máximo por encima de dos píxeles significa que emparejaste mal
    los rótulos con sus valores, o que un rótulo se partió en dos grupos."""
    centros, valores = np.asarray(centros, float), np.asarray(valores, float)
    b, a = np.polyfit(valores, centros, 1)
    return a, b, float(np.abs(centros - (a + b * valores)).max())


def ajuste(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    b, a = np.polyfit(x, y, 1)
    e = y - (a + b * x)
    r2 = 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, a, r2


def influencia(x, y):
    """h, distancia de Cook y efecto de excluir el punto de mayor abscisa.

    Cortes convencionales: h > 2(k+1)/n y D > 1. Reportar los dos y decir por
    cuál criterio se pronuncia cada uno."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    b, a, r2 = ajuste(x, y)
    e = y - (a + b * x)
    Sxx = ((x - x.mean()) ** 2).sum()
    h = 1 / n + (x - x.mean()) ** 2 / Sxx
    s2 = (e ** 2).sum() / (n - 2)
    D = e ** 2 * h / (2 * s2 * (1 - h) ** 2)
    k = int(np.argmax(x)); m = np.ones(n, bool); m[k] = False
    b2, _, _ = ajuste(x[m], y[m])
    return {'pendiente': b, 'intercepto': a, 'R2': r2, 'h': h, 'D': D,
            'corte_h': 2 * 2 / n, 'influyente': k,
            'pendiente_sin': b2, 'caida_pct': 100 * (1 - b2 / b)}


def banda(x, y, px_x, px_y, reps=4000, semilla=0):
    """Rango de cada cifra al mover cada lectura un píxel en cualquier dirección.

    `px_x` y `px_y` son los píxeles por unidad de dato de cada eje (la b de
    `calibrar`). Pasa px_x=None para las abscisas que NO digitalizaste."""
    rng = np.random.default_rng(semilla)
    x, y = np.asarray(x, float), np.asarray(y, float)
    acc = {k: [] for k in ('pendiente', 'R2', 'h', 'D', 'caida_pct')}
    for _ in range(reps):
        xj = x if px_x is None else x + rng.uniform(-1, 1, len(x)) / px_x
        yj = y + rng.uniform(-1, 1, len(y)) / px_y
        r = influencia(xj, yj)
        k = r['influyente']
        for kk in acc:
            v = r[kk]
            acc[kk].append(v[k] if isinstance(v, np.ndarray) else v)
    return {k: (float(np.min(v)), float(np.max(v))) for k, v in acc.items()}


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == 'extraer':
        extraer(a[1], int(a[2]), a[3]); print('listo')
    else:
        print(__doc__)
