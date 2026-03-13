from django.utils.html import format_html
from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto, DetallePedido, Pedido



# Configuración para ver los productos dentro pedido (como una tabla)
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ['producto', 'precio', 'cantidad', 'obtener_costo']
    can_delete = False
    

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # inlines = [ImagenProductoInline]
    list_display = ['mostrar_imagen', 'nombre', 'precio', 'stock_alerta', 'categoria']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['categoria']

    def mostrar_imagen(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 5px; object-fit: cover;" />', obj.imagen.url
            )
        return "Sin imagen"

    mostrar_imagen.short_description = 'Foto'
    
    def stock_alerta(self, obj):
        # Si hay poco stock, lo ponemos en rojo
        color = 'red' if obj.stock <= 5 else 'inherit'
        return format_html(
            '<b style="color: {};">{}</b>', color, obj.stock
        )
        
    stock_alerta.short_description = 'Stock'

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    
    def colorear_estado(self, obj):
        colores = {
            'pendiente': '#f1c40f',
            'pagado': '#2ecc71',
            'cancelado': '#e74c3c',
        }
        color = colores.get(obj.estado, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 12px; font-weight: bold; text-transform: uppercase; font-size: 10px;">{}</span>',
            color,
            obj.get_estado_display() # Muestra el texto legible (ej: "Pendiente de Pago") de la tupla que creamos para los estados. Si pusiera obj.estado me devolveria 'pendiente'. Django genera automáticamente estas funciones get_CAMPO_display() para cualquier campo que tenga choices.
        )
    
    colorear_estado.short_description = 'Estado' # Título de la columna
        
    # Qué columnas se ven en la tabla principal
    list_display = ['id', 'nombre', 'apellido', 'fecha','total', 'colorear_estado']

    # Buscador por nombre de cliente o ID de pedido
    search_fields = ['nombre', 'apellido', 'id']
    
    # Filtros laterales para encontrar pedidos rápido
    list_filter = ['estado', 'fecha']
    
    # Hacemos que el estado sea editable desde la lista sin entrar al pedido
    list_editable = []
    
    # Ordenar la tabla por fecha de pedido
    ordering = ['-fecha']
    
    inlines = [DetallePedidoInline]
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'apellido', 'telefono', 'direccion'),
            'classes': ('wide',),
        }),
        ('Estado y Totales', {
            'fields': ('estado', 'total'),
            'description': 'Recuerda que al cambiar a <b>Pagado</b> se descontará el stock.'
        }),
    )
    readonly_fields = ['total', 'fecha'] # Evita errores humanos
    
    
    
    def save_model(self, request, obj, form, change):
        # Si el estado cambió a 'pagado' en esta edición
        if 'estado' in form.changed_data and obj.estado == 'pagado':
            for item in obj.items.all():
                producto = item.producto
                producto.stock -= item.cantidad
                producto.save()
                
        super().save_model(request, obj, form, change)
    

admin.site.register(Categoria)
