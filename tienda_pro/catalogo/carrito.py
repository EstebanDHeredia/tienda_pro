"""
Clase Carrito - Gestión del carrito de compras.

Esta clase maneja toda la lógica del carrito de compras, incluyendo:
- Agregar, eliminar, modificar cantidades de productos
- Cálculo de totales y descuentos
- Gestión de cupones de descuento
- Persistencia mediante sesiones de Django

El carrito se almacena en la sesión del usuario (request.session),
lo que permite que persista entre diferentes páginas y visitas.

Estructura del carrito en sesión:
    session['carrito'] = {
        'producto_id': {
            'producto_id': 1,
            'nombre': 'Producto X',
            'precio': '1000.00',  # Como string para JSON
            'cantidad': 2,
            'subtotal': '2000.00',
            'imagen': '/media/productos/img.jpg'
        },
        ...
    }
"""

from decimal import Decimal
from .models import Producto, Cupon


class Carrito:
    """
    Clase para gestionar el carrito de compras.
    
    Attributes:
        request: Objeto HttpRequest de Django
        session: Referencia a request.session para persistencia
        carrito: Dict con los productos en el carrito
        cupon_id: ID del cupón aplicado (si existe)
    """
    
    def __init__(self, request):
        """
        Inicializa el carrito con la sesión del usuario.
        
        Si no existe un carrito en la sesión, crea uno vacío.
        Recupera también el ID del cupón aplicado (si existe).
        
        Args:
            request: HttpRequest de Django
        """
        self.request = request
        self.session = request.session
        
        # Obtener carrito de la sesión o crear uno nuevo
        carrito = self.session.get('carrito')
        if not carrito:
            carrito = self.session['carrito'] = {}
        self.carrito = carrito
        
        # Recuperar ID del cupón de la sesión
        self.cupon_id = self.session.get('cupon_id', None)
    
    
    # =========================================================================
    # Métodos de persistencia
    # =========================================================================
    
    def guardar_sesion(self):
        """
        Guarda el carrito en la sesión.
        
        Debe llamarse después de cualquier modificación al carrito
        para asegurar que los cambios persistan.
        """
        self.session['carrito'] = self.carrito
        self.session.modified = True
    
    
    # =========================================================================
    # Métodos de gestión de productos
    # =========================================================================
    
    def agregar(self, producto, cantidad=1):
        """
        Agrega un producto al carrito o aumenta su cantidad.
        
        Verifica que haya stock suficiente antes de agregar.
        
        Args:
            producto: Instancia del modelo Producto
            cantidad: Cantidad a agregar (default: 1)
            
        Returns:
            True si se agregó correctamente, False si no hay stock
            
        Estructura guardada:
            {
                'producto_id': ID del producto,
                'nombre': Nombre del producto,
                'precio': Precio como string,
                'cantidad': Cantidad,
                'subtotal': Precio * cantidad,
                'imagen': URL de la imagen
            }
        """
        id_prod = str(producto.id)
        
        # Cantidad actual en carrito
        cantidad_en_carrito = self.carrito[id_prod]['cantidad'] if id_prod in self.carrito else 0
        
        # Verificar stock disponible
        if producto.stock >= (cantidad_en_carrito + cantidad):
            if id_prod not in self.carrito:
                # Nuevo producto
                self.carrito[id_prod] = {
                    'producto_id': producto.id,
                    'nombre': producto.nombre,
                    'precio': str(producto.precio),
                    'cantidad': int(cantidad),
                    'subtotal': str(int(cantidad) * producto.precio),
                    'imagen': producto.imagen.url if producto.imagen else ""
                }
            else:
                # Aumentar cantidad existente
                self.carrito[id_prod]['cantidad'] += int(cantidad)
                self.carrito[id_prod]['subtotal'] = str(
                    self.carrito[id_prod]['cantidad'] * Decimal(self.carrito[id_prod]['precio'])
                )
            
            self.guardar_sesion()
            return True
        else:
            return False  # No hay stock suficiente
    
    
    def eliminar(self, producto):
        """
        Elimina un producto completamente del carrito.
        
        Args:
            producto: Instancia del modelo Producto
        """
        id_prod = str(producto.id)
        if id_prod in self.carrito:
            del self.carrito[id_prod]
            self.guardar_sesion()
    
    
    def restar(self, producto):
        """
        Reduce la cantidad de un producto en 1.
        
        Si la cantidad llega a 0, elimina el producto del carrito.
        
        Args:
            producto: Instancia del modelo Producto
        """
        id_prod = str(producto.id)
        if id_prod in self.carrito:
            self.carrito[id_prod]['cantidad'] -= 1
            self.carrito[id_prod]['subtotal'] = str(
                int(self.carrito[id_prod]['cantidad'] * Decimal(self.carrito[id_prod]['precio']))
            )
            
            if self.carrito[id_prod]['cantidad'] < 1:
                self.eliminar(producto)
            else:
                self.guardar_sesion()
    
    
    def limpiar(self):
        """
        Vacía completamente el carrito.
        
        Elimina todos los productos del carrito.
        """
        self.session['carrito'] = {}
        self.session.modified = True
    
    
    # =========================================================================
    # Propiedades de cálculo
    # =========================================================================
    
    @property
    def total_pagar(self):
        """
        Calcula el total sin descuentos.
        
        Suma: precio * cantidad de todos los productos.
        
        Returns:
            Decimal con el total sin descuento
        """
        return sum(
            Decimal(item['precio']) * item['cantidad'] 
            for item in self.carrito.values()
        )
    
    
    @property
    def total_items(self):
        """
        Cuenta el total de items en el carrito.
        
        Returns:
            Int con la suma de todas las cantidades
        """
        return sum(item['cantidad'] for item in self.carrito.values())
    
    
    @property
    def productos_detalle(self):
        """
        Retorna lista detallada de productos con objetos Django.
        
        Combina los datos de la sesión con los objetos Producto
        de la base de datos para tener acceso completo a los datos.
        
        No guarda objetos Django en la sesión (solo datos serializables).
        
        Returns:
            List de dicts con datos del producto + objeto Producto
        """
        productos_ids = self.carrito.keys()
        productos_db = Producto.objects.filter(id__in=productos_ids)
        productos_dict = {str(p.id): p for p in productos_db}
        
        lista_detallada = []
        for id_prod, datos in self.carrito.items():
            item = datos.copy()
            item['producto'] = productos_dict.get(id_prod)
            lista_detallada.append(item)
        
        return lista_detallada
    
    
    # =========================================================================
    # Métodos de gestión de cupones
    # =========================================================================
    
    def aplicar_cupon(self, cupon_id):
        """
        Aplica un cupón de descuento al carrito.
        
        Guarda el ID del cupón en la sesión para que persista
        entre páginas.
        
        Args:
            cupon_id: ID del cupón a aplicar
        """
        self.session['cupon_id'] = cupon_id
        self.cupon_id = cupon_id
        self.session.modified = True
    
    
    def eliminar_cupon(self):
        """
        Elimina el cupón aplicado del carrito.
        
        Limpia tanto la sesión como el atributo de la instancia.
        """
        if 'cupon_id' in self.session:
            del self.session['cupon_id']
        self.cupon_id = None
        self.session.modified = True
    
    
    # =========================================================================
    # Propiedades de cupones y descuentos
    # =========================================================================
    
    @property
    def cupon(self):
        """
        Obtiene el cupón aplicado desde la base de datos.
        
        Returns:
            Objeto Cupon si existe y es válido, None en caso contrario
        """
        if self.cupon_id:
            try:
                return Cupon.objects.get(id=self.cupon_id)
            except Cupon.DoesNotExist:
                return None
        return None
    
    
    @property
    def descuento_total(self):
        """
        Calcula el monto del descuento.
        
        Solo aplica si hay un cupón válido.
        
        Returns:
            Decimal con el monto del descuento
        """
        if self.cupon and self.cupon.es_valido:
            return self.total_pagar * (
                Decimal(self.cupon.descuento_porcentaje) / Decimal(100)
            )
        return Decimal('0')
    
    
    @property
    def total_con_descuento(self):
        """
        Calcula el total después de aplicar el descuento.
        
        Returns:
            Decimal con el total menos el descuento
        """
        return self.total_pagar - self.descuento_total
