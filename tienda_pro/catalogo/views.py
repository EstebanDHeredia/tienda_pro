from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Producto
from django.db.models import Q

# Create your views here.
class ListaProductosView(ListView):
    model = Producto
    template_name = 'catalogo/lista.html'
    context_object_name = 'mis_productos'
    
    def get_queryset(self):
        queryset = Producto.objects.filter(stock__gt=0)
        
        termino = self.request.GET.get('buscar')

        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino) | Q(descripcion__icontains=termino))
        return queryset
        

class DetalleProductoView(DetailView):
    model = Producto
    template_name = "catalogo/detalle.html"
    context_object_name = 'producto'
    