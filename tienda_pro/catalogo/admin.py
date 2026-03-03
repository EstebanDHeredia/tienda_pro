from django.contrib import admin
from .models import Categoria, Producto, ImagenProducto

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    inlines = [ImagenProductoInline]
    list_display = ['nombre', 'precio', 'stock', 'categoria']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['categoria']

admin.site.register(Categoria)
