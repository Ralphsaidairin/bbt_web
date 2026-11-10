# -*- coding: utf-8 -*-
"""Mapa ilustrado del noroeste para /sucursales.

La costa y las ciudades van en coordenadas reales (latitud, longitud) y se proyectan a un SVG de
VIEW_W x VIEW_H. Para agregar una ciudad con sucursal nueva basta con sumarla a CITIES (el nombre
se compara sin acentos ni mayúsculas contra la ciudad del contacto del almacén).
"""
import math
import unicodedata

# Recuadro del mapa
LON_MIN, LON_MAX = -117.4, -104.0
LAT_MIN, LAT_MAX = 20.4, 32.8
VIEW_W = 620
_KX = math.cos(math.radians(26.5))  # corrige el ancho de los grados de longitud a esta latitud
_SCALE = VIEW_W / ((LON_MAX - LON_MIN) * _KX)
VIEW_H = round((LAT_MAX - LAT_MIN) * _SCALE)

# Costa simplificada (lon, lat): parte continental (Sonora, Sinaloa, Nayarit) y península
MAINLAND = [
    (-114.8, 32.8), (-104.0, 32.8), (-104.0, 20.4), (-105.25, 20.4), (-105.25, 20.6), (-105.3, 21.5),
    (-105.7, 22.5), (-106.4, 23.2), (-107.4, 24.2), (-107.9, 24.6), (-108.6, 25.2), (-109.05, 25.6),
    (-109.4, 26.0), (-109.6, 26.7), (-110.3, 27.3), (-110.9, 27.9), (-111.5, 28.4), (-111.9, 28.8),
    (-112.2, 29.3), (-112.6, 30.0), (-113.1, 30.7), (-113.5, 31.3), (-114.2, 31.5), (-114.8, 31.8),
]
PENINSULA = [
    (-114.8, 31.8), (-114.85, 31.0), (-114.4, 30.0), (-113.55, 28.95), (-112.8, 28.0), (-112.3, 27.3),
    (-112.0, 26.9), (-111.35, 26.0), (-110.9, 25.0), (-110.3, 24.15), (-109.7, 23.7), (-109.7, 23.05),
    (-109.9, 22.9), (-110.25, 23.45), (-111.0, 24.2), (-112.1, 24.8), (-112.3, 25.6), (-113.0, 26.3),
    (-113.6, 26.7), (-114.1, 27.3), (-114.05, 27.95), (-114.3, 28.6), (-115.2, 29.5), (-115.8, 30.3),
    (-116.1, 30.8), (-116.6, 31.85), (-117.1, 32.5), (-117.1, 32.8), (-114.8, 32.8),
]

# Ciudades con sucursal (lat, lon) y desde dónde se dibuja su etiqueta
CITIES = {
    'los mochis': ('Los Mochis', 25.79, -108.99, 'left'),
    'guasave': ('Guasave', 25.57, -108.47, 'right'),
    'culiacan': ('Culiacán', 24.81, -107.39, 'right'),
    'mazatlan': ('Mazatlán', 23.25, -106.41, 'right'),
    'obregon': ('Cd. Obregón', 27.48, -109.93, 'right'),
    'ciudad obregon': ('Cd. Obregón', 27.48, -109.93, 'right'),
    'hermosillo': ('Hermosillo', 29.07, -110.96, 'right'),
    'la paz': ('La Paz', 24.14, -110.31, 'left'),
    'tepic': ('Tepic', 21.50, -104.89, 'left'),
}
HUB = 'los mochis'  # Matriz y Centro de Distribución
FERRY = ((24.14, -110.31), (25.60, -109.05))  # La Paz – Topolobampo (ruta de ferry, solo decorativa)

LABELS = [
    # (texto, lat, lon, tipo, alineación, giro en grados)
    ('Sonora', 30.0, -109.6, 'state', 'middle', 0), ('Sinaloa', 24.15, -104.95, 'state', 'middle', 0),
    ('Nayarit', 22.3, -104.15, 'state', 'end', 0), ('Baja California Sur', 25.3, -114.5, 'state', 'middle', 0),
    ('Golfo de California', 27.4, -111.6, 'sea', 'middle', 50), ('Océano Pacífico', 22.0, -113.2, 'sea', 'middle', 0),
]


def project(lat, lon):
    return (round((lon - LON_MIN) * _KX * _SCALE, 1), round((LAT_MAX - lat) * _SCALE, 1))


def _path(points):
    return 'M' + 'L'.join('%s %s' % project(lat, lon) for lon, lat in points) + 'Z'


def _norm(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode()
    return ' '.join(text.lower().replace('cd.', 'ciudad').split())


def build(cards):
    """Recibe las tarjetas de sucursal (_bbt_website_card) y devuelve lo que dibuja la plantilla."""
    cities = {}
    for card in cards:
        key = _norm(card.get('city'))
        if key not in CITIES:
            continue
        name, lat, lon, side = CITIES[key]
        x, y = project(lat, lon)
        city = cities.setdefault(name, {'key': key.replace(' ', '-'), 'name': name, 'x': x, 'y': y,
                                        'side': side, 'hub': key == HUB, 'branches': []})
        city['branches'].append(card)
    cities = sorted(cities.values(), key=lambda c: (not c['hub'], c['y']))
    hub = next((c for c in cities if c['hub']), None)
    routes = []
    if hub:
        for c in cities:
            if c is hub:
                continue
            # Curva suave desde la matriz hasta cada ciudad
            mx, my = (hub['x'] + c['x']) / 2, (hub['y'] + c['y']) / 2
            dx, dy = c['x'] - hub['x'], c['y'] - hub['y']
            bend = 0.18
            routes.append({'key': c['key'], 'd': 'M%s %sQ%s %s %s %s' % (
                hub['x'], hub['y'], round(mx - dy * bend, 1), round(my + dx * bend, 1), c['x'], c['y'])})
    ferry = False
    if any(c['key'] == 'la-paz' for c in cities):
        (ax, ay), (bx, by) = project(*FERRY[0]), project(*FERRY[1])
        ferry = 'M%s %sQ%s %s %s %s' % (ax, ay, round((ax + bx) / 2 - 6, 1), round((ay + by) / 2 - 26, 1), bx, by)
    labels = []
    for text, lat, lon, kind, anchor, angle in LABELS:
        x, y = project(lat, lon)
        labels.append({'text': text, 'x': x, 'y': y, 'kind': kind, 'anchor': anchor,
                       'transform': 'rotate(%s %s %s)' % (angle, x, y) if angle else False})
    return {
        'w': VIEW_W, 'h': VIEW_H,
        'mainland': _path(MAINLAND), 'peninsula': _path(PENINSULA),
        'cities': cities, 'routes': routes, 'labels': labels, 'ferry': ferry,
        'total': sum(len(c['branches']) for c in cities),
        'unmapped': [card for card in cards if _norm(card.get('city')) not in CITIES],
    }
