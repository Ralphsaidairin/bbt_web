# website_babatsa (Odoo 19)

Sitio web corporativo de Babatsa: Inicio, Marcas (modelo propio), Sucursales (desde Inventario), Contacto (a CRM) y pie de página.

## Instalación
1. Copiar la carpeta `website_babatsa` al directorio de addons personalizados.
2. Reiniciar Odoo y actualizar la lista de aplicaciones (modo desarrollador).
3. Instalar **Sitio web Babatsa**. Depende de: website, website_crm, website_hr_recruitment, stock, crm.

## Configuración después de instalar
1. **Almacenes** (Inventario > Configuración > Almacenes), pestaña **Sitio web** en cada uno:
   - Activar *Mostrar en sitio web*.
   - Tipo: *Sucursal* o *Centro de Distribución* (CEDIS Poseidón).
   - Nombre público, horario, foto de fachada y, opcional, enlace de Google Maps.
   - Dirección, teléfono y correo salen del **contacto de dirección** del almacén: revisar que estén completos.
   - Si el contacto tiene coordenadas, "Cómo llegar" las usa; si no, usa la dirección escrita.
2. **Paleta**: Sitio web > Editar > Tema > Colores: elegir la paleta *babatsa*. Fuente: Montserrat.
3. **Logo del encabezado**: Sitio web > Editar > clic en el logo > subir `static/src/img/logo-color.svg`
   (mínimo 150 px de ancho según el manual).
4. **Menú**: el módulo agrega *Marcas* (/marcas), *Sucursales* (/sucursales) y *Contacto* (/contacto).
   Borrar el menú nativo "Contáctenos" (/contactus) y crear una redirección 301 /contactus → /contacto
   (Sitio web > Configuración > Redirecciones). Faltan Nosotros, Productos y Servicios.
   Nota: si actualizas desde 19.0.1.0.0, el hook no vuelve a correr; crea el menú Marcas (/marcas) a mano.
5. **Equipo de ventas para contacto** (opcional): Ajustes > Técnico > Parámetros del sistema,
   clave `website_babatsa.contact_team_id`, valor = ID del equipo de CRM que recibirá los mensajes.
   Cada mensaje crea un registro en CRM con etiqueta igual al motivo (Cotización, Garantía, Proveedores...).
6. **Vacantes**: RH publica puestos en Reclutamiento; el pie de página enlaza a /jobs.
7. **Copyright**: editar la línea de copyright de Odoo debajo del pie: "© Babatsa. Todos los derechos reservados."
8. **Aviso de privacidad**: crear la página /aviso-de-privacidad con el texto de Contabilidad.

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
