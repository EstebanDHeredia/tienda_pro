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

# Create your views here.
class ListaProductosView(ListView):
    model = Producto
    template_name = 'catalogo/lista.html'
    context_object_name = 'mis_productos'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Producto.objects.filter(stock__gt=0)
       
        # 1. Filtro de búsqueda
        termino = self.request.GET.get('buscar')

        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino) | Q(descripcion__icontains=termino))

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
            # Usamos '-id' para que los últimos productos añadidos salgan primero
            queryset = queryset.order_by('-id') 

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Categoria
        context['categorias'] = Categoria.objects.all()
        
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            context['categoria_seleccionada'] = Categoria.objects.get(id=categoria_id)
        
        return context
        
class DetalleProductoView(DetailView):
    model = Producto
    template_name = "catalogo/detalle.html"
    context_object_name = 'producto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relacionados'] = Producto.objects.filter(
            categoria=self.object.categoria,
            stock__gt=0
        ).exclude(id=self.object.id)[:3]
        context['galeria'] = self.object.imagenes.all()
        
        # Calcular stock disponible (total - lo que ya está en carrito)
        carrito = Carrito(self.request)
        cantidad_en_carrito = 0
        id_prod = str(self.object.id)
        if id_prod in carrito.carrito:
            cantidad_en_carrito = carrito.carrito[id_prod]['cantidad']
        context['stock_disponible'] = self.object.stock - cantidad_en_carrito
        
        return context

def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)

    cantidad = int(request.POST.get('cantidad',1))
    
    fue_posible = carrito.agregar(producto=producto, cantidad=cantidad)
    
    if not fue_posible:
        messages.error(request, f"⚠️ !Lo sentimos! No hay más stock de {producto.nombre}. ")
    else:   
        messages.success(request, f"✅ Se agregó una unidad de {producto.nombre}.")
    
    return redirect('detalle', pk=producto_id)
        
def ver_carrito(request):
    return render(request, 'catalogo/carrito_detalle.html')

