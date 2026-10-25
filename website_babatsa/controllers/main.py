# -*- coding: utf-8 -*-
import re

from markupsafe import Markup, escape
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.fields import Domain
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import WebsiteSale

MOTIVOS = [
    'Cotización',
    'Información de producto',
    'Asesoría',
    'Servicio técnico',
    'Garantía',
    'Proveedores',
    'Otro',
]

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
FIELDS = ['nombre', 'empresa', 'ciudad', 'telefono', 'email', 'motivo', 'sucursal', 'mensaje']


class BabatsaWebsite(http.Controller):

    # ------------------------------------------------------------------
    # Sucursales
    # ------------------------------------------------------------------
    def _bbt_published_warehouses(self):
        return request.env['stock.warehouse'].sudo().search(
            [('bbt_published', '=', True)], order='bbt_sequence, name')

    @http.route('/sucursales', type='http', auth='public', website=True, sitemap=True)
    def sucursales(self, **kw):
        # Todas juntas, en el orden de "Orden en sitio web" (la matriz va primero)
        warehouses = self._bbt_published_warehouses()
        values = {
            'branches': [wh._bbt_website_card() for wh in warehouses],
            'count_sucursales': len(warehouses.filtered(lambda w: w.bbt_type == 'sucursal')),
            'count_cedis': len(warehouses.filtered(lambda w: w.bbt_type == 'cedis')),
        }
        return request.render('website_babatsa.sucursales_page', values)

    @http.route('/sucursales/<int:warehouse_id>/foto', type='http', auth='public', website=True, sitemap=False)
    def sucursal_foto(self, warehouse_id, **kw):
        warehouse = request.env['stock.warehouse'].sudo().browse(warehouse_id).exists()
        if not warehouse or not warehouse.bbt_published or not warehouse.bbt_image:
            raise NotFound()
        return request.env['ir.binary']._get_image_stream_from(warehouse, 'bbt_image').get_response()

    # ------------------------------------------------------------------
    # Contacto
    # ------------------------------------------------------------------
    def _bbt_contact_values(self, form=None, errors=None):
        sucursales = [
            {'id': str(wh.id), 'name': wh.bbt_public_name or wh.name}
            for wh in self._bbt_published_warehouses()
        ]
        return {
            'form': form or {},
            'errors': errors or set(),
            'motivos': MOTIVOS,
            'sucursales': sucursales,
        }

    @http.route('/contacto', type='http', auth='public', website=True, sitemap=True)
    def contacto(self, sucursal=None, motivo=None, producto=None, **kw):
        form = {}
        if sucursal:
            form['sucursal'] = str(sucursal)
        if motivo in MOTIVOS:
            form['motivo'] = motivo
        # Desde la ficha de un producto del catálogo: se prellena el mensaje
        if producto and str(producto).isdigit():
            product = request.env['product.template'].sudo().browse(int(producto)).exists()
            if product and product.is_published:
                ref = ' (%s)' % product.default_code if product.default_code else ''
                form['mensaje'] = 'Me interesa el producto: %s%s' % (product.name, ref)
        return request.render('website_babatsa.contacto_page', self._bbt_contact_values(form))

    @http.route('/contacto/enviar', type='http', auth='public', website=True, methods=['POST'], csrf=True, sitemap=False)
    def contacto_enviar(self, **post):
        # Campo trampa para bots: si viene lleno se descarta en silencio.
        if post.get('website_url'):
            return request.redirect('/contacto/gracias')

        form = {key: (post.get(key) or '').strip() for key in FIELDS}
        errors = set()
        if not form['nombre']:
            errors.add('nombre')
        if form['motivo'] not in MOTIVOS:
            errors.add('motivo')
        if not form['mensaje']:
            errors.add('mensaje')
        if form['email'] and not EMAIL_RE.match(form['email']):
            errors.add('email')
        if not form['email'] and not form['telefono']:
            errors.update({'email', 'telefono', 'medio'})
        if errors:
            return request.render('website_babatsa.contacto_page', self._bbt_contact_values(form, errors))

        warehouse = request.env['stock.warehouse'].sudo()
        if form['sucursal'].isdigit():
            warehouse = warehouse.browse(int(form['sucursal'])).exists().filtered('bbt_published')
        sucursal_name = (warehouse.bbt_public_name or warehouse.name) if warehouse else ''

        rows = [
            ('Motivo', form['motivo']),
            ('Nombre', form['nombre']),
            ('Empresa', form['empresa']),
            ('Ciudad', form['ciudad']),
            ('Teléfono', form['telefono']),
            ('Correo', form['email']),
            ('Sucursal de interés', sucursal_name),
        ]
        description = Markup('').join(
            Markup('<p><strong>%s:</strong> %s</p>') % (label, value) for label, value in rows if value
        )
        description += Markup('<p><strong>Mensaje:</strong><br/>%s</p>') % Markup('<br/>').join(
            escape(line) for line in form['mensaje'].splitlines()
        )

        Tag = request.env['crm.tag'].sudo()
        tag = Tag.search([('name', '=', form['motivo'])], limit=1) or Tag.create({'name': form['motivo']})

        team_id = request.env['ir.config_parameter'].sudo().get_param('website_babatsa.contact_team_id')
        team = request.env['crm.team'].sudo().browse(int(team_id)).exists() if team_id and team_id.isdigit() else False

        lead_vals = {
            'name': '[Sitio web] %s · %s' % (form['motivo'], form['nombre']),
            'contact_name': form['nombre'],
            'partner_name': form['empresa'],
            'city': form['ciudad'],
            'phone': form['telefono'],
            'email_from': form['email'],
            'description': description,
            'tag_ids': [(4, tag.id)],
            'user_id': False,
            'company_id': request.website.company_id.id,
        }
        if team:
            lead_vals['team_id'] = team.id
        request.env['crm.lead'].sudo().with_context(mail_create_nosubscribe=True).create(lead_vals)
        return request.redirect('/contacto/gracias')

    @http.route('/contacto/gracias', type='http', auth='public', website=True, sitemap=False)
    def contacto_gracias(self, **kw):
        return request.render('website_babatsa.contacto_gracias')


