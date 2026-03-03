from .carrito import Carrito

def carrito_global(request):
    return {'carrito': Carrito(request)}