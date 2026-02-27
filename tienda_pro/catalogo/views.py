from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Producto
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
        return context
        

class DetalleProductoView(DetailView):
    model = Producto
    template_name = "catalogo/detalle.html"
    context_object_name = 'producto'
    