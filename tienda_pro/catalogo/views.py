"""
Vistas de la aplicación catalogo.

Este módulo contiene todas las vistas (funciones y clases) que manejan
las solicitudes HTTP y retornan respuestas para el usuario.
"""

from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from decimal import Decimal
from .forms import PedidoCreateForm
import urllib.parse
import json
from urllib.parse import quote
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView
from .models import Producto, DetallePedido, Pedido, Cupon
from .carrito import Carrito
from django.db.models import Q
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F


# =============================================================================
# VISTAS DE PRODUCTOS
# =============================================================================

class ListaProductosView(ListView):
    """
    Vista basada en clases para listar productos del catálogo.
    
    Presenta una lista paginada de productos con soporte para:
    - Búsqueda por nombre o descripción
    - Filtrado por categoría
    - Ordenamiento por precio o por fecha de creación
    
    Template: catalogo/lista.html
    Contexto: 'mis_productos' (lista de productos paginada)
    """
    
    model = Producto
    template_name = 'catalogo/lista.html'
    context_object_name = 'mis_productos'
    paginate_by = 6  # Productos por página
    
    def get_queryset(self):
        """
        Obtiene y filtra el queryset de productos.
        
        Permite tres tipos de filtros:
        1. buscar: Busca en nombre y descripción (case-insensitive)
        2. categoria: Filtra por ID de categoría
        3. orden: 'barato' (ascendente) o 'caro' (descendente)
        
        Returns:
            QuerySet de Producto filtrado y ordenado
        """
        queryset = Producto.objects.filter(stock__gt=0)
       
        # 1. Filtro de búsqueda
        termino = self.request.GET.get('buscar')
        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino) | Q(descripcion__icontains=termino)
            )

        # 2. Filtro de categoría
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        # 3. Ordenamiento
        orden = self.request.GET.get('orden')
        if orden == 'barato':
            queryset = queryset.order_by('precio')
        elif orden == 'caro':
            queryset = queryset.order_by('-precio')
        else:
            queryset = queryset.order_by('-id')

        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto de la plantilla.
        
        Añade:
        - Lista de todas las categorías para el menú de filtros
        - Categoría seleccionada actualmente (si aplica)
        
        Returns:
            Dict con el contexto para la plantilla
        """
        context = super().get_context_data(**kwargs)
        from .models import Categoria
        context['categorias'] = Categoria.objects.all()
        
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            context['categoria_seleccionada'] = Categoria.objects.get(id=categoria_id)
        
        return context


class DetalleProductoView(DetailView):
    """
    Vista para mostrar el detalle de un producto individual.
    
    Muestra información completa del producto incluyendo:
    - Datos del producto
    - Galería de imágenes adicionales
    - Productos relacionados de la misma categoría
    - Stock disponible considerando el carrito actual
    
    Template: catalogo/detalle.html
    Contexto: 'producto' (objeto Producto)
    """
    
    model = Producto
    template_name = "catalogo/detalle.html"
    context_object_name = 'producto'
    
    def get_context_data(self, **kwargs):
        """
        Agrega datos adicionales al contexto.
        
        Añade:
        - productos relacionados (misma categoría, máximo 3)
        - galería de imágenes del producto
        - stock disponible (stock total menos cantidad en carrito)
        
        Returns:
            Dict con el contexto para la plantilla
        """
        context = super().get_context_data(**kwargs)
        
        # Productos relacionados de la misma categoría (excluye el producto actual)
        context['relacionados'] = Producto.objects.filter(
            categoria=self.object.categoria,
            stock__gt=0
        ).exclude(id=self.object.id)[:3]
        
        # Galería de imágenes adicionales
        context['galeria'] = self.object.imagenes.all()
        
        # Calcular stock disponible considerando el carrito actual
        carrito = Carrito(self.request)
        cantidad_en_carrito = 0
        id_prod = str(self.object.id)
        if id_prod in carrito.carrito:
            cantidad_en_carrito = carrito.carrito[id_prod]['cantidad']
        context['stock_disponible'] = self.object.stock - cantidad_en_carrito
        
        return context


# =============================================================================
# VISTAS DEL CARRITO DE COMPRAS
# =============================================================================

def agregar_producto(request, producto_id):
    """
    Agrega un producto al carrito de compras.
    
    Recibe el ID del producto y la cantidad del formulario POST.
    Valida que haya stock disponible antes de agregar.
    
    Args:
        request: HttpRequest con POST conteniendo 'cantidad'
        producto_id: ID del producto a agregar
        
    Returns:
        Redirect a la página de detalle del producto
        
    Mensajes:
        - Éxito: 'Se agregó una unidad de {producto}'
        - Error: 'No hay más stock de {producto}'
    """
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    
    cantidad = int(request.POST.get('cantidad', 1))
    fue_posible = carrito.agregar(producto=producto, cantidad=cantidad)
    
    if not fue_posible:
        messages.error(request, f"No hay más stock de {producto.nombre}.")
    else:
        messages.success(request, f"Se agregaron {cantidad} unidades de {producto.nombre}.")
    
    return redirect('detalle', pk=producto_id)


def ver_carrito(request):
    """
    Muestra la página del carrito de compras.
    
    Renderiza la plantilla con el carrito actual.
    El objeto 'carrito' se agrega automáticamente via context_processor.
    
    Template: catalogo/carrito_detalle.html
    """
    return render(request, 'catalogo/carrito_detalle.html')


def eliminar_producto(request, producto_id):
    """
    Elimina un producto completamente del carrito.
    
    No reduce la cantidad, elimina el producto por completo.
    
    Args:
        request: HttpRequest
        producto_id: ID del producto a eliminar
        
    Returns:
        Redirect a la página del carrito
    """
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    return redirect('ver_carrito')


def limpiar_carrito(request):
    """
    Vacía completamente el carrito de compras.
    
    Elimina todos los productos del carrito del usuario.
    
    Returns:
        Redirect a la página del carrito
    """
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('ver_carrito')


def sumar_item(request, producto_id):
    """
    Aumenta en 1 la cantidad de un producto en el carrito.
    
    Valida que haya stock disponible antes de aumentar.
    
    Args:
        request: HttpRequest
        producto_id: ID del producto a incrementar
        
    Returns:
        Redirect a la página del carrito
        
    Mensajes:
        - Éxito: 'Se agregó una unidad de {producto}'
        - Error: 'No hay más stock de {producto}'
    """
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    
    fue_posible = carrito.agregar(producto=producto)

    if not fue_posible:
        messages.error(request, f"No hay más stock de {producto.nombre}.")
    else:
        messages.success(request, f"Se agregó una unidad de {producto.nombre}.")
    
    return redirect('ver_carrito')


def restar_item(request, producto_id):
    """
    Reduce en 1 la cantidad de un producto en el carrito.
    
    Si la cantidad llega a 0, elimina el producto del carrito.
    
    Args:
        request: HttpRequest
        producto_id: ID del producto a decrementar
        
    Returns:
        Redirect a la página del carrito
    """
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    return redirect('ver_carrito')


# =============================================================================
# VISTAS DE PEDIDOS
# =============================================================================

def pedido_crear(request):
    """
    Maneja el formulario de checkout y creación de pedidos.
    
    Proceso:
    1. GET: Muestra el formulario con datos del carrito
    2. POST: Valida datos, crea el pedido con cupón si existe,
             guarda los detalles y redirige a confirmación
    
    Template: catalogo/checkout.html
    Contexto: 'carrito' (Carrito), 'form' (PedidoCreateForm)
    
    El pedido se crea con:
    - Datos del cliente del formulario
    - Total calculado con descuento (si hay cupón)
    - Cupón y descuento aplicado (si existe)
    """
    carrito = Carrito(request)
    
    if request.method == 'POST':
        form = PedidoCreateForm(request.POST)
        if form.is_valid():
            # Crear objeto pedido sin guardarlo aún
            pedido = form.save(commit=False)
            
            # Usar total CON descuento
            pedido.total = carrito.total_con_descuento
            
            # Verificar si hay cupón en sesión
            cupon_id = request.session.get('cupon_id')
            if cupon_id:
                try:
                    cupon = Cupon.objects.get(id=cupon_id)
                    if cupon.es_valido:
                        pedido.cupon = cupon
                        pedido.descuento_aplicado = carrito.descuento_total
                        # Eliminar cupón de sesión después de aplicar
                        del request.session['cupon_id']
                except Cupon.DoesNotExist:
                    pass
            
            # Guardar pedido (desencadena signals para stock)
            pedido.save()
            
            # Crear detalles del pedido para cada producto
            for item in carrito.productos_detalle:
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=item['producto'],
                    precio=Decimal(item['precio']),
                    cantidad=item['cantidad']
                )
            
            # Guardar ID del pedido en sesión para usar en confirmación
            request.session['pedido_id'] = pedido.id
            
            return redirect('pedido_confirmado')
    else:
        form = PedidoCreateForm()
        
    return render(request, 'catalogo/checkout.html', {'carrito': carrito, 'form': form})


def pedido_confirmado(request):
    """
    Confirma el pedido y envía notificación por WhatsApp.
    
    Proceso:
    1. Obtiene el pedido de la sesión
    2. Construye mensaje con todos los datos
    3. Incluye información del cupón si se aplicó
    4. Limpia carrito y sesión
    5. Redirige a WhatsApp con mensaje prellenado
    
    El mensaje incluye:
    - Datos del cliente
    - Lista de productos con cantidades y precios
    - Cupón aplicado (si existe)
    - Descuento y total final
    """
    pedido_id = request.session.get('pedido_id')
    pedido = get_object_or_404(Pedido, id=pedido_id)
    carrito = Carrito(request)

    # Construir mensaje de WhatsApp
    mensaje = "🛒 NUEVO PEDIDO - Mi Tienda\n\n"
    mensaje += f"Pedido: #{pedido.id}\n"
    mensaje += f"Cliente: {pedido.nombre} {pedido.apellido}\n"
    mensaje += f"Entrega: {pedido.direccion}\n"
    mensaje += f"Tel: {pedido.telefono}\n"
    mensaje += "----------------------------------------------------\n\n"

    # Detalle de productos
    for item in pedido.items.all():
        mensaje += f"📦 {item.producto.nombre}\n"
        mensaje += f"  Cantidad: {item.cantidad}\n"
        mensaje += f"  Precio: ${item.precio}\n"
        mensaje += f"  Subtotal: ${item.obtener_costo()}\n\n"
    
    # Totales (con cupón si aplica)
    mensaje += "===========================\n"
    if pedido.cupon:
        mensaje += f"🎟️ Cupón: {pedido.cupon.codigo} ({pedido.cupon.descuento_porcentaje}%)\n"
        mensaje += f"💸 Descuento: -${pedido.descuento_aplicado}\n"
        mensaje += "---------------------------\n"
    mensaje += f"💰 TOTAL: ${pedido.total}\n"
    mensaje += "===========================\n\n"
    mensaje += "Gracias por tu compra!"

    # Limpiar carrito y sesión
    carrito.limpiar()
    del request.session['pedido_id']
    
    # Redirigir a WhatsApp
    telefono = "5493512946883"
    params = {'phone': telefono, 'text': mensaje}
    url_base = "https://api.whatsapp.com/send?"
    url_encoded = urllib.parse.urlencode(params, safe='')
    url_whatsapp = url_base + url_encoded

    return redirect(url_whatsapp)


# =============================================================================
# VISTAS DE ADMINISTRACIÓN (STAFF)
# =============================================================================

@staff_member_required
def dashboard_ventas(request):
    """
    Panel de dashboard con estadísticas de ventas.
    
    Solo accesible para usuarios staff (administradores).
    
    Estadísticas calculadas:
    - Total recaudo (pedidos pagados)
    - Ventas últimos 7 días
    - Ticket promedio
    - Productos más vendidos (top 5)
    - Stock crítico (menos de 5 unidades)
    - Ventas diarias (para gráfico)
    - Producto estrella de la semana
    
    Template: catalogo/dashboard.html
    """
    # Período de análisis: últimos 7 días
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=6)
        
    # Total acumulado (solo pedidos pagados)
    total_recaudado = Pedido.objects.filter(
        estado='pagado'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas de los últimos 7 días
    ventas_recientes = Pedido.objects.filter(
        estado='pagado',
        fecha__gte=hace_7_dias
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ticket promedio
    cantidad_pagados = Pedido.objects.filter(estado='pagado').count()
    ticket_promedio = total_recaudado / cantidad_pagados if cantidad_pagados > 0 else 0
    
    # Productos con stock crítico (menos de 5 unidades)
    stock_critico = Producto.objects.filter(stock__lt=5).order_by('stock')
    
    # Conteo de pedidos por estado
    conteo_estados = Pedido.objects.values('estado').annotate(cantidad=Count('id'))
    
    # Top 5 productos más vendidos
    productos_top = DetallePedido.objects.values('producto__nombre').annotate(
        vendidos=Sum('cantidad')
    ).order_by('-vendidos')[:5]

    # Ventas diarias para gráfico (últimos 7 días)
    ventas_diarias = Pedido.objects.filter(
        estado='pagado',
        fecha__date__gte=hace_7_dias
    ).annotate(
        dia=TruncDate('fecha')
    ).values('dia').annotate(
        total=Sum('total')
    ).order_by('dia')
        
    # Preparar datos para JavaScript (gráfico)
    labels_grafico = []
    datos_grafico = []
    
    # Rellenar todos los días (incluye días sin ventas = 0)
    for i in range(7):
        fecha_loop = hace_7_dias + timedelta(days=i)
        labels_grafico.append(fecha_loop.strftime("%d/%m"))
        
        # Buscar si hay venta ese día
        venta_dia = next(
            (v['total'] for v in ventas_diarias if v['dia'] == fecha_loop),
            0
        )
        datos_grafico.append(float(venta_dia))
    
    # Producto que más ingresos generó en la semana
    producto_estrella = DetallePedido.objects.filter(
        pedido__estado='pagado',
        pedido__fecha__gte=hace_7_dias
    ).annotate(
        subtotal_detalle=F('precio') * F('cantidad')
    ).values(
        'producto__nombre',
        'producto__imagen',
        'producto__stock'
    ).annotate(
        total_recaudado_prod=Sum('subtotal_detalle')
    ).order_by('-total_recaudado_prod').first()
    
    context = {
        'total_recaudado': total_recaudado,
        'conteo_estados': conteo_estados,
        'productos_top': productos_top,
        'ventas_recientes': ventas_recientes,
        'ticket_promedio': ticket_promedio,
        'stock_critico': stock_critico,
        'labels_grafico': json.dumps(labels_grafico),
        'datos_grafico': json.dumps(datos_grafico),
        'producto_estrella': producto_estrella
    }
    
    return render(request, 'catalogo/dashboard.html', context)


@staff_member_required
def lista_pedidos(request):
    """
    Lista todos los pedidos con filtro opcional por estado.
    
    Solo accesible para usuarios staff.
    
    Filtros:
    - estado: 'pendiente', 'pagado' o 'cancelado'
    
    Template: catalogo/lista_pedidos.html
    """
    filtro_estado = request.GET.get('estado')
    pedidos = Pedido.objects.all().order_by('-fecha')

    if filtro_estado:
        pedidos = pedidos.filter(estado=filtro_estado)
    
    return render(request, 'catalogo/lista_pedidos.html', {
        'filtro_estado': filtro_estado,
        'pedidos': pedidos
    })


@staff_member_required
def cambiar_estado_pedido(request, pedido_id, nuevo_estado):
    """
    Cambia el estado de un pedido.
    
    Estados válidos: 'pendiente', 'pagado', 'cancelado'
    
    Args:
        pedido_id: ID del pedido a modificar
        nuevo_estado: Nuevo estado ('pendiente', 'pagado', 'cancelado')
        
    Returns:
        Redirect a lista_pedidos
        
    Nota:
        El cambio de estado también afecta el stock gracias a las signals.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.estado = nuevo_estado
    pedido.save()
    messages.success(request, f"Pedido #{pedido.id} marcado como {nuevo_estado}.")
    return redirect('lista_pedidos')


# =============================================================================
# VISTAS DE CUPONES
# =============================================================================

def aplicar_cupon(request):
    """
    Aplica un cupón de descuento al carrito.
    
    Proceso:
    1. Obtiene código del POST
    2. Busca cupón en la base de datos
    3. Valida que el cupón sea válido
    4. Guarda ID del cupón en la sesión
    
    Args:
        request: HttpRequest POST con 'codigo'
        
    Returns:
        Redirect a ver_carrito
        
    Mensajes:
        - Éxito: 'Descuento del X% aplicado.'
        - Error: 'Este cupón ya expiró o no tiene más usos.'
        - Error: 'El código de cupón no existe.'
    """
    cart = Carrito(request)
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        
        try:
            cupon = Cupon.objects.get(codigo__iexact=codigo)
            if cupon.es_valido:
                cart.aplicar_cupon(cupon.id)
                messages.success(request, f"Descuento del {cupon.descuento_porcentaje}% aplicado.")
            else:
                messages.error(request, "Este cupón ya expiró o no tiene más usos.")
        except Cupon.DoesNotExist:
            messages.error(request, "El código de cupón no existe.")
        
        return redirect('ver_carrito')
    
    return redirect('ver_carrito')


def eliminar_cupon(request):
    """
    Elimina el cupón aplicado del carrito.
    
    Quita el cupón de la sesión sin validar nada.
    
    Returns:
        Redirect a ver_carrito
        
    Mensajes:
        Éxito: 'Cupón eliminado.'
    """
    cart = Carrito(request)
    cart.eliminar_cupon()
    messages.success(request, "Cupón eliminado.")
    return redirect('ver_carrito')
