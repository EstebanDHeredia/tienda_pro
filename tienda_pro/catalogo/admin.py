from django.utils.html import format_html
from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto, DetallePedido, Pedido, Cupon



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
            obj.get_estado_display()
        )
    
    colorear_estado.short_description = 'Estado'
    
    def mostrar_cupon(self, obj):
        if obj.cupon:
            return format_html(
                '<span style="background-color: #2ecc71; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">{} (-{}%)</span>',
                obj.cupon.codigo,
                obj.cupon.descuento_porcentaje
            )
        return '-'
    
    mostrar_cupon.short_description = 'Cupón'
    
    def total_final(self, obj):
        return f"${obj.total - obj.descuento_aplicado:,.2f}"
    
    total_final.short_description = 'Total Final'
        
    list_display = ['id', 'nombre', 'apellido', 'fecha', 'mostrar_cupon', 'descuento_aplicado', 'total', 'colorear_estado']

    search_fields = ['nombre', 'apellido', 'id']
    
    list_filter = ['estado', 'fecha', 'cupon']
    
    list_editable = []
    
    ordering = ['-fecha']
    
    inlines = [DetallePedidoInline]
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'apellido', 'telefono', 'direccion'),
            'classes': ('wide',),
        }),
        ('Cupón Aplicado', {
            'fields': ('cupon', 'descuento_aplicado'),
            'classes': ('wide',),
        }),
        ('Estado y Totales', {
            'fields': ('estado', 'total'),
            'description': 'Recuerda que al cambiar a <b>Pagado</b> se descontará el stock.'
        }),
    )
    readonly_fields = ['total', 'fecha', 'descuento_aplicado']

@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descuento_porcentaje', 'valido_hasta', 'usos_actuales', 'limite_usos', 'activo']
    list_filter = ['activo', 'valido_hasta']
    search_fields = ['codigo']
    
    
    # BORRA ESTO DE ACÁ, TODA LA LOGICA DEL NEGOCIO DEBE ESTAR CENTRALIZADA, Y LA MISMA ESTÁ EN SIGNALS
    # def save_model(self, request, obj, form, change):
    #     # Si el estado cambió a 'pagado' en esta edición
    #     if 'estado' in form.changed_data and obj.estado == 'pagado':
    #         for item in obj.items.all():
    #             producto = item.producto
    #             producto.stock -= item.cantidad
    #             producto.save()
                
    #     super().save_model(request, obj, form, change)
    

admin.site.register(Categoria)
