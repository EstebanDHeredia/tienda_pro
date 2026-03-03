from django.contrib import messages
from django.http import JsonResponse
import urllib.parse
from urllib.parse import quote
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView
from .models import Producto
from .carrito import Carrito
from django.db.models import Q

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
    
def finalizar_pedido(request):
    carrito = Carrito(request)

    if not carrito.carrito:
        return redirect('lista')


    # --- Configuración del Mensaje Decorado ---
    mensaje = "🛒 NUEVO PEDIDO - Mi Tienda\n\n"
        
    for key, value in carrito.carrito.items():
        # Descuento el stock del producto
        producto = Producto.objects.get(id=value['producto_id'])
        producto.stock -= value['cantidad']
        producto.save()
        
        # Genero el msj de whatsApp
        mensaje += f"📦 {value['nombre']}\n"
        mensaje += f"  Cantidad: {value['cantidad']}\n"
        mensaje += f"  Precio: ${value['precio']}\n"
        mensaje += f"  Subtotal: ${value['subtotal']}\n\n"

    mensaje += "===========================\n"
    mensaje += f"💰 TOTAL: ${carrito.total_pagar}\n"
    mensaje += "===========================\n\n"
    mensaje += "Gracias por tu compra!"    
    mensaje += "_Por favor, confírmame los datos para la entrega._"
    
    # Codificar el mensaje de forma robusta para WhatsApp
    telefono = "5493512946883"
    params = {'phone': telefono, 'text': mensaje}
    url_base = "https://api.whatsapp.com/send?"
    url_encoded = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url_whatsapp = url_base + url_encoded

    return redirect(url_whatsapp)

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
