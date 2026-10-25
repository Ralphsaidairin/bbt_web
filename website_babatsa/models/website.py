# -*- coding: utf-8 -*-
from odoo import fields, models

BBT_HEADER_STYLES = [
    ('capsula', 'Cápsula flotante'),
    ('doble', 'Doble barra con mega menú'),
    ('completo', 'Menú a pantalla completa'),
]


class Website(models.Model):
    _inherit = 'website'

    bbt_header_style = fields.Selection(
        selection=BBT_HEADER_STYLES,
        string='Estilo de encabezado',
        default='capsula',
        required=True,
        help='Diseño del encabezado del sitio. Para comparar sin guardar: agregar ?navbar=doble a la dirección.',
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_bbt_header_style = fields.Selection(
        related='website_id.bbt_header_style', readonly=False)
