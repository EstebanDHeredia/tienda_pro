from decimal import Decimal
from .models import Producto

class Carrito:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        carrito = self.session.get('carrito')
        if not carrito:
            carrito = self.session['carrito'] = {}
        self.carrito = carrito

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
        # Trae los objetos Producto de la BD
        # para tener acceso al stock real en el HTML
        # y poder saber e impedir que ponga en el carrito
        # mas productos de los que hay en stock
               
        productos_ids = self.carrito.keys()
        # Buscamos los objetos reales en la BD
        productos_db = Producto.objects.filter(id__in=productos_ids)
        # Creo un diccionario para buscar los productos por Id rápido
        productos_dict = {str(p.id): p for p in productos_db}

        lista_detallada = []
        for id_prod, datos in self.carrito.items():
            #  .copy() es la clave: creamos una copia para NO afectar a self.session
            item = datos.copy() # Son los datos del producto que están en el carrito de la sesión (accessible en el template a través de item.cantidad, item.precio, item.imagen, etc)
            item['producto'] = productos_dict.get(id_prod) # Son los datos del producto que están en la BD (accesible en el template a través de item.producto.stock o item.producto.precio, item.producto.imagen, etc)
            lista_detallada.append(item)

        return lista_detallada
    
    