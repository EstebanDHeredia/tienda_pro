# Mi Tienda - Documentación del Proyecto

## Descripción
E-commerce completo desarrollado con Django 4.2 que incluye catálogo de productos, carrito de compras, gestión de pedidos con cupones de descuento y panel de administración.

---

## Estructura del Proyecto

```
tienda_pro/
├── tienda_pro/              # Configuración principal de Django
│   ├── settings.py          # Configuraciones del proyecto
│   ├── urls.py             # URLs principales
│   └── ...
├── catalogo/                # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas y lógica de negocio
│   ├── urls.py             # URLs de la aplicación
│   ├── admin.py            # Configuración del admin
│   ├── forms.py            # Formularios
│   ├── carrito.py           # Clase Carrito (gestión del carrito)
│   ├── signals.py          # Señales Django (stock, pedidos)
│   ├── context_processors.py # Context processors
│   ├── templates/          # Plantillas HTML
│   │   ├── base.html
│   │   ├── lista_productos.html
│   │   ├── detalle_producto.html
│   │   ├── carrito_detalle.html
│   │   ├── checkout.html
│   │   ├── lista_pedidos.html
│   │   └── dashboard.html
│   ├── static/             # Archivos estáticos (CSS, JS, imágenes)
│   └── migrations/         # Migraciones de la base de datos
├── media/                  # Archivos multimedia subidos por usuarios
├── poblar.py              # Script para poblar la BD con datos de prueba
└── manage.py              # Utilidad de línea de comandos de Django
```

---

## Modelos de Datos

### 1. Categoria
Categorías para clasificar productos.
- `nombre`: Nombre de la categoría

### 2. Producto
Productos disponibles en la tienda.
- `nombre`: Nombre del producto
- `descripcion`: Descripción detallada
- `precio`: Precio (DecimalField)
- `stock`: Cantidad disponible (IntegerField)
- `imagen`: Imagen principal (opcional)
- `categoria`: ForeignKey a Categoria

### 3. ImagenProducto
Galería de imágenes adicionales por producto.
- `producto`: ForeignKey a Producto
- `imagen`: Imagen adicional

### 4. Cupon
Cupones de descuento para los pedidos.
- `codigo`: Código único del cupón
- `descuento_porcentaje`: Porcentaje de descuento (1-100%)
- `valido_desde`: Fecha/hora de inicio de validez
- `valido_hasta`: Fecha/hora de fin de validez
- `limite_usos`: Cantidad máxima de usos permitidos
- `usos_actuales`: Contador de usos realizados
- `activo`: Si el cupón está activo
- `es_valido` (property): Valida si el cupón puede usarse

### 5. Pedido
Pedidos realizados por clientes.
- `nombre`, `apellido`, `telefono`, `direccion`: Datos del cliente
- `fecha`: Fecha de creación (auto_now_add)
- `total`: Monto total del pedido
- `estado`: Estado del pedido ('pendiente', 'pagado', 'cancelado')
- `cupon`: ForeignKey opcional a Cupon
- `descuento_aplicado`: Monto del descuento aplicado

### 6. DetallePedido
Detalle de productos en cada pedido.
- `pedido`: ForeignKey a Pedido
- `producto`: ForeignKey a Producto
- `precio`: Precio al momento de la compra
- `cantidad`: Cantidad solicitada
- `obtener_costo()`: Calcula subtotal (precio × cantidad)

---

