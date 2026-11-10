# -*- coding: utf-8 -*-
import base64
import json
import re
from urllib.parse import quote

from markupsafe import Markup, escape
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.fields import Domain
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import WebsiteSale

from ..models import branch_map

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
        branches = [wh._bbt_website_card() for wh in warehouses]
        values = {
            'branches': branches,
            'branch_map': branch_map.build(branches),
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


class BabatsaJobs(http.Controller):

    @http.route('/vacantes/<int:job_id>/flyer', type='http', auth='public', website=True, sitemap=False)
    def vacante_flyer(self, job_id, **kw):
        job = request.env['hr.job'].sudo().browse(job_id).exists()
        can_preview = request.env.user.has_group('hr_recruitment.group_hr_recruitment_user')
        if not job or not job.bbt_flyer or not (job.website_published or can_preview):
            raise NotFound()
        return request.env['ir.binary']._get_image_stream_from(job, 'bbt_flyer').get_response()


class BabatsaTuPieza(http.Controller):
    """Herramienta "Tu pieza": el cliente describe y mide la pieza que busca, elige sucursal y la
    solicitud queda en CRM (con fotos y folio); si la sucursal tiene WhatsApp, además se le abre
    el chat con el mensaje ya escrito y el folio para que el mostrador lo encuentre."""

    TIPOS = ('balero', 'reten', 'banda', 'tornillo', 'manguera', 'otra')
    MAX_PIEZAS = 15
    MAX_FOTOS = 3
    MAX_FOTO_BYTES = 8 * 1024 * 1024

    def _bbt_sucursales(self):
        warehouses = request.env['stock.warehouse'].sudo().search(
            [('bbt_published', '=', True)], order='bbt_sequence, name')
        return [{
            'id': wh.id,
            'name': wh.bbt_public_name or wh.name,
            'city': (wh.partner_id.city or '').strip(),
            'whatsapp': bool(wh._bbt_whatsapp_number()),
        } for wh in warehouses]

    @http.route('/tu-pieza', type='http', auth='public', website=True, sitemap=True)
    def tu_pieza(self, sucursal=None, tipo=None, **kw):
        return request.render('website_babatsa.tu_pieza_page', {
            'sucursales': self._bbt_sucursales(),
            'sucursal_id': int(sucursal) if str(sucursal or '').isdigit() else False,
            'tipo': tipo if tipo in self.TIPOS else 'balero',
        })

    @http.route('/tu-equipo', type='http', auth='public', website=True, sitemap=True)
    def tu_equipo(self, **kw):
        # Cada parte del despiece enlaza a su línea del catálogo (o a /productos si aún no tiene productos)
        cats = {code: request.website._bbt_line_url(code)
                for code in ['rodamientos', 'transmision', 'hidraulica', 'tornilleria', 'lubricacion']}
        return request.render('website_babatsa.tu_equipo_page', {'cats': cats})

    @http.route('/tu-pieza/gracias', type='http', auth='public', website=True, sitemap=False)
    def tu_pieza_gracias(self, **kw):
        return request.render('website_babatsa.tu_pieza_gracias')

    def _bbt_clean(self, value, size=120):
        return re.sub(r'\s+', ' ', str(value or '')).strip()[:size]

    def _bbt_parse_piezas(self, raw):
        """Lista que arma el JS: [{tipo, codigo, equipo, medidas: [{nombre, valor, unidad}]}]."""
        try:
            data = json.loads(raw or '[]')
        except ValueError:
            return []
        piezas = []
        for item in data[:self.MAX_PIEZAS] if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            medidas = []
            for m in item.get('medidas') or []:
                if isinstance(m, dict) and self._bbt_clean(m.get('valor'), 20):
                    medidas.append(' '.join(p for p in [
                        self._bbt_clean(m.get('nombre'), 40),
                        self._bbt_clean(m.get('valor'), 20),
                        self._bbt_clean(m.get('unidad'), 8),
                    ] if p))
            pieza = {
                'tipo': self._bbt_clean(item.get('tipo'), 40) or 'Pieza',
                'codigo': self._bbt_clean(item.get('codigo'), 60),
                'equipo': self._bbt_clean(item.get('equipo'), 80),
                'medidas': medidas,
            }
            if pieza['codigo'] or pieza['medidas'] or pieza['equipo']:
                piezas.append(pieza)
        return piezas

    def _bbt_pieza_line(self, pieza):
        parts = [pieza['tipo'] + (' ' + pieza['codigo'] if pieza['codigo'] else '')]
        if pieza['medidas']:
            parts.append(', '.join(pieza['medidas']))
        if pieza['equipo']:
            parts.append('para ' + pieza['equipo'])
        return ' – '.join(parts)

    @http.route('/tu-pieza/enviar', type='http', auth='public', website=True, methods=['POST'], csrf=True, sitemap=False)
    def tu_pieza_enviar(self, **post):
        wants_json = request.httprequest.headers.get('X-Requested-With') == 'fetch'

        def reply(ok, **values):
            if wants_json:
                return request.make_json_response(dict(values, ok=ok), status=200 if ok else 400)
            return request.redirect('/tu-pieza/gracias' if ok else '/tu-pieza')

        if post.get('website_url'):  # campo trampa para bots
            return reply(True)

        nombre = self._bbt_clean(post.get('nombre'), 80)
        telefono = self._bbt_clean(post.get('telefono'), 30)
        nota = (post.get('nota') or '').strip()[:1000]
        accion = 'whatsapp' if post.get('accion') == 'whatsapp' else 'llamada'
        piezas = self._bbt_parse_piezas(post.get('piezas'))
        fotos = [f for f in request.httprequest.files.getlist('fotos') if f and f.filename][:self.MAX_FOTOS]

        errors = []
        if not nombre:
            errors.append('nombre')
        if len(re.sub(r'\D', '', telefono)) < 10:
            errors.append('telefono')
        if not (piezas or nota or fotos):
            errors.append('piezas')
        warehouse = request.env['stock.warehouse'].sudo()
        if str(post.get('sucursal') or '').isdigit():
            warehouse = warehouse.browse(int(post['sucursal'])).exists().filtered('bbt_published')
        if not warehouse:
            errors.append('sucursal')
        if errors:
            return reply(False, errors=errors)

        sucursal_name = warehouse.bbt_public_name or warehouse.name
        lines = [self._bbt_pieza_line(p) for p in piezas]
        description = Markup('<p><strong>Sucursal:</strong> %s<br/><strong>Nombre:</strong> %s<br/>'
                             '<strong>Teléfono:</strong> %s<br/><strong>Prefiere:</strong> %s</p>') % (
            sucursal_name, nombre, telefono, 'WhatsApp' if accion == 'whatsapp' else 'Que le llamen')
        if lines:
            description += Markup('<p><strong>Piezas:</strong></p><ul>%s</ul>') % Markup('').join(
                Markup('<li>%s</li>') % line for line in lines)
        if nota:
            description += Markup('<p><strong>Comentarios:</strong><br/>%s</p>') % Markup('<br/>').join(
                escape(line) for line in nota.splitlines())

        Tag = request.env['crm.tag'].sudo()
        tag = Tag.search([('name', '=', 'Tu pieza')], limit=1) or Tag.create({'name': 'Tu pieza'})
        team_id = request.env['ir.config_parameter'].sudo().get_param('website_babatsa.contact_team_id')
        team = request.env['crm.team'].sudo().browse(int(team_id)).exists() if team_id and team_id.isdigit() else False
        first = (piezas[0]['tipo'] + (' ' + piezas[0]['codigo'] if piezas[0]['codigo'] else '')) if piezas else 'Pieza'
        more = ' y %s más' % (len(piezas) - 1) if len(piezas) > 1 else ''
        lead_vals = {
            'name': '[Tu pieza] %s%s · %s' % (first, more, nombre),
            'contact_name': nombre,
            'phone': telefono,
            'city': warehouse.partner_id.city or False,
            'description': description,
            'tag_ids': [(4, tag.id)],
            'user_id': False,
            'company_id': request.website.company_id.id,
        }
        if team:
            lead_vals['team_id'] = team.id
        lead = request.env['crm.lead'].sudo().with_context(mail_create_nosubscribe=True).create(lead_vals)

        attachments = request.env['ir.attachment'].sudo()
        for foto in fotos:
            content = foto.read(self.MAX_FOTO_BYTES + 1)
            if len(content) > self.MAX_FOTO_BYTES or not (foto.mimetype or '').startswith('image/'):
                continue
            attachments |= attachments.create({
                'name': foto.filename[:120],
                'datas': base64.b64encode(content),
                'res_model': 'crm.lead',
                'res_id': lead.id,
            })
        if attachments:
            lead.message_post(body=Markup('<p>Fotos de la pieza enviadas desde el sitio web.</p>'),
                              attachment_ids=attachments.ids)

        folio = 'TP-%05d' % lead.id
        whatsapp_url = False
        number = warehouse._bbt_whatsapp_number()
        if accion == 'whatsapp' and number:
            text = ['%s, busco %s:' % (warehouse._bbt_greeting(), 'estas piezas' if len(lines) > 1 else 'esta pieza')]
            text += ['• ' + line for line in lines] or ['• (va en las fotos)']
            if attachments:
                text.append('Subí %s foto%s en el sitio.' % (len(attachments), 's' if len(attachments) > 1 else ''))
            text.append('Soy %s. Folio %s.' % (nombre, folio))
            whatsapp_url = 'https://wa.me/%s?text=%s' % (number, quote('\n'.join(text)))
        return reply(True, folio=folio, whatsapp_url=whatsapp_url, sucursal=sucursal_name)
