from django.urls import path
from .views import ListaProductosView, DetalleProductoView, agregar_producto, ver_carrito, eliminar_producto, limpiar_carrito, finalizar_pedido, sumar_item, restar_item

urlpatterns = [
    path('', ListaProductosView.as_view(), name='lista'),
    path('<int:pk>/', DetalleProductoView.as_view(), name='detalle'),
    path('agregar/<int:producto_id>/', agregar_producto, name='agregar'),
    path('carrito/', ver_carrito, name="ver_carrito"),
    path('eliminar/<int:producto_id>/', eliminar_producto, name='eliminar'),
    path('limpiar/', limpiar_carrito, name='limpiar'),
    path('finalizar-pedido/', finalizar_pedido, name="finalizar_pedido"),
    path('sumar-item/<int:producto_id>', sumar_item, name='sumar_item'),
    path('restar-item/<producto_id>', restar_item, name='restar_item'),
]

