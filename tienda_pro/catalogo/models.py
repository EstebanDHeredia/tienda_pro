from django.db import models

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')
    
    class Meta:
        ordering = ['id']
        
class Pedido(models.Model):
    # Opciones para el estado del pedido
    ESTADOS = (
        ('pendiente', 'Pendiente de Pago'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    )
    
    # Datos del cliente
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)

    # Datos del pedido
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre} {self.apellido}"

class DetallePedido(models.Model):
    # Relacionamos este detalle con el Pedido de arriba
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    
    # Relacionamos este detalle con el Producto que ya tengo
    producto = models.ForeignKey(Producto, related_name='detalle_pedido', on_delete=models.CASCADE)

    # Guardamos el precio por si después cambia, ya que debo respetar el precio original
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.id} - {self.producto.nombre}"

    def obtener_costo(self):
        return (self.precio or 0) * (self.cantidad or 0)
    