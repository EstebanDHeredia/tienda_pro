from django.urls import path
from .views import ListaProductosView, DetalleProductoView, agregar_producto, ver_carrito,eliminar_producto, limpiar_carrito,  sumar_item, restar_item, pedido_crear,pedido_confirmado, dashboard_ventas, lista_pedidos, cambiar_estado_pedido, aplicar_cupon, eliminar_cupon

urlpatterns = [
    path('', ListaProductosView.as_view(), name='lista'),
    path('<int:pk>/', DetalleProductoView.as_view(), name='detalle'),
    path('agregar/<int:producto_id>/', agregar_producto, name='agregar'),
    path('carrito/', ver_carrito, name="ver_carrito"),
    path('eliminar/<int:producto_id>/', eliminar_producto, name='eliminar'),
    path('limpiar/', limpiar_carrito, name='limpiar'),
    # path('finalizar-pedido/', finalizar_pedido, name="finalizar_pedido"),
    path('sumar-item/<int:producto_id>', sumar_item, name='sumar_item'),
    path('restar-item/<int:producto_id>', restar_item, name='restar_item'),
    path('checkout/', pedido_crear, name='checkout'),
    path('confirmado/', pedido_confirmado, name='pedido_confirmado'),
    path('dashboard/', dashboard_ventas, name='dashboard'),
    path('pedidos/', lista_pedidos, name='lista_pedidos'),
    path('pedidos/estado/<int:pedido_id>/<str:nuevo_estado>', cambiar_estado_pedido, name='cambiar_estado'),
    path('cupon/aplicar/', aplicar_cupon, name='aplicar_cupon'),
    path('cupon/eliminar/', eliminar_cupon, name='eliminar_cupon'),
    
]

