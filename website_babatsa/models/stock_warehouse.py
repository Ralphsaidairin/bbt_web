# -*- coding: utf-8 -*-
import json
import re
from datetime import timedelta
from urllib.parse import quote

from odoo import fields, models

DAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    bbt_published = fields.Boolean(
        string='Mostrar en sitio web',
        default=False,
        help='Si está activo, el almacén aparece en la página /sucursales y en el formulario de contacto.',
    )
    bbt_type = fields.Selection(
        selection=[('sucursal', 'Sucursal'), ('cedis', 'Centro de Distribución')],
        string='Tipo en sitio web',
        default='sucursal',
        required=True,
    )
    bbt_public_name = fields.Char(
        string='Nombre público',
        help='Nombre que verá el cliente (ej. "Sucursal Centro"). Si se deja vacío se usa el nombre del almacén.',
    )
    bbt_sequence = fields.Integer(string='Orden en sitio web', default=10)
    bbt_hours = fields.Text(
        string='Horario de atención',
        help='Un renglón por bloque, ej.:\nLunes a viernes: 8:00 a 18:00\nSábado: 8:00 a 14:00',
    )
    bbt_image = fields.Image(string='Foto de fachada', max_width=1920, max_height=1920)
    bbt_maps_url = fields.Char(
        string='Enlace de Google Maps',
        help='Opcional. Si se deja vacío, el botón "Cómo llegar" usa las coordenadas o la dirección del contacto del almacén.',
    )
    bbt_mobile = fields.Char(
        string='Celular (sitio web)',
        help='Se muestra junto al teléfono del contacto del almacén.',
    )
    bbt_whatsapp = fields.Boolean(
        string='El celular tiene WhatsApp',
        default=True,
        help='Si está activo, el sitio ofrece "Escríbenos por WhatsApp" con el celular de la sucursal '
             '(tarjetas de /sucursales y la herramienta "Tu pieza").',
    )
    bbt_calendar_id = fields.Many2one(
        'resource.calendar', string='Horario estructurado',
        help='Horario de trabajo de Odoo (Empleados > Configuración > Horarios de trabajo). '
             'Con él, el sitio muestra "Abierta ahora · cierra en..." y avisa los días festivos '
             '(ausencias globales del horario). Si se deja vacío se muestra el texto de "Horario de atención".',
    )
    bbt_note = fields.Char(
        string='Nota en sitio web',
        help='Una línea opcional en la tarjeta, ej. "Centro de servicio Makita, Urrea...".',
    )

    def _bbt_phone_link(self, phone):
        return re.sub(r'[^\d+]', '', phone or '')

    def _bbt_location_query(self):
        """Coordenadas del contacto si las tiene; si no, la dirección escrita."""
        self.ensure_one()
        partner = self.partner_id
        if partner.partner_latitude and partner.partner_longitude:
            return '%s,%s' % (partner.partner_latitude, partner.partner_longitude)
        parts = [partner.street, partner.street2, partner.zip, partner.city, partner.state_id.name, partner.country_id.name]
        return ', '.join(p for p in parts if p)

    def _bbt_directions_url(self):
        self.ensure_one()
        if self.bbt_maps_url:
            return self.bbt_maps_url
        destination = self._bbt_location_query()
        if not destination:
            return False
        return 'https://www.google.com/maps/dir/?api=1&destination=%s' % quote(destination)

    def _bbt_map_embed_url(self):
        """Mapa pequeño para la tarjeta cuando no hay foto (embebido de Google Maps, sin clave de API)."""
        self.ensure_one()
        query = self._bbt_location_query()
        if not query:
            return False
        return 'https://maps.google.com/maps?q=%s&z=16&output=embed' % quote(query)

    def _bbt_whatsapp_number(self):
        """Celular en formato internacional para wa.me (México: 52 + 10 dígitos)."""
        self.ensure_one()
        if not (self.bbt_whatsapp and self.bbt_mobile):
            return ''
        digits = re.sub(r'\D', '', self.bbt_mobile)
        if len(digits) == 10:
            digits = '52' + digits
        return digits

    def _bbt_greeting(self):
        """Saludo para WhatsApp; los nombres públicos ya suelen decir "Babatsa ..."."""
        self.ensure_one()
        name = self.bbt_public_name or self.name
        return 'Hola %s' % name if name.lower().startswith('babatsa') else 'Hola Babatsa %s' % name

    def _bbt_schedule(self):
        """Horario para el JS de "abierta ahora": zona horaria, bloques por día (0 = lunes)
        y días festivos de los próximos 60 días. False si no tiene horario estructurado."""
        self.ensure_one()
        calendar = self.bbt_calendar_id
        if not calendar:
            return False
        days = {str(d): [] for d in range(7)}
        for att in calendar.attendance_ids.filtered(lambda a: not a.display_type and a.week_type in (False, '0')):
            days[att.dayofweek].append([round(att.hour_from, 4), round(att.hour_to, 4)])
        for blocks in days.values():
            blocks.sort()
        today = fields.Date.context_today(self)
        limit = today + timedelta(days=60)
        closed = set()
        for leave in calendar.global_leave_ids:
            day = leave.date_from.date()
            while day <= leave.date_to.date() and day <= limit:
                if day >= today:
                    closed.add(day.isoformat())
                day += timedelta(days=1)
        return {'tz': calendar.tz or 'America/Mazatlan', 'days': days, 'closed': sorted(closed)}

    def _bbt_schedule_text(self, schedule):
        """Horario legible a partir del estructurado, agrupando días seguidos iguales."""
        def fmt(h):
            return '%d:%02d' % (int(h), round((h - int(h)) * 60))
        lines, start = [], 0
        signature = [' y '.join('%s a %s' % (fmt(a), fmt(b)) for a, b in schedule['days'][str(d)]) for d in range(7)]
        for d in range(1, 8):
            if d == 7 or signature[d] != signature[start]:
                if signature[start]:
                    label = DAY_NAMES[start] if d - 1 == start else '%s a %s' % (DAY_NAMES[start], DAY_NAMES[d - 1].lower())
                    lines.append('%s: %s' % (label, signature[start]))
                start = d
        return '\n'.join(lines)

    def _bbt_website_card(self):
        """Datos ya preparados para la plantilla pública (se llama con sudo)."""
        self.ensure_one()
        partner = self.partner_id
        schedule = self._bbt_schedule()
        whatsapp = self._bbt_whatsapp_number()
        street = ', '.join(p for p in [partner.street, partner.street2] if p)
        zip_city = ' '.join(p for p in [partner.zip, partner.city] if p)
        city_line = ', '.join(p for p in [zip_city, partner.state_id.name] if p)
        return {
            'id': self.id,
            'name': self.bbt_public_name or self.name,
            'type': self.bbt_type,
            'city': (partner.city or '').strip() or 'Otras ubicaciones',
            'street': street,
            'city_line': city_line,
            'phone': partner.phone or '',
            'phone_link': self._bbt_phone_link(partner.phone),
            'mobile': self.bbt_mobile or '',
            'mobile_link': self._bbt_phone_link(self.bbt_mobile),
            'note': self.bbt_note or '',
            'sequence': self.bbt_sequence,
            'email': partner.email or '',
            'hours': self.bbt_hours or (self._bbt_schedule_text(schedule) if schedule else ''),
            'schedule_json': json.dumps(schedule) if schedule else False,
            'whatsapp': whatsapp,
            'whatsapp_url': ('https://wa.me/%s?text=%s' % (whatsapp, quote(self._bbt_greeting() + ', '))) if whatsapp else False,
            'image_url': ('/sucursales/%s/foto' % self.id) if self.bbt_image else False,
            'map_embed_url': self._bbt_map_embed_url(),
            'directions_url': self._bbt_directions_url(),
            'contact_url': '/contacto?sucursal=%s' % self.id,
        }
