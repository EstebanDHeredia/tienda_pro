from django.urls import path
from .views import ListaProductosView, DetalleProductoView

urlpatterns = [
    path('', ListaProductosView.as_view(), name='lista'),
    path('<int:pk>/', DetalleProductoView.as_view(), name='detalle'),

]

