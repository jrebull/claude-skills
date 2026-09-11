"""Colas exactas de t, F y Pearson, y la nula exacta de Spearman, en Python puro.

Sin scipy. Un artículo se audita recalculando sus valores p, y el entorno donde
se audita casi nunca tiene scipy instalado. La beta incompleta por fracción
continua (Numerical Recipes) da doce cifras, de sobra para comparar contra
valores publicados con dos o cuatro decimales.

    python3 estadistica_pura.py t 2.45 6
    python3 estadistica_pura.py r 0.96 8
    python3 estadistica_pura.py F 43 1 6
    python3 estadistica_pura.py spearman 8
"""
import math, sys
from fractions import Fraction
from itertools import permutations
from collections import Counter

__all__ = ['ibeta', 'p_t', 'p_F', 'p_pearson', 'spearman_exacto', 'caja']


def _betacf(a, b, x, itmax=300, eps=3e-16, fpmin=1e-300):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < fpmin: d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; c = 1.0 + aa / c
        if abs(d) < fpmin: d = fpmin
        if abs(c) < fpmin: c = fpmin
        d = 1.0 / d; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; c = 1.0 + aa / c
        if abs(d) < fpmin: d = fpmin
        if abs(c) < fpmin: c = fpmin
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def ibeta(a, b, x):
    """Función beta incompleta regularizada I_x(a, b)."""
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    lb = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
          + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1.0 - x) / b


def p_t(t, df):
    """Valor p bilateral de una t de Student."""
    df = float(df)
    return ibeta(df / 2.0, 0.5, df / (df + float(t) ** 2))


def p_F(F, df1, df2):
    """Cola superior de una F de Snedecor."""
    F, df1, df2 = float(F), float(df1), float(df2)
    if F <= 0: return 1.0
    return ibeta(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * F))


def p_pearson(r, n):
    """Valor p bilateral de un coeficiente de Pearson con n observaciones."""
    r = abs(float(r))
    if r >= 1.0: return 0.0
    return p_t(r * math.sqrt((n - 2) / (1.0 - r * r)), n - 2)


def spearman_exacto(n):
    """Nula exacta de rho por enumeración de las n! permutaciones (n <= 10).

    Devuelve (reticula, cola, critico, tamano):
      reticula  lista descendente de los valores de rho alcanzables SIN empates
      cola      dict {rho: P(|rho_nula| >= rho)}
      critico   menor valor de la retícula cuya cola bilateral es <= 0.05,
                o None si NINGUNO lo es: con n <= 5 ni siquiera rho = 1
                alcanza el 5 %, y ahí la prueba no puede rechazar nunca
      tamano    la cola exacta en ese punto, que NO es 0.05

    Con empates la retícula es más densa y esta nula no aplica: comprobar
    siempre cuántos coeficientes publicados caen fuera de ella.
    """
    if n > 10:
        raise ValueError('n! se dispara; para n > 10 usa una aproximación')
    base = list(range(n))
    cnt = Counter()
    for p in permutations(base):
        cnt[sum((a - b) ** 2 for a, b in zip(base, p))] += 1
    tot = sum(cnt.values())
    den = n * (n * n - 1)
    rho = {S: Fraction(1) - Fraction(6 * S, den) for S in cnt}
    reticula = sorted(set(rho.values()), reverse=True)
    cola = {r: sum(c for S, c in cnt.items() if abs(rho[S]) >= r) / tot
            for r in reticula if r > 0}
    critico = tamano = None
    for r in reticula:
        if r <= 0: break
        if cola[r] <= 0.05:
            critico, tamano = r, cola[r]
    return reticula, cola, critico, tamano


def caja(valor, decimales):
    """Intervalo del que pudo venir una cifra impresa con esos decimales.

    La regla de oro de estas auditorías: nunca tratar un número redondeado como
    puntual. Propagar la caja y quedarse solo con lo que sobrevive a ella.
    """
    h = 0.5 * 10 ** (-decimales)
    return (valor - h, valor + h)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == 't':
        print(f'p bilateral = {p_t(float(a[1]), float(a[2])):.8f}')
    elif a[0] == 'r':
        print(f'p bilateral = {p_pearson(float(a[1]), int(a[2])):.8f}')
    elif a[0] == 'F':
        print(f'cola superior = {p_F(float(a[1]), float(a[2]), float(a[3])):.8f}')
    elif a[0] == 'spearman':
        n = int(a[1])
        ret, cola, crit, tam = spearman_exacto(n)
        print(f'n = {n}: {len(ret)} valores alcanzables sin empates')
        print(f'critico bilateral 5% = {float(crit):.6f}  (cola exacta {tam:.6f})')
        print('cinco valores mas altos y su cola:')
        for r in ret[:6]:
            if r > 0: print(f'   rho = {float(r):.6f}   P(|rho| >= r) = {cola[r]:.6f}')
    else:
        print(__doc__)
