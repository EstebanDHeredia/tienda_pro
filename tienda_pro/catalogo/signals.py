"""
Señales Django para la aplicación catalogo.

Las señales permiten ejecutar código automáticamente cuando ocurre
un evento en los modelos (crear, guardar, eliminar).

Señales definidas:
1. restar_stock_al_crear: Descuenta stock al crear DetallePedido
2. devolver_stock_al_cancelar: Devuelve stock al cancelar/reactivar pedido
3. devolver_stock_al_borrar: Devuelve stock al eliminar DetallePedido
4. aplicar_descuento_cupon: Aplica descuento del cupón al pedido
5. aumentar_uso_cupon: Incrementa contador de usos del cupón
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Pedido, DetallePedido
from django.db.models import F
from decimal import Decimal


# =============================================================================
# SEÑALES DE GESTIÓN DE STOCK
# =============================================================================

@receiver(post_save, sender=DetallePedido)
def restar_stock_al_crear(sender, instance, created, **kwargs):
    """
    Descuenta el stock del producto cuando se crea un DetallePedido.
    
    Esta señal se ejecuta DESPUÉS de guardar un DetallePedido.
    Solo actúa cuando el detalle es nuevo (created=True).
    
    Uso de F() expression:
        Se usa F('stock') para que la Base de Datos calcule el nuevo valor,
        evitando problemas de 'Race Condition' (condiciones de carrera)
        cuando dos usuarios acceden simultáneamente al mismo stock.
    
    Args:
        sender: El modelo que envió la señal (DetallePedido)
        instance: La instancia de DetallePedido que fue guardada
        created: Booleano - True si es un objeto nuevo
        **kwargs: Argumentos adicionales de Django
    
    Ejemplo:
        Si producto.stock = 10 y cantidad = 3,
        el nuevo stock será 10 - 3 = 7
    """
    if created:
        producto = instance.producto
        producto.stock = F('stock') - instance.cantidad
        producto.save()


@receiver(pre_save, sender=Pedido)
def devolver_stock_al_cancelar(sender, instance, **kwargs):
    """
    Gestiona el stock cuando cambia el estado de un pedido.
    
    Esta señal se ejecuta ANTES de guardar un Pedido.
    
    Comportamientos:
    1. Al CANCELAR (cualquier estado → cancelado):
       - Devuelve el stock a todos los productos del pedido
    
    2. Al REACTIVAR (cancelado → otro estado):
       - Descuenta nuevamente el stock de los productos
    
    El pedido debe existir previamente (instance.id existe).
    Si es un pedido nuevo, no hace nada.
    
    Args:
        sender: El modelo que envió la señal (Pedido)
        instance: La instancia de Pedido a guardar
        **kwargs: Argumentos adicionales de Django
    
    Validación:
        Solo actúa si el pedido ya existe en la BD (para comparar estados).
    """
    if instance.id:
        try:
            # Obtener estado actual del pedido ANTES del cambio
            pedido_previo = Pedido.objects.get(id=instance.id)
            
            # Caso 1: Cancelar pedido
            if pedido_previo.estado != 'cancelado' and instance.estado == 'cancelado':
                productos_pedido = instance.items.all()
                for item in productos_pedido:
                    producto = item.producto
                    producto.stock = F('stock') + item.cantidad
                    producto.save()
            
            # Caso 2: Reactivar pedido cancelado
            elif pedido_previo.estado == 'cancelado' and instance.estado != 'cancelado':
                productos_pedido = instance.items.all()
                for item in productos_pedido:
                    producto = item.producto
                    producto.stock = F('stock') - item.cantidad
                    producto.save()
                    
        except Pedido.DoesNotExist:
            pass


@receiver(post_delete, sender=DetallePedido)
def devolver_stock_al_borrar(sender, instance, **kwargs):
    """
    Devuelve el stock al eliminar un DetallePedido.
    
    Esta señal se ejecuta DESPUÉS de eliminar un DetallePedido.
    
    Condición:
        Solo devuelve stock si el pedido NO estaba cancelado,
        ya que si estaba cancelado, el stock ya fue devuelto
        por la señal 'devolver_stock_al_cancelar'.
    
    Args:
        sender: El modelo que envió la señal (DetallePedido)
        instance: La instancia de DetallePedido que fue eliminada
        **kwargs: Argumentos adicionales de Django
    
    Ejemplo:
        Si producto.stock = 7 y cantidad = 3,
        el nuevo stock será 7 + 3 = 10
    """
    # Solo devolver stock si el pedido no estaba cancelado
    if instance.pedido.estado != 'cancelado':
        producto = instance.producto
        producto.stock = F('stock') + instance.cantidad
        producto.save()


# =============================================================================
# SEÑALES DE GESTIÓN DE CUPONES
# =============================================================================

@receiver(pre_save, sender=Pedido)
def aplicar_descuento_cupon(sender, instance, **kwargs):
    """
    Aplica el descuento del cupón al guardar un Pedido.
    
    Esta señal se ejecuta ANTES de guardar un Pedido.
    
    Comportamiento:
        Solo actúa si el pedido tiene un cupón asignado Y
        el pedido NO tenía cupón previamente (para evitar
        recalcular el descuento si ya fue aplicado).
    
    Cálculo del descuento:
        descuento = total * (porcentaje / 100)
    
    Campos modificados:
        - descuento_aplicado: Monto del descuento
        - total: Total original - descuento
    
    Args:
        sender: El modelo que envió la señal (Pedido)
        instance: La instancia de Pedido a guardar
        **kwargs: Argumentos adicionales de Django
    """
    if instance.id:
        try:
            pedido_previo = Pedido.objects.get(id=instance.id)
            
            # Si el pedido anterior ya tenía cupón, no recalcular
            if pedido_previo.cupon:
                pass
            else:
                # Solo aplicar si hay cupón válido
                if instance.cupon and instance.cupon.es_valido:
                    porcentaje = Decimal(instance.cupon.descuento_porcentaje)
                    descuento = instance.total * (porcentaje / Decimal(100))
                    
                    # Guardar monto del descuento
                    instance.descuento_aplicado = descuento
                    
                    # Restar descuento del total
                    instance.total = instance.total - descuento
                else:
                    instance.descuento_aplicado = Decimal('0')
                    
        except Pedido.DoesNotExist:
            pass


@receiver(pre_save, sender=Pedido)
def aumentar_uso_cupon(sender, instance, **kwargs):
    """
    Incrementa el contador de usos del cupón al pagar.
    
    Esta señal se ejecuta ANTES de guardar un Pedido.
    
    Comportamiento:
        Cuando un pedido pasa a estado 'pagado' y tiene un cupón,
        incrementa el contador de usos de ese cupón.
    
    Uso de F() expression:
        Se usa F('usos_actuales') para que la Base de Datos
        incremente atomicamente, evitando problemas de concurrencia.
    
    Args:
        sender: El modelo que envió la señal (Pedido)
        instance: La instancia de Pedido a guardar
        **kwargs: Argumentos adicionales de Django
    """
    if instance.id:
        try:
            pedido_previo = Pedido.objects.get(id=instance.id)
            
            # Solo incrementar si el pedido pasa a 'pagado'
            if pedido_previo.estado != 'pagado' and instance.estado == 'pagado':
                if instance.cupon:
                    instance.cupon.usos_actuales = F('usos_actuales') + 1
                    instance.cupon.save()
                    
        except Pedido.DoesNotExist:
            pass