## URLs de la Aplicación

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/` | `ListaProductosView` | Lista de productos (catálogo) |
| `/<int:pk>/` | `DetalleProductoView` | Detalle de un producto |
| `/agregar/<int:producto_id>/` | `agregar_producto` | Agregar producto al carrito |
| `/carrito/` | `ver_carrito` | Ver carrito de compras |
| `/eliminar/<int:producto_id>/` | `eliminar_producto` | Eliminar producto del carrito |
| `/limpiar/` | `limpiar_carrito` | Vaciar carrito |
| `/sumar-item/<int:producto_id>` | `sumar_item` | Aumentar cantidad en carrito |
| `/restar-item/<int:producto_id>` | `restar_item` | Disminuir cantidad en carrito |
| `/checkout/` | `pedido_crear` | Formulario de checkout |
| `/confirmado/` | `pedido_confirmado` | Confirmación y envío a WhatsApp |
| `/pedidos/` | `lista_pedidos` | Lista de pedidos (staff) |
| `/pedidos/estado/<id>/<estado>` | `cambiar_estado_pedido` | Cambiar estado de pedido |
| `/cupon/aplicar/` | `aplicar_cupon` | Aplicar cupón de descuento |
| `/cupon/eliminar/` | `eliminar_cupon` | Eliminar cupón aplicado |
| `/dashboard/` | `dashboard_ventas` | Panel de estadísticas (staff) |

---

## Gestión del Carrito

### Clase Carrito (`carrito.py`)

El carrito se maneja mediante la sesión del usuario.

**Métodos principales:**
- `agregar(producto, cantidad)`: Agrega producto al carrito
- `eliminar(producto)`: Elimina producto del carrito
- `restar(producto)`: Reduce cantidad en 1
- `limpiar()`: Vacía el carrito
- `aplicar_cupon(cupon_id)`: Aplica un cupón
- `eliminar_cupon()`: Elimina el cupón aplicado

**Propiedades:**
- `total_pagar`: Suma total sin descuentos
- `total_items`: Cantidad de productos
- `productos_detalle`: Lista detallada con objetos Producto
- `cupon`: Obtiene el cupón aplicado
- `descuento_total`: Monto del descuento
- `total_con_descuento`: Total menos descuento

---

## Señales (Signals)

### 1. `restar_stock_al_crear`
Cuando se crea un DetallePedido, descuenta el stock del producto.

### 2. `devolver_stock_al_cancelar`
Cuando un pedido se cancela, devuelve el stock de los productos.
Cuando un pedido cancelado se reactiva, descuenta el stock nuevamente.

### 3. `devolver_stock_al_borrar`
Cuando se elimina un DetallePedido, devuelve el stock.

---

## Flujo de Compra

1. **Navegación**: Usuario ve productos en `/`
2. **Detalle**: Usuario ve detalle en `/<id>/`
3. **Agregar**: Usuario agrega al carrito `/agregar/<id>/`
4. **Carrito**: Usuario revisa carrito en `/carrito/`
5. **Cupón**: Opcionalmente aplica cupón en `/cupon/aplicar/`
6. **Checkout**: Completa datos del formulario en `/checkout/`
7. **Confirmación**: Se genera pedido y se envía WhatsApp en `/confirmado/`
8. **Gestión**: Admin ve y gestiona pedidos en `/pedidos/`

---

## Panel de Administración (Django Admin)

Acceso: `/admin/`

### Gestión de Pedidos
- Lista con filtros por estado y fecha
- Cambio de estado (pendiente → pagado → cancelado)
- Visualización de cupones aplicados
- Detalle de productos en línea

### Gestión de Productos
- CRUD completo de productos
- Control de stock con alertas visuales
- Gestión de imágenes múltiples

### Gestión de Cupones
- Crear/editar cupones
- Definir fechas de validez
- Establecer límite de usos
- Activar/desactivar cupones

---

## Dashboard de Ventas

Acceso: `/dashboard/` (solo staff)

**Estadísticas disponibles:**
- Total recaudado (pedidos pagados)
- Ventas últimos 7 días
- Ticket promedio
- Top 5 productos más vendidos
- Alertas de stock crítico
- Gráfico de ventas diarias (últimos 7 días)

---

## Comandos de Gestión

### Poblar Base de Datos
```bash
python manage.py poblar_db
```
Crea categorías, productos con imágenes y pedidos de prueba.

---

## Configuración de Medios

Los archivos subidos (imágenes de productos) se guardan en:
```
media/productos/
```

---

## WhatsApp Integration

Los pedidos se confirman mediante WhatsApp:
- URL configurada en `pedido_confirmado()` (views.py)
- Número de teléfono configurable en la vista
- Mensaje formateado con datos del pedido y cupón

---

## Tecnologías Utilizadas

- **Backend**: Django 4.2
- **Base de datos**: SQLite (desarrollo)
- **Frontend**: HTML5, CSS3, JavaScript
- **Gráficos**: Chart.js
- **Imágenes**: LoremFlickr (descarga automática)
- **Comunicación**: WhatsApp API

---

## Requisitos de Instalación

```bash
pip install django
pip install pillow  # Para imágenes
```

### Ejecutar el Proyecto
```bash
cd tienda_pro
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Notas de Desarrollo

- El stock se gestiona automáticamente mediante señales Django
- Los cupones se almacenan en sesión hasta confirmar el pedido
- El carrito persiste en la sesión del navegador
- Las imágenes se descargan de loremflickr.com para desarrollo
