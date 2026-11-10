# -*- coding: utf-8 -*-
import re
from urllib.parse import quote

from odoo import fields, models

BBT_HEADER_STYLES = [
    ('capsula', 'Cápsula flotante'),
    ('doble', 'Doble barra con mega menú'),
    ('completo', 'Menú a pantalla completa'),
]

YOUTUBE_RE = re.compile(r'(?:youtu\.be/|[?&]v=|/shorts/|/embed/|/live/)([\w-]{11})')
VIMEO_RE = re.compile(r'vimeo\.com/(?:video/)?(\d+)')


class Website(models.Model):
    _inherit = 'website'

    bbt_header_style = fields.Selection(
        selection=BBT_HEADER_STYLES,
        string='Estilo de encabezado',
        default='capsula',
        required=True,
        help='Diseño del encabezado del sitio. Para comparar sin guardar: agregar ?navbar=doble a la dirección.',
    )
    bbt_catalog_mode = fields.Boolean(
        string='Modo catálogo',
        default=True,
        help='La tienda muestra los productos como referencia: sin precios, sin carrito ni pago. '
             'En su lugar invita a visitar una sucursal o pedir cotización. '
             'Apagarlo cuando se quiera vender en línea.',
    )
    bbt_rh_email = fields.Char(
        string='Correo de RH',
        help='Se muestra en /jobs como opción para enviar el CV por correo. '
             'Si se deja vacío, solo se ofrece el formulario de cada vacante.',
    )
    bbt_founder_video_url = fields.Char(
        string='Video del fundador',
        help='Enlace de YouTube, Vimeo o Facebook, o de un archivo .mp4. Aparece en Nosotros; '
             'el video no se descarga hasta que el visitante le da play. Vacío: la sección no se muestra.',
    )
    bbt_founder_caption = fields.Char(
        string='Pie del video',
        help='Ej. el nombre del fundador y el año de la entrevista.',
    )

    def _bbt_line_url(self, code):
        """Enlace a una línea de producto (categorías pcat_<código>). Una categoría sin productos
        publicados da 404 en la tienda, así que entonces se manda a su sección en /productos."""
        cat = self.env.ref('website_babatsa.pcat_%s' % code, raise_if_not_found=False)
        cat = cat and cat.sudo()
        if cat and self.env['product.template'].sudo().search_count(
                [('public_categ_ids', 'child_of', cat.id), ('is_published', '=', True)], limit=1):
            return '/shop/category/%s' % self.env['ir.http']._slug(cat)
        return '/productos#%s' % code

    def _bbt_line_urls(self):
        codes = ['rodamientos', 'transmision', 'hidraulica', 'tornilleria', 'herramientas',
                 'lubricacion', 'abrasivos', 'ferreteria']
        return {code: self._bbt_line_url(code) for code in codes}

    def _bbt_founder_video(self):
        """Cómo reproducir el video del fundador: {kind, src, thumb} o False."""
        self.ensure_one()
        url = (self.bbt_founder_video_url or '').strip()
        if not url:
            return False
        m = YOUTUBE_RE.search(url)
        if m:
            vid = m.group(1)
            return {'kind': 'embed', 'src': 'https://www.youtube-nocookie.com/embed/%s?autoplay=1&rel=0' % vid,
                    'thumb': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % vid, 'url': url}
        m = VIMEO_RE.search(url)
        if m:
            return {'kind': 'embed', 'src': 'https://player.vimeo.com/video/%s?autoplay=1' % m.group(1), 'thumb': False, 'url': url}
        if 'facebook.com' in url or 'fb.watch' in url:
            return {'kind': 'embed', 'src': 'https://www.facebook.com/plugins/video.php?href=%s&show_text=false&autoplay=1' % quote(url, safe=''),
                    'thumb': False, 'url': url}
        return {'kind': 'file', 'src': url, 'thumb': False, 'url': url}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_bbt_header_style = fields.Selection(
        related='website_id.bbt_header_style', readonly=False)
    website_bbt_catalog_mode = fields.Boolean(
        related='website_id.bbt_catalog_mode', readonly=False)
    website_bbt_rh_email = fields.Char(
        related='website_id.bbt_rh_email', readonly=False)
    website_bbt_founder_video_url = fields.Char(
        related='website_id.bbt_founder_video_url', readonly=False)
    website_bbt_founder_caption = fields.Char(
        related='website_id.bbt_founder_caption', readonly=False)
