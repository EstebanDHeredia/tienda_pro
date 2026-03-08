from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto, DetallePedido, Pedido

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    inlines = [ImagenProductoInline]
    list_display = ['nombre', 'precio', 'stock', 'categoria']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['categoria']

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [DetallePedidoInline]
    list_display = ['id', 'total', 'fecha']
    search_fields = ['id', 'total']
    list_filter = ['fecha']
    


admin.site.register(Categoria)
