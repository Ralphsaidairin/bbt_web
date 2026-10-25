# -*- coding: utf-8 -*-
"""Carga las sucursales de Babatsa en los almacenes de Odoo (pestaña "Sitio web").

Fuente: https://www.babatsa.net/sucursales (consultada el 2026-10-25). Teléfonos con formato uniforme
y direcciones con mayúsculas normales; el contenido es el mismo.

Uso (odoo shell, con el repo montado en /mnt/babatsa-web):
    odoo shell -d <base> < /mnt/babatsa-web/scripts/cargar_sucursales.py

Busca cada almacén por su código (CODE); si no existe lo crea. En producción conviene revisar antes
qué almacén corresponde a cada sucursal y ajustar los códigos de esta lista a los reales.
Sin datos en la fuente: horarios, fotos y ubicación en Google Maps ("Cómo llegar" usa la dirección).
"""

SUCURSALES = [
    # code, nombre del almacén, nombre público, tipo, orden, calle, colonia, ciudad, estado, CP, tel, cel, correo, nota
    ('MTRZ', 'Babatsa Matriz', 'Babatsa Matriz', 'sucursal', 10,
     'G. Leyva No. 732 Nte.', 'Col. Centro', 'Los Mochis', 'Sinaloa', '81200',
     '668 812 0210', '668 174 2737', 'gerencia.matriz@babatsa.com.mx', ''),
    ('POSE', 'Babatsa Poseidón', 'Babatsa Poseidón', 'sucursal', 20,
     'Blvd. A. López Mateos No. 2414 Nte.', 'Fracc. Las Fuentes', 'Los Mochis', 'Sinaloa', '81223',
     '668 818 5151', '668 174 5615', 'gerencia.poseidon@babatsa.com.mx', ''),
    ('CEDIS', 'CEDIS Babatsa', 'Centro de Distribución (CEDIS)', 'cedis', 30,
     'Calle de la Agricultura No. 1620 Ote.', 'Parque Industrial Ecológico', 'Los Mochis', 'Sinaloa', '82070',
     '', '668 189 0953', '', ''),
    ('RUKA', 'Babatsa Ruka', 'Babatsa Ruka', 'sucursal', 40,
     'Blvd. M. Gaxiola y A. Cano 799 Ote.', 'Fracc. El Parque', 'Los Mochis', 'Sinaloa', '81200',
     '668 812 7612', '668 179 3161', 'gerencia.ruka@babatsa.com.mx', ''),
    ('INDEP', 'Babatsa Independencia', 'Babatsa Independencia', 'sucursal', 50,
     'Av. Independencia No. 1339', 'Fracc. Jardines del Valle', 'Los Mochis', 'Sinaloa', '81245',
     '668 815 2080', '668 217 2949', 'gerencia.independencia@babatsa.com.mx',
     "Centro de servicio Makita, Evans, Mikel's, Surtek, Urrea, Ingersoll Rand."),
    ('CLN', 'Babatsa Culiacán', 'Babatsa Culiacán', 'sucursal', 60,
     'Blvd. Emiliano Zapata No. 4988 Pte.', 'Col. San Rafael', 'Culiacán', 'Sinaloa', '80150',
     '667 761 1075', '667 296 4151', 'gerencia.culiacan@babatsa.com.mx', ''),
    ('GSV', 'Babatsa Guasave', 'Babatsa Guasave', 'sucursal', 70,
     'Blvd. Central #140 Nte.', 'Col. Centro', 'Guasave', 'Sinaloa', '81000',
     '687 872 4368', '687 149 0110', 'gerencia.guasave@babatsa.com.mx', ''),
    ('MZT', 'Babatsa Mazatlán', 'Babatsa Mazatlán', 'sucursal', 80,
     'Av. Luis Donaldo Colosio Murrieta #19', 'Col. Rincón de Urías', 'Mazatlán', 'Sinaloa', '82070',
     '669 980 2546', '668 180 1312', 'gerencia.mazatlan@babatsa.com.mx', ''),
    ('OBR', 'Babatsa Obregón', 'Babatsa Obregón', 'sucursal', 90,
     'Coahuila #872 Sur', 'Col. Centro', 'Obregón', 'Sonora', '85000',
     '644 417 7444', '644 184 1260', 'gerencia.obregon@babatsa.com.mx', ''),
    ('HMO', 'Babatsa Hermosillo', 'Babatsa Hermosillo', 'sucursal', 100,
     'Periférico Nte. No. 50', 'Col. Loma Linda', 'Hermosillo', 'Sonora', '83150',
     '662 215 6775', '662 197 1830', 'gerencia.hermosillo@babatsa.com.mx', ''),
    ('LAP', 'Babatsa La Paz', 'Babatsa La Paz', 'sucursal', 110,
     'Calle Abasolo No. 3805, entre Colima y Bugambilias', 'Col. Benito Juárez', 'La Paz', 'Baja California Sur', '23060',
     '612 146 2543', '612 150 1569', 'gerencia.lapaz@babatsa.com.mx', ''),
    ('TPC', 'Babatsa Tepic', 'Babatsa Tepic', 'sucursal', 120,
     'Av. Insurgentes #3860 Ote.', 'Col. Puente de San Cayetano', 'Tepic', 'Nayarit', '63193',
     '311 133 0080', '668 153 4418', 'gerencia.tepic@babatsa.com.mx', ''),
]

mx = env.ref('base.mx')
company = env.company
Warehouse = env['stock.warehouse']
for (code, wh_name, public, wtype, seq, street, street2, city, state_name, zip_code,
     phone, mobile, email, note) in SUCURSALES:
    state = env['res.country.state'].search([('country_id', '=', mx.id), ('name', '=', state_name)], limit=1)
    partner_vals = {
        'name': wh_name, 'type': 'other', 'parent_id': company.partner_id.id,
        'street': street, 'street2': street2, 'city': city, 'zip': zip_code,
        'state_id': state.id, 'country_id': mx.id, 'phone': phone, 'email': email,
    }
    wh = Warehouse.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
    if wh:
        if wh.partner_id and wh.partner_id != company.partner_id:
            wh.partner_id.write(partner_vals)
        else:
            wh.partner_id = env['res.partner'].create(partner_vals)
    else:
        wh = Warehouse.create({
            'name': wh_name, 'code': code, 'company_id': company.id,
            'partner_id': env['res.partner'].create(partner_vals).id,
        })
    wh.write({
        'bbt_published': True, 'bbt_type': wtype, 'bbt_public_name': public, 'bbt_sequence': seq,
        'bbt_mobile': mobile, 'bbt_note': note,
    })
    print('OK', code, public, '/', city, '/', state.name or 'SIN ESTADO')

env.cr.commit()
print('Sucursales publicadas:', Warehouse.search_count([('bbt_published', '=', True)]))
