# -*- coding: utf-8 -*-
from . import models
from . import controllers

# Menús que el módulo agrega al menú principal de cada sitio web.
# (nombre, url, secuencia)
BBT_MENUS = [
    ('Nosotros', '/nosotros', 20),
    ('Productos', '/productos', 30),
    ('Marcas', '/marcas', 40),
    ('Servicios', '/servicios', 50),
    ('Sucursales', '/sucursales', 60),
    ('Contacto', '/contacto', 70),
]


def post_init_hook(env):
    """Crea los menús en cada sitio web existente.

    Los registros website.menu de datos XML solo se copian a sitios nuevos;
    por eso se crean aquí directamente bajo el menú raíz de cada sitio.
    """
    Menu = env['website.menu']
    for website in env['website'].search([]):
        root = website.menu_id
        if not root:
            continue
        for name, url, sequence in BBT_MENUS:
            exists = Menu.search([('url', '=', url), ('website_id', '=', website.id)], limit=1)
            if not exists:
                Menu.create({
                    'name': name,
                    'url': url,
                    'parent_id': root.id,
                    'website_id': website.id,
                    'sequence': sequence,
                })
