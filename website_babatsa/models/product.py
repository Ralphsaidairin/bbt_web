# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.http import request


def _bbt_catalog_mode():
    """True si el sitio actual está en modo catálogo (sin precios ni carrito)."""
    return bool(request and getattr(request, 'website', None) and request.website.bbt_catalog_mode)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bbt_brand_id = fields.Many2one(
        'babatsa.brand', string='Marca (sitio web)',
        help='Marca que se muestra en la ficha del producto en el sitio web.',
    )

    def _get_combination_info(self, *args, **kwargs):
        # Modo catálogo: se reutiliza el mecanismo de Odoo para "precio en cero":
        # oculta precio, cantidad y botón de carrito, y muestra el bloque de contacto.
        info = super()._get_combination_info(*args, **kwargs)
        website = self.env['website'].get_current_website()
        if website.bbt_catalog_mode:
            info['prevent_zero_price_sale'] = True
            info['compare_list_price'] = 0
        return info

    def _website_show_quick_add(self):
        if _bbt_catalog_mode():
            return False
        return super()._website_show_quick_add()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _website_show_quick_add(self):
        if _bbt_catalog_mode():
            return False
        return super()._website_show_quick_add()

    def _is_add_to_cart_allowed(self):
        if _bbt_catalog_mode():
            return False
        return super()._is_add_to_cart_allowed()
