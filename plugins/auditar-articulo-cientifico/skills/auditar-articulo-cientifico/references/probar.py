"""Batería de regresión del skill. Ejecutarla antes de confiar en cualquier módulo.

Comprueba las cinco herramientas contra la auditoría de `microorganisms-12-02661`
(dengue en México, MDPI 2024), cuyas cifras están verificadas de forma
independiente. Si una prueba falla, el módulo cambió y las cifras del manual ya
no valen.

    python3 probar.py [ruta/al/fulltext.xml] [ruta/al/raster_figura.png]

Sin argumentos comprueba solo lo que no necesita los archivos del artículo.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estadistica_pura as ep, jats, barridos as ba, maquetacion as mq

FALLOS = []


def ok(cond, desc):
    print(('  OK   ' if cond else '  FALLA ') + desc)
    if not cond:
        FALLOS.append(desc)


def sin_archivos():
    print('=== estadistica_pura ===')
    _, _, crit, tam = ep.spearman_exacto(8)
    ok(abs(float(crit) - 0.7380952) < 1e-6 and abs(tam - 0.0458333) < 1e-6,
       f'crítico de Spearman n=8 = {float(crit):.6f} con cola {tam:.6f}')
    ok(abs(ep.p_pearson(0.96, 8) - 0.00015524) < 1e-8, 'p(r=0.96, n=8) = 0.00015524')
    ok(abs(ep.p_F(43, 1, 6) - 0.00060220) < 1e-8, 'cola de F(1,6)=43 = 0.00060220')
    ok(ep.spearman_exacto(4)[2] is None, 'con n=4 no hay crítico al 5 % y lo devuelve como None')
    ok(abs(ep.caja(0.03, 2)[0] - 0.025) < 1e-9, 'caja de 0.03 con dos decimales')

    print('=== jats.num ===')
    ok(jats.num('−11.82') == -11.82, 'menos tipográfico U+2212')
    ok(jats.num('1,500') == 1500.0, 'coma de millares')
    ok(jats.num('0,05') is None, 'coma decimal NO se vuelve 5 en silencio')
    ok(jats.num('0,05', coma='decimal') == 0.05, 'coma decimal cuando se pide a propósito')

    print('=== barridos ===')
    ok(ba.reconstruir_n(0.88, 43)[2] == [8], 'n reconstruido de R²=0.88 y F=43 es 8')
    try:
        ba.reconstruir_n(1.00, 43); ok(False, 'R²=1 debe avisar')
    except ValueError:
        ok(True, 'R²=1 avisa en vez de devolver un intervalo sin sentido')
    try:
        ba.multiplicidad(0, 0); ok(False, 'cero pruebas debe avisar')
    except ValueError:
        ok(True, 'cero pruebas avisa en vez de dividir por cero')
    try:
        ba.spearman_umbral([{'rho': 0.9, 'prho': 0.01}], 4); ok(False, 'n=4 debe avisar')
    except ValueError:
        ok(True, 'umbral de Spearman con n=4 avisa de que no hay umbral')


def con_xml(ruta):
    print('=== jats sobre el artículo real ===')
    x = jats.cargar(ruta)
    T = jats.tablas(x)
    ok(len(T) == 6, f'{len(T)} tablas extraídas (esperadas 6)')
    ok(jats.buscar(x, 'Cook')['Cook'] == 0, '«Cook» no aparece ni una vez en todo el XML')
    ok(jats.buscar(x, 'collinearity')['collinearity'] == 1, '«collinearity» aparece exactamente una vez')


def con_figura(ruta):
    import numpy as np
    from PIL import Image
    import digitalizar as dg
    print('=== digitalizar, flujo completo y a ciegas ===')
    A = np.asarray(Image.open(ruta).convert('RGB'))
    tinta = dg.mascara_color(A, lambda r, g, b: r + g + b < 700)
    azul = dg.mascara_color(A, lambda r, g, b: (b > 130) & (b - r > 35) & (b - g > 15))
    cx = dg.etiquetas(tinta, (347, 365), 'x', hueco=20)
    cy = [v for v in dg.etiquetas(tinta, (40, 78), 'y', hueco=4) if v < 345]
    ok(len(cx) == 11 and len(cy) == 7, f'{len(cx)} rótulos en X y {len(cy)} en Y')
    ok(len(set(round(v, 1) for v in cx)) == len(cx),
       'los centroides son distintos entre sí (el agrupador no aliasa las listas)')
    ax, bx, rx = dg.calibrar(cx, np.arange(10, 21, 1.0))
    ay, by, ry = dg.calibrar(cy, np.arange(1.20, -0.01, -0.20))
    ok(rx < 2 and ry < 2, f'calibración con residuo máximo {rx:.2f} y {ry:.2f} px')
    pts = sorted(dg.centro(p, lado=8) for p in dg.componentes(azul, minimo=40))
    ok(len(pts) == 8, f'{len(pts)} marcadores hallados (esperados 8)')
    X = np.array([(p - ax) / bx for p, _ in pts])
    Y = np.array([(q - ay) / by for _, q in pts])
    b, a, r2 = dg.ajuste(X, Y)
    ok(abs(b - 0.4185) < 0.005 and abs(r2 - 0.912) < 0.005,
       f'ajuste {b:.4f} / {r2:.4f} contra 0.4185 / 0.912 impresos en la figura')
    r = dg.influencia(X, Y); k = r['influyente']
    ok(r['h'][k] > r['corte_h'] and r['D'][k] > 1,
       f"h {r['h'][k]:.3f} sobre el corte {r['corte_h']:.2f}, y D de Cook {r['D'][k]:.2f} sobre 1")


if __name__ == '__main__':
    sin_archivos()
    a = sys.argv[1:]
    if len(a) > 0 and os.path.exists(a[0]): con_xml(a[0])
    if len(a) > 1 and os.path.exists(a[1]): con_figura(a[1])
    print()
    print('TODO EN ORDEN' if not FALLOS else f'{len(FALLOS)} PRUEBAS FALLAN:')
    for f in FALLOS: print('   -', f)
    sys.exit(1 if FALLOS else 0)
