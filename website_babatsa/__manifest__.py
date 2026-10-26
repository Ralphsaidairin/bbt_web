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
- Vacantes (/jobs, app Reclutamiento) con tarjetas tipo flyer, sucursal y correo de RH.
- Páginas Nosotros, Productos y Servicios; encabezado propio con 3 estilos.
- Tienda (Comercio electrónico) en modo catálogo: sin precios ni carrito, invita a sucursal o cotización.
- Paleta y tipografía de marca disponibles en el constructor del sitio web.
""",
    'version': '19.0.1.2.0',
    'category': 'Website',
    'author': 'Babatsa · TI',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_crm',
        'website_hr_recruitment',
        'stock',
        'crm',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/babatsa_brand_data.xml',
        'data/product_public_category_data.xml',
        'views/babatsa_brand_views.xml',
        'views/stock_warehouse_views.xml',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_common_templates.xml',
        'views/website_marcas_templates.xml',
        'views/website_home_templates.xml',
        'views/website_nosotros_templates.xml',
        'views/website_productos_templates.xml',
        'views/website_servicios_templates.xml',
        'views/website_header_templates.xml',
        'views/website_footer_templates.xml',
        'views/website_sucursales_templates.xml',
        'views/website_contacto_templates.xml',
        'views/website_shop_templates.xml',
        'views/hr_job_views.xml',
        'views/website_jobs_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'website_babatsa/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'website_babatsa/static/src/scss/babatsa.scss',
            'website_babatsa/static/src/js/babatsa_reveal.js',
            'website_babatsa/static/src/js/babatsa_nav.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