def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    return redirect('ver_carrito')

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('ver_carrito')
  
     
def sumar_item(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    
    fue_posible = carrito.agregar(producto=producto)

    if not fue_posible:
        messages.error(request, f"⚠️ !Lo sentimos! No hay más stock de {producto.nombre}. ")
    else:   
        messages.success(request, f"✅ Se agregó una unidad de {producto.nombre}.")
    
    return redirect('ver_carrito')

def restar_item(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    return redirect('ver_carrito')

def pedido_crear(request):
    carrito = Carrito(request)
    if request.method == 'POST':
        form = PedidoCreateForm(request.POST)
        if form.is_valid():
            # Creo el objeto pedido
            pedido = form.save(commit=False) # Crea el objeto pero todavia no lo guarda
            pedido.total = carrito.total_con_descuento
            
            cupon_id = request.session.get('cupon_id')
            if cupon_id:
                try:
                    cupon = Cupon.objects.get(id=cupon_id)
                    if cupon.es_valido:
                        pedido.cupon = cupon
                        pedido.descuento_aplicado = carrito.descuento_total
                        del request.session['cupon_id']
                except Cupon.DoesNotExist:
                    pass
            
            pedido.save() # Ahora lo guardamos en la BD (antes llama a las signals pre_save, calcula el descuento y modifica el total si hay un cupon) y se le da una ID
            
            # Guardamos cada item del carrito en DetallePedido
            for item in carrito.productos_detalle:
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=item['producto'], # El objeto producto REAL
                    precio=Decimal(item['precio']), # El precio en la BD es un DecimalFielditem['precio'],
                    cantidad=item['cantidad']
                )
            
            # Guardo en el Id del pedido en la sesión, para utilizarlo en la redirección
            request.session['pedido_id'] = pedido.id

            # Redirigimos a una nueva funcion que enviará a whatsapp
            return redirect('pedido_confirmado')

    else:
        form = PedidoCreateForm()
        
    return render(request, 'catalogo/checkout.html', {'carrito': carrito, 'form':form})

def pedido_confirmado(request):
    pedido_id = request.session.get('pedido_id')
    pedido = get_object_or_404(Pedido, id=pedido_id)
    carrito = Carrito(request)

    # Contruyo el msj de WhatsApp con los datos del formulario
    mensaje = "🛒 NUEVO PEDIDO - Mi Tienda\n\n"
    mensaje = f" *Pedido: #{pedido.id}*\n"
    mensaje += f" Cliente: {pedido.nombre} {pedido.apellido}\n"
    mensaje += f" Entrega: {pedido.direccion}\n"
    mensaje += f" Tel: {pedido.telefono}\n"
    mensaje += "----------------------------------------------------\n\n"

    for item in pedido.items.all(): #'items' es el related_name que puse en DetallePedido
        mensaje += f"📦 {item.producto.nombre}\n"
        mensaje += f"  Cantidad: {item.cantidad}\n"
        mensaje += f"  Precio: ${item.precio}\n"
        mensaje += f"  Subtotal: ${item.obtener_costo()}\n\n"
    
    mensaje += "===========================\n"
    if pedido.cupon:
        mensaje += f"🎟️ Cupón aplicado: {pedido.cupon.codigo} ({pedido.cupon.descuento_porcentaje}%)\n"
        mensaje += f"💸 Descuento: -${pedido.descuento_aplicado}\n"
        mensaje += "---------------------------\n"
    mensaje += f"💰 *TOTAL: ${pedido.total}*\n"
    mensaje += "===========================\n\n"
    mensaje += "Gracias por tu compra!"  
            

    # limpiamos el carrito y el Id del pedido de la sesion
    carrito.limpiar()
    del request.session['pedido_id']
    
    telefono = "5493512946883"
    params = {'phone': telefono, 'text': mensaje}
    url_base = "https://api.whatsapp.com/send?"
    url_encoded = urllib.parse.urlencode(params, safe='')
    url_whatsapp = url_base + url_encoded

    return redirect(url_whatsapp)

@staff_member_required # Solo el estaff puede ver lo que devuelve esta funcion
def dashboard_ventas(request):
    # --- FILTROS DE TIEMPO ---
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=6) # Usamos 6 para incluir "hoy" y completar 7 días
        
    # Total de dinero recaudado (solo los pedidos pagados)
    total_recaudado = Pedido.objects.filter(estado='pagado').aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas de los ultimos 7 dias
    ventas_recientes = Pedido.objects.filter(estado='pagado', fecha__gte = hace_7_dias).aggregate(Sum('total'))['total__sum'] or 0
    
    # Tckt promedio
    cantidad_pagados = Pedido.objects.filter(estado='pagado').count()
    ticket_promedio = total_recaudado / cantidad_pagados if cantidad_pagados > 0 else 0
    
    # Stock crítico
    # Productos con menos de 5 unidades
    stock_critico = Producto.objects.filter(stock__lt=5).order_by('stock')
    
    # Cantidad de pedidos según su estado
    conteo_estados = Pedido.objects.values('estado').annotate(cantidad=Count('id'))
    
    # Los 5 productos mas vendidos:
    productos_top = DetallePedido.objects.values('producto__nombre').annotate(
        vendidos=Sum('cantidad')
    ).order_by('-vendidos')[:5]

    # DATOS PARA EL GRAFICO DE VENTAS DIARIAS DE LOS ULTIMOS 7 DIAS
    ventas_diarias = Pedido.objects.filter(
        estado='pagado',
        fecha__date__gte=hace_7_dias
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            total=Sum('total')
        ).order_by('dia')
        
    # print("------------------------------------------")
    # print("VENTAS DIARIAS")
    # for v in ventas_diarias:
    #     print(v['dia'])
    #     print(v['total'])
    # print("------------------------------------------")
        
    #Preparo las listas para el javascript
    labels_grafico = []
    datos_grafico = []
    
    # Logica para rellenar dias con 0
    for i in range(7):
        fecha_loop = hace_7_dias + timedelta(days=i)
        print("fecha_loop")
        print(fecha_loop)
        labels_grafico.append(fecha_loop.strftime("%d/%m"))
        
        # Buscamos si hay venta ese dia en el queryset
        # for v in ventas_diarias:
        #     print("v.dia = {}, v.total = {}, fecha_loop = {}".format(v['dia'], v['total'], fecha_loop))
        #     print(TruncDate(fecha_loop))
        #     if v['dia'] == fecha_loop:
        #         print ("coincide")
        #     else:
        #         print("no coincide")
            
        venta_dia = next((v['total'] for v in ventas_diarias if v['dia'] == fecha_loop), 0)
        datos_grafico.append(float(venta_dia))
        
    # print("--------------------------------------------")
    # print("labels_grafico")
    # print(labels_grafico)
    # print("---------------------------------------------")
    # print("datos_grafico")
    # print(datos_grafico)
    
    # Buscamos el producto que mas generó dinero en la semana
    producto_estrella = DetallePedido.objects.filter(
        pedido__estado='pagado',
        pedido__fecha__gte = hace_7_dias # Filtramos los detalle pedido de los pedidos con estado 'pagado' y con fecha mayor o igual que hace 7 dias
        ).annotate(
            subtotal_detalle = F('precio') * F('cantidad') # Al resultado anterior le agrego una columna 'annotate' que se va a llamar subtotal_detalle en el que se calcula el total de la venta de ese producto al multiplicar el precio x la cantidad
        ).values('producto__nombre',
                 'producto__imagen',
                 'producto__stock').annotate( # A ese resultado lo agrupo 'values' por nombre del producto e imagen (lo hago por imagen ya que es un campo que voy a necesitar luego para mostrar la imagen del producto) y stock (porque tambie lo voy a necesitar despues)
            total_recaudado_prod = Sum('subtotal_detalle') # Y a esa agrupación le agrego un campo 'total_recaudado_prod con la suma de los subtotales de ese producto
        ).order_by('-total_recaudado_prod').first() # De todo eso lo ordeno de mayor  a menor y de esa ordenación saco el primero. Es decir el producto que mas ingreso me produjo (precio x cantidad) enn los ultimos 7 dias
    
    print(producto_estrella)
    
    
    context = {
        'total_recaudado': total_recaudado,
        'conteo_estados': conteo_estados,
        'productos_top': productos_top,
        'ventas_recientes': ventas_recientes,
        'ticket_promedio': ticket_promedio,
        'stock_critico': stock_critico,
        'labels_grafico': labels_grafico,
        'datos_grafico': datos_grafico,
        'producto_estrella': producto_estrella
    }
    
    return render(request, 'catalogo/dashboard.html', context)

