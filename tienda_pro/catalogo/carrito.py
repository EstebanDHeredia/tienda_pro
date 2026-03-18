from decimal import Decimal
from .models import Producto, Cupon

class Carrito:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        carrito = self.session.get('carrito')
        
        if not carrito:
            carrito = self.session['carrito'] = {}
        self.carrito = carrito
        
        self.cupon_id = self.session.get('cupon_id', None)
    
    def aplicar_cupon(self, cupon_id):
        self.session['cupon_id'] = cupon_id
        self.cupon_id = cupon_id
        self.session.modified = True
    
    def agregar(self, producto, cantidad=1):
        id_prod = str(producto.id)

        # Obtenemos la cantidad de ese producto en el carrito, si es que hay
        cantidad_en_carrito = self.carrito[id_prod]['cantidad'] if id_prod in self.carrito else 0
        
        # Verificamos si hay stock suficiente para lo que queremos agregar
        if producto.stock >= (cantidad_en_carrito + cantidad):          
            if id_prod not in self.carrito:
                self.carrito[id_prod] = {
                    'producto_id': producto.id,
                    'nombre': producto.nombre,
                    'precio': str(producto.precio),
                    'cantidad': int(cantidad),
                    'subtotal': str(int(cantidad) * producto.precio),
                    'imagen': producto.imagen.url if producto.imagen else ""
                }
            else:
                self.carrito[id_prod]['cantidad'] += int(cantidad)
                self.carrito[id_prod]['subtotal'] = str(self.carrito[id_prod]['cantidad'] * Decimal(self.carrito[id_prod]['precio']))
        
            self.guardar_sesion()
            return True
        else:
            return False # No hay stock sufuciente
    

    def guardar_sesion(self):
        self.session['carrito'] = self.carrito
        self.session.modified = True

    def eliminar(self, producto):
        id_prod = str(producto.id)
        if id_prod in self.carrito:
            del self.carrito[id_prod]
            self.guardar_sesion()

    def restar(self, producto):
        id_prod = str(producto.id)
        if id_prod in self.carrito:
            self.carrito[id_prod]['cantidad'] -= 1
            self.carrito[id_prod]['subtotal'] = str(int(self.carrito[id_prod]['cantidad'] * Decimal(self.carrito[id_prod]['precio'])))
            if self.carrito[id_prod]['cantidad'] < 1:
                self.eliminar(producto)
            else:
                self.guardar_sesion()

    def limpiar(self):
        self.session['carrito'] = {}
        self.session.modified = True

    @property
    def total_pagar(self):
        return sum(Decimal(item['precio']) * item['cantidad'] for item in self.carrito.values())

    @property
    def total_items(self):
        return sum(item['cantidad'] for item in self.carrito.values())
    
    @property
    def productos_detalle(self):
        # Solo devuelve los datos que ya están en la sesión
        # No guarda objetos Django en la sesión
        productos_ids = self.carrito.keys()
        productos_db = Producto.objects.filter(id__in=productos_ids)
        productos_dict = {str(p.id): p for p in productos_db}

        lista_detallada = []
        for id_prod, datos in self.carrito.items():
            # .copy() crea una copia para NO afectar la sesión
            item = datos.copy()
            # Agregamos el objeto solo para uso en memoria (no se guarda en sesión)
            item['producto'] = productos_dict.get(id_prod)
            lista_detallada.append(item)

        return lista_detallada
    
    @property
    def cupon(self):
        if self.cupon_id:
            try:
                return Cupon.objects.get(id=self.cupon_id)
            except Cupon.DoesNotExist:
                return None
        return None
    
    def eliminar_cupon(self):
        if 'cupon_id' in self.session:
            del self.session['cupon_id']
            self.cupon_id = None
            self.session.modified = True
    
    @property
    def descuento_total(self):
        if self.cupon and self.cupon.es_valido:
            return self.total_pagar * (Decimal(self.cupon.descuento_porcentaje) / Decimal(100))
        return Decimal('0')
        
    @property
    def total_con_descuento(self):
        # El total que el cliente ve en el carrito
        return self.total_pagar - self.descuento_total
    
    