# -*- coding: utf-8 -*-
import re
import unicodedata

from odoo import api, fields, models


def _bbt_slug(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


class BabatsaBrandLine(models.Model):
    _name = 'babatsa.brand.line'
    _description = 'Línea de producto (Marcas Babatsa)'
    _order = 'sequence, name'

    name = fields.Char(string='Línea', required=True, translate=True)
    code = fields.Char(
        string='Código URL',
        compute='_compute_code', store=True, readonly=False,
        help='Se usa en el filtro de /marcas?linea=codigo. Se genera del nombre si se deja vacío.',
    )
    sequence = fields.Integer(default=10)
    brand_ids = fields.Many2many(
        'babatsa.brand', 'babatsa_brand_line_rel', 'line_id', 'brand_id', string='Marcas')

    _code_unique = models.Constraint('unique(code)', 'El código URL de la línea debe ser único.')

    @api.depends('name')
    def _compute_code(self):
        for line in self:
            if not line.code:
                line.code = _bbt_slug(line.name)


class BabatsaBrand(models.Model):
    _name = 'babatsa.brand'
    _description = 'Marca distribuida por Babatsa'
    _order = 'sequence, name'

    name = fields.Char(string='Marca', required=True)
    sequence = fields.Integer(string='Orden', default=10)
    active = fields.Boolean(default=True)
    website_published = fields.Boolean(string='Publicada en sitio web', default=True)
    tier = fields.Selection(
        selection=[('principal', 'Principal / estratégica'), ('especializada', 'Especializada')],
        string='Nivel', default='especializada', required=True,
        help='Las principales se muestran más grandes y en la página de inicio.',
    )
    logo = fields.Image(string='Logo', max_width=800, max_height=800)
    url = fields.Char(string='Sitio oficial')
    description = fields.Char(string='Descripción corta', help='Opcional, una línea. Ej. "Rodamientos y sellos".')
    line_ids = fields.Many2many(
        'babatsa.brand.line', 'babatsa_brand_line_rel', 'brand_id', 'line_id', string='Líneas de producto')
    is_service_center = fields.Boolean(
        string='Centro de servicio autorizado',
        help='Babatsa es centro de servicio autorizado de esta marca.',
    )
    has_program = fields.Boolean(
        string='Programa especializado',
        help='Babatsa tiene programa de análisis o proyectos de mejora con esta marca.',
    )

    def _bbt_website_card(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'logo_url': ('/marcas/%s/logo' % self.id) if self.logo else False,
            'url': self.url or False,
            'description': self.description or '',
            'lines': self.line_ids.sorted(lambda l: (l.sequence, l.name)).mapped('name'),
            'service_center': self.is_service_center,
            'program': self.has_program,
        }
