"""Barridos algebraicos sobre las celdas publicadas de un artículo de regresión.

La idea de fondo: un artículo que publica b, R², p y correlaciones está
**sobredeterminado**. Esas cifras tienen que satisfacer identidades exactas
entre sí, y cada identidad rota es un hallazgo verificable que no depende de
ninguna opinión sobre el trabajo.

Contrato de una celda (un dict por modelo publicado; faltantes en None):
    tab, fila, col   etiquetas para poder citar la ubicación exacta
    b, pb            coeficiente y su valor p
    R2, p            R² del modelo y su valor p
    r, pr            Pearson y su valor p
    rho, prho        Spearman y su valor p
    b1, pb1, b2, pb2 para modelos de dos predictores

⚠️ Todas las funciones propagan la caja de redondeo. Un hallazgo que no
sobrevive a la caja no es un hallazgo: es una cifra redondeada.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estadistica_pura import p_t, caja, spearman_exacto

__all__ = ['identidad_R2', 'signo', 'p_redundante', 'cota_t', 'spearman_umbral',
           'pearson_vs_spearman', 'multiplicidad', 'reconstruir_n']


def _dec(x, dec=None):
    """Decimales con que se imprimió una cifra.

    ⚠️ NO deducirlos de repr(): el artículo imprime «0.90» y float lo devuelve
    como 0.9, así que la caja saldría diez veces más ancha y el barrido
    silenciosamente más permisivo. Pasa siempre `dec` explícito, leído de cómo
    imprime la tabla. La deducción solo es un último recurso.
    """
    if dec is not None:
        return dec
    s = f'{x!r}'
    return len(s.split('.')[1]) if '.' in s else 0


def identidad_R2(celdas, dec=2):
    """En regresión simple R² = r². Roto => una de las dos celdas es errata.

    Devuelve las celdas incompatibles incluso propagando el redondeo. Cuando
    falla, mirar qué valor p acompaña a cuál cifra: eso dice cuál es la errónea.
    """
    malas = []
    for c in celdas:
        if c.get('R2') is None or c.get('r') is None: continue
        rlo, rhi = caja(abs(c['r']), _dec(c['r'], dec))
        Rlo, Rhi = caja(c['R2'], _dec(c['R2'], dec))
        r2lo = 0.0 if rlo <= 0 else rlo * rlo      # la caja puede cruzar el cero
        if not (r2lo <= Rhi and rhi * rhi >= Rlo):
            malas.append((c, c['r'] ** 2, c['R2']))
    return malas


def signo(celdas):
    """En regresión simple con intercepto b = r·s_y/s_x: los signos coinciden.

    Se omiten las celdas con b impreso como 0.00, donde el signo no es legible.
    """
    return [c for c in celdas
            if c.get('b') not in (None, 0.0) and c.get('r') not in (None, 0.0)
            and c['b'] * c['r'] < 0]


def p_redundante(celdas, dec=2, alfa=0.05):
    """En regresión simple p(b) = p(modelo) = p(Pearson): es la misma prueba.

    Devuelve (celda, valores, rango, cruza_umbral, benigna). `benigna` es que
    todo el desacuerdo quepa en una unidad de la última cifra impresa: eso es
    redondeo. Lo demás es un hallazgo, y que además cruce el alfa lo agrava.
    """
    unidad = 10.0 ** (-dec)
    out = []
    for c in celdas:
        v = {k: c[k] for k in ('pb', 'p', 'pr') if c.get(k) is not None}
        if len(set(v.values())) > 1:
            rango = max(v.values()) - min(v.values())
            cruza = (min(v.values()) < alfa) != (max(v.values()) < alfa)
            out.append((c, v, rango, cruza, rango <= unidad * 1.0001))
    return out


def cota_t(celdas, n, k=2, dec=2):
    """Cota algebraica: t_j² <= df·R²/(1-R²) para cualquier coeficiente.

    El R² total limita cuán significativo puede ser un coeficiente suelto. Un
    p(b) publicado por debajo de esa cota es aritméticamente imposible: no puede
    provenir del ajuste que la misma fila reporta.
    """
    df = n - k - 1
    malas = []
    for c in celdas:
        if c.get('R2') is None: continue
        Rhi = caja(c['R2'], _dec(c['R2'], dec))[1]          # el borde más favorable
        if Rhi >= 1: continue
        tmax = math.sqrt(df * Rhi / (1 - Rhi))
        pmin = p_t(tmax, df)
        for kk in ('pb1', 'pb2', 'pb'):
            if c.get(kk) is not None and caja(c[kk], _dec(c[kk], dec))[1] < pmin:
                malas.append((c, kk, c[kk], pmin, tmax))
    return malas


def spearman_umbral(celdas, n, alfa=0.05, dec=2):
    """Compara los rho publicados contra la nula EXACTA de permutación.

    Con n pequeño la nula de rho es discreta y su crítico no es el de Pearson.
    Devuelve (cambian, borde, fuera_de_reticula):
      cambian  la caja de redondeo del rho impreso queda ENTERA por debajo del
               crítico, así que el artículo lo declara significativo y la
               prueba exacta no lo respalda
      borde    la caja cruza el crítico. Ojo: dentro de la retícula sin empates
               puede haber un único valor alcanzable en esa caja, y si es el
               propio crítico, la celda sí rechaza. Mirar antes de acusar.

    ⚠️ `fuera_de_reticula` es la cifra que gobierna la conclusión: si muchos
    coeficientes no caen en la retícula alcanzable sin empates, hay empates en
    los datos, la nula sin empates no aplica y ninguna celda queda resuelta.
    """
    ret, cola, crit, _ = spearman_exacto(n)
    if crit is None:
        raise ValueError(f'con n = {n} ningún valor de rho alcanza el {alfa:.0%}: '
                         'la prueba no puede rechazar y no hay umbral que comparar')
    cambian, borde, fuera = [], [], []
    for c in celdas:
        rho, pr = c.get('rho'), c.get('prho')
        if rho is None: continue
        lo, hi = caja(abs(rho), _dec(rho, dec))
        dentro = [r for r in ret if lo <= float(r) < hi]
        if not dentro:
            fuera.append(c)
        if pr is None: continue
        if pr < alfa and hi <= float(crit):
            cambian.append((c, float(crit)))
        elif pr < alfa and lo < float(crit) <= hi:
            borde.append((c, float(crit), [float(r) for r in ret if lo <= float(r) < hi]))
    return cambian, borde, fuera


def pearson_vs_spearman(celdas, alfa=0.05):
    """La discrepancia entre ambos ES la señal diagnóstica, y suele ignorarse.

    Un Pearson y un Spearman que caen en lados opuestos del alfa, o que tienen
    signos opuestos, apuntan a no linealidad o a una observación influyente.
    Si el artículo publica los dos y nunca comenta una discrepancia, tenía el
    diagnóstico impreso en sus propias tablas y no lo miró.
    """
    lados = [c for c in celdas
             if None not in (c.get('pr'), c.get('prho'))
             and (c['pr'] < alfa) != (c['prho'] < alfa)]
    signos = [c for c in celdas
              if c.get('r') not in (None, 0.0) and c.get('rho') not in (None, 0.0)
              and c['r'] * c['rho'] < 0]
    return lados, signos


def multiplicidad(n_pruebas, n_significativas, alfa=0.05):
    """Esperadas bajo nulo global, umbral de Bonferroni y exceso observado.

    Contar pruebas DISTINTAS, no celdas: en regresión simple p(b), p(modelo) y
    p(Pearson) son la misma prueba impresa tres veces.
    """
    if n_pruebas <= 0:
        raise ValueError('no hay pruebas que contar')
    return {'esperadas': n_pruebas * alfa,
            'observadas': n_significativas,
            'bonferroni': alfa / n_pruebas}


def reconstruir_n(R2, F, k=1, dec_R2=2, dec_F=0):
    """Despeja n de F = (R²/k)/((1-R²)/(n-k-1)) propagando ambas cajas.

    La vía más barata para recuperar el tamaño de muestra cuando el artículo no
    lo declara. Confirmarla siempre con una segunda vía independiente: colas de
    cuatro decimales, o el diseño descrito en métodos.
    """
    Rlo, Rhi = caja(R2, dec_R2)
    Flo, Fhi = caja(F, dec_F)
    if Rlo <= 0 or Rhi >= 1:
        raise ValueError(f'R2={R2} con esa precisión no despeja n: la caja '
                         f'[{Rlo:.4f}, {Rhi:.4f}] toca 0 o 1')
    lo = k * Flo * (1 - Rhi) / Rhi + k + 1
    hi = k * Fhi * (1 - Rlo) / Rlo + k + 1
    return lo, hi, [m for m in range(2, 2000) if lo <= m <= hi]


if __name__ == '__main__':
    print(__doc__)