# ----------------------------------------------------------------------
# Tienda en modo catálogo: sin carrito ni pago (website.bbt_catalog_mode)
# ----------------------------------------------------------------------
class BabatsaCart(Cart):

    @http.route()
    def cart(self, *args, **kwargs):
        if request.website.bbt_catalog_mode:
            return request.redirect('/shop')
        return super().cart(*args, **kwargs)

    @http.route()
    def add_to_cart(self, *args, **kwargs):
        if request.website.bbt_catalog_mode:
            raise NotFound()
        return super().add_to_cart(*args, **kwargs)


class BabatsaWebsiteSale(WebsiteSale):

    @http.route()
    def shop_checkout(self, *args, **kwargs):
        if request.website.bbt_catalog_mode:
            return request.redirect('/shop')
        return super().shop_checkout(*args, **kwargs)

    @http.route()
    def shop_payment(self, *args, **kwargs):
        if request.website.bbt_catalog_mode:
            return request.redirect('/shop')
        return super().shop_payment(*args, **kwargs)

    def _get_shop_domain(self, search, category, attribute_value_dict, search_in_description=True):
        # /shop?marca=<id>: productos de una marca (enlace desde la ficha del producto)
        domain = super()._get_shop_domain(search, category, attribute_value_dict, search_in_description)
        marca = request.params.get('marca')
        if marca and str(marca).isdigit():
            domain = Domain.AND([domain, [('bbt_brand_id', '=', int(marca))]])
        return domain


class BabatsaBrands(http.Controller):

    def _bbt_brand_cards(self, brands):
        return [brand._bbt_website_card() for brand in brands]

    @http.route('/marcas', type='http', auth='public', website=True, sitemap=True)
    def marcas(self, linea=None, **kw):
        Brand = request.env['babatsa.brand'].sudo()
        Line = request.env['babatsa.brand.line'].sudo()
        published = Brand.search([('website_published', '=', True)])
        lines = Line.search([]).filtered(lambda l: l.brand_ids & published)

        current = Line.browse()
        if linea:
            current = lines.filtered(lambda l: l.code == linea)[:1]
        brands = published.filtered(lambda b: current in b.line_ids) if current else published
        brands = brands.sorted(lambda b: (b.sequence, b.name.lower()))

        values = {
            'lines': [{'code': l.code, 'name': l.name} for l in lines],
            'current_line': current.code if current else False,
            'current_line_name': current.name if current else False,
            'principales': self._bbt_brand_cards(brands.filtered(lambda b: b.tier == 'principal')),
            'especializadas': self._bbt_brand_cards(brands.filtered(lambda b: b.tier == 'especializada')),
        }
        return request.render('website_babatsa.marcas_page', values)

    @http.route('/marcas/<int:brand_id>/logo', type='http', auth='public', website=True, sitemap=False)
    def marca_logo(self, brand_id, **kw):
        brand = request.env['babatsa.brand'].sudo().browse(brand_id).exists()
        if not brand or not brand.website_published or not brand.logo:
            raise NotFound()
        return request.env['ir.binary']._get_image_stream_from(brand, 'logo').get_response()
