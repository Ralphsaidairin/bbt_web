# -*- coding: utf-8 -*-
{
    'name': 'Sitio web Babatsa',
    'summary': 'Inicio, sucursales desde almacenes y contacto a CRM para babatsa.com.mx',
    'description': """
Sitio web corporativo de Babatsa.
- Página de inicio con identidad de marca (Manual de Identidad Babatsa).
- Página /sucursales generada desde los almacenes de Inventario.
- Página /contacto que crea oportunidades/iniciativas en CRM con etiqueta por motivo.
- Página /marcas desde el modelo Marcas Babatsa (logo, nivel, líneas, centro de servicio, programa).
- Pie de página con logo, enlaces, redes, vacantes (/jobs) y aviso de privacidad.
- Paleta y tipografía de marca disponibles en el constructor del sitio web.
""",
    'version': '19.0.1.1.0',
    'category': 'Website',
    'author': 'Babatsa · TI',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_crm',
        'website_hr_recruitment',
        'stock',
        'crm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/babatsa_brand_data.xml',
        'views/babatsa_brand_views.xml',
        'views/stock_warehouse_views.xml',
        'views/website_marcas_templates.xml',
        'views/website_home_templates.xml',
        'views/website_nosotros_templates.xml',
        'views/website_footer_templates.xml',
        'views/website_sucursales_templates.xml',
        'views/website_contacto_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'website_babatsa/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'website_babatsa/static/src/scss/babatsa.scss',
            'website_babatsa/static/src/js/babatsa_reveal.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
