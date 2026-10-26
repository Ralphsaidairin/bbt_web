# website_babatsa (Odoo 19)

Sitio web corporativo de Babatsa: Inicio, Marcas (modelo propio), Sucursales (desde Inventario), Contacto (a CRM) y pie de página.

## Instalación
Requiere Odoo 19 (Odoo.sh o servidor propio; no se puede en Odoo Online porque trae código Python).
1. Copiar la carpeta `website_babatsa` al directorio de addons personalizados.
2. Reiniciar Odoo y actualizar la lista de aplicaciones (modo desarrollador).
3. Instalar **Sitio web Babatsa**. Depende de: website, website_crm, website_hr_recruitment, stock, crm, website_sale.

### En Odoo.sh
1. Agregar la carpeta `website_babatsa` a la raíz del repositorio del proyecto (junto a los demás módulos)
   y hacer push a una rama **staging** primero.
2. Cuando el build termine: Aplicaciones > Actualizar lista de aplicaciones > instalar **Sitio web Babatsa**
   (en staging y producción los módulos nuevos no se instalan solos).
3. Cargar las sucursales desde la terminal del editor de esa rama, revisando antes que los códigos de
   almacén del script coincidan con los almacenes reales (si no, crea almacenes nuevos):
   `odoo-bin shell < scripts/cargar_sucursales.py`
4. Seguir "Configuración después de instalar" (abajo); validar el sitio en staging y luego pasar la rama a producción.

## Configuración después de instalar
1. **Almacenes** (Inventario > Configuración > Almacenes), pestaña **Sitio web** en cada uno:
   - Activar *Mostrar en sitio web*.
   - Tipo: *Sucursal* o *Centro de Distribución* (CEDIS Poseidón).
   - Nombre público, horario, foto de fachada y, opcional, enlace de Google Maps.
   - Dirección, teléfono y correo salen del **contacto de dirección** del almacén: revisar que estén completos.
   - Si el contacto tiene coordenadas, "Cómo llegar" las usa; si no, usa la dirección escrita.
   - *Celular (sitio web)* y *Nota en sitio web* (ej. centros de servicio) se capturan en la misma pestaña.
   - Carga inicial: `scripts/cargar_sucursales.py` (datos de babatsa.net/sucursales; ver uso en el archivo).
2. **Paleta**: Sitio web > Editar > Tema > Colores: elegir la paleta *babatsa*. Fuente: Montserrat.
3. **Logo del encabezado**: ya viene en el encabezado propio (`static/src/img/logo-color.svg`); no se sube.
4. **Menú** (orden del documento): Inicio | Nosotros | Productos | Marcas | Servicios | Sucursales | Contacto.
   Borrar los menús nativos "Contáctenos" (/contactus) y "Empleos" (/jobs; las vacantes van en el pie) y crear
   una redirección 301 /contactus → /contacto (Sitio web > Configuración > Redirecciones).
   Nota: al actualizar el módulo el hook no vuelve a correr; crea a mano los menús nuevos.
   El encabezado es propio y toma los enlaces de primer nivel de Sitio web > Menús. Tiene 3 estilos
   (Sitio web > Configuración > Ajustes > Babatsa > Estilo de encabezado): Cápsula flotante, Doble barra con
   mega menú (Productos abre las categorías) y Menú a pantalla completa. Para comparar sin guardar:
   agregar ?navbar=capsula, ?navbar=doble o ?navbar=completo a cualquier dirección.
5. **Nosotros**: la línea del tiempo tiene hitos con [Año] y [por confirmar]; editarlos en el constructor
   cuando se tengan los datos reales.
6. **Equipo de ventas para contacto** (opcional): Ajustes > Técnico > Parámetros del sistema,
   clave `website_babatsa.contact_team_id`, valor = ID del equipo de CRM que recibirá los mensajes.
   Cada mensaje crea un registro en CRM con etiqueta igual al motivo (Cotización, Garantía, Proveedores...).
7. **Vacantes**: RH publica puestos en Reclutamiento; el pie de página enlaza a /jobs.
8. **Copyright**: editar la línea de copyright de Odoo debajo del pie: "© Babatsa. Todos los derechos reservados."
9. **Aviso de privacidad**: crear la página /aviso-de-privacidad con el texto de Contabilidad.

## Catálogo de productos (Comercio electrónico en modo catálogo)
- Depende de `website_sale` (instala Ventas y Facturación si no están).
- **Modo catálogo** (Sitio web > Configuración > Ajustes > Babatsa): la tienda /shop muestra los productos
  como referencia, sin precios, carrito ni pago; cada ficha invita a "Encuentra tu sucursal" o
  "Solicita cotización" (prellena el formulario de contacto con el producto). /shop/cart y /shop/checkout
  redirigen a /shop. Para vender en línea: apagar el modo catálogo.
- Selección curada: solo aparecen los productos con *Publicado en el sitio web*.
- En el producto: categoría de tienda (8 líneas, mismos nombres que /productos) y *Marca (sitio web)*.
- Borrar el menú "Tienda" (/shop) que agrega Odoo: el menú del documento no lo incluye.
- Diseño propio: portada azul con las líneas de producto, tarjetas con marca y "Ver producto".

## Marcas (Sitio web > Configuración > Marcas Babatsa)
- 46 marcas precargadas del documento del sitio (12 principales + 34 especializadas), sin logo.
- Sin logo se muestra el nombre en tipografía de marca; al subir el logo se reemplaza solo.
- *Principal*: aparece grande en /marcas y en la página de inicio (máximo 12, por orden).
- *Líneas de producto*: alimentan el filtro /marcas?linea=... Solo se asignaron las líneas evidentes; revisar el resto.
- *Centro de servicio* y *Programa especializado*: precargados según el documento (Urrea, Makita, Mikels, Evans, ITC; SKF, Parker)
  para usarlos en la página de Servicios.
- Nombres corregidos al cargar: "móvil" → Mobil, "bardhal" → Bardahl. Revisar: Esculumex, Pensilvania, Ingersoll.
- Los datos son noupdate: actualizar el módulo no borra lo que edite mercadotecnia.

## Imágenes pendientes (placeholders en static/src/img/ph/)
Fotos reales de mostrador, asesor y promoción; logo de aniversario; mapa de sucursales;
logos de marcas (se suben en el registro de cada marca). Las fotos se reemplazan desde el constructor con doble clic.

## Notas
- Si la página de inicio ya había sido editada en el constructor, existe una copia específica del sitio
  y la herencia del módulo no se ve hasta restablecerla.
- El contenido editado en el constructor se guarda como copia en la base de datos, no en este módulo.
