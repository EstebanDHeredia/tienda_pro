"""
Context Processors de la aplicación catalogo.

Los context processors permiten agregar variables al contexto
de todas las plantillas automáticamente.

Para activar un context processor, debe estar registrado en:
    settings.py -> TEMPLATES -> 'context_processors'
"""

from .carrito import Carrito


def carrito_global(request):
    """
    Context processor que agrega el carrito a todas las plantillas.
    
    Este context processor asegura que el objeto 'carrito' esté
    disponible en TODAS las plantillas del proyecto sin necesidad
    de pasarlo manualmente en cada vista.
    
    Funcionamiento:
        1. Se ejecuta en cada request
        2. Crea una instancia de Carrito con la sesión del usuario
        3. Retorna un diccionario con 'carrito'
        4. Django fusiona este dict con el contexto de cada plantilla
    
    Uso en plantillas:
        {{ carrito.total_pagar }}       - Total sin descuento
        {{ carrito.total_items }}      - Cantidad de productos
        {{ carrito.cupon }}            - Cupón aplicado (si existe)
        {{ carrito.descuento_total }} - Monto del descuento
        {{ carrito.total_con_descuento }} - Total con descuento
    
    Args:
        request: El objeto HttpRequest de Django
        
    Returns:
        Dict con la clave 'carrito' conteniendo la instancia de Carrito
    """
    return {'carrito': Carrito(request)}