@staff_member_required
def lista_pedidos(request):
    # Obtenemos el filtro 'estado' si existe:
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
    print("cambiar_estado_pedido")
    pedido = get_object_or_404(Pedido, id = pedido_id)
    pedido.estado = nuevo_estado
    pedido.save()
    messages.success(request, f"Pedido #{pedido.id} marcado como {nuevo_estado}.")
    return redirect('lista_pedidos')
    
def aplicar_cupon(request):
    cart = Carrito(request)
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        print("------------------------------")
        print(f"DEBUG: {codigo}")
        print("-------------------------------")
        try:
            cupon = Cupon.objects.get(codigo__iexact=codigo)
            print(f"DEBUG: objeto CUPON:{cupon}")
            if cupon.es_valido:
                cart.aplicar_cupon(cupon.id)
                messages.success(request, f"Descuento del {cupon.descuento_porcentaje}% aplicado.")
            else:
                messages.error(request, "Este cupón ya expiró o no tiene mas usos.")
        except:
            messages.error(request, "El código de cupón no existe.")                
        
        return redirect('ver_carrito')
def eliminar_cupon(request):
    cart = Carrito(request)
    cart.eliminar_cupon()
    messages.success(request, "Cupón eliminado.")
    return redirect('ver_carrito')



# def sumar_item(request, producto_id):
    # producto = get_object_or_404(Producto, id=producto_id)
    
    # fue_posible = carrito.agregar(producto=producto)

    # if not fue_posible:
    #     messages.error(request, f"⚠️ !Lo sentimos! No hay más stock de {producto.nombre}. ")
    # else:   
    #     messages.success(request, f"✅ Se agregó una unidad de {producto.nombre}.")
    
    # return redirect('ver_carrito')



    return redirect('ver_carrito')

# def finalizar_pedido(request):
#     carrito = Carrito(request)

#     if not carrito.carrito:
#         return redirect('lista')


#     # --- Configuración del Mensaje Decorado ---
#     mensaje = "🛒 NUEVO PEDIDO - Mi Tienda\n\n"
        
#     for key, value in carrito.carrito.items():
#         # Descuento el stock del producto
#         producto = Producto.objects.get(id=value['producto_id'])
#         producto.stock -= value['cantidad']
#         producto.save()
        
#         # Genero el msj de whatsApp
#         mensaje += f"📦 {value['nombre']}\n"
#         mensaje += f"  Cantidad: {value['cantidad']}\n"
#         mensaje += f"  Precio: ${value['precio']}\n"
#         mensaje += f"  Subtotal: ${value['subtotal']}\n\n"

#     mensaje += "===========================\n"
#     mensaje += f"💰 TOTAL: ${carrito.total_pagar}\n"
#     mensaje += "===========================\n\n"
#     mensaje += "Gracias por tu compra!"    
#     mensaje += "_Por favor, confírmame los datos para la entrega._"
    
#     # Codificar el mensaje de forma robusta para WhatsApp
#     telefono = "5493512946883"
#     params = {'phone': telefono, 'text': mensaje}
#     url_base = "https://api.whatsapp.com/send?"
#     url_encoded = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
#     url_whatsapp = url_base + url_encoded

#     return redirect(url_whatsapp)