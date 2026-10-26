# -*- coding: utf-8 -*-
from urllib.parse import quote

from odoo import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    bbt_flyer = fields.Image(
        string='Flyer',
        max_width=1600, max_height=1600,
        help='Imagen de la vacante (el flyer que hace RH). Se muestra en /jobs y en la página de la vacante. '
             'Si se deja vacío, el sitio dibuja una tarjeta con el nombre del puesto.',
    )
    bbt_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Sucursal',
        domain=[('bbt_published', '=', True)],
        help='Sucursal donde está la vacante. Se muestra en la tarjeta del sitio web.',
    )
    # Odoo trae como descripción una página de ejemplo con fotos y textos de otra empresa;
    # aquí empieza con una estructura sencilla que RH llena desde el editor.
    website_description = fields.Html(default=lambda self: self._bbt_default_website_description())
    # Odoo trae "2 días hábiles / 1 llamada / 1 entrevista": se deja vacío para que RH escriba su proceso real.
    job_details = fields.Html(default=False)

    def _bbt_default_website_description(self):
        return self.env['ir.qweb']._render('website_babatsa.job_default_description', raise_if_not_found=False)

    def _bbt_location(self):
        """Sucursal pública de la vacante; si no tiene, la ciudad de su dirección de trabajo."""
        self.ensure_one()
        warehouse = self.sudo().bbt_warehouse_id
        if warehouse:
            return warehouse.bbt_public_name or warehouse.name
        return self.sudo().address_id.city or ''

    def _bbt_cv_mailto(self, email):
        self.ensure_one()
        return 'mailto:%s?subject=%s' % (email, quote('CV - %s' % self.name))
