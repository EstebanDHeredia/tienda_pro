from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Pedido, DetallePedido
from django.db.models import F
from decimal import Decimal


# Señal 1: Restar Stock al crear el detalle
@receiver(post_save, sender=DetallePedido)
def restar_stock_al_crear(sender, instance, created, **kwargs):
    # Cuando se cread un Detalle de pedido se resta el stock del producto
    # Esto es importante porque si despues modifico por ej la direccion del cliente en el pedido 
    # esta señal se va a volver a ejecutar y no quiero que reste nuevamente la cantidad al stock del producto
    # Esto solo debe suceder cuando se crea el pedido
    if created: 
        print(f"DEBUG: Estoy creando el detalle {instance.id}")
        producto = instance.producto
        producto.stock = F('stock') - instance.cantidad # el motor de la BD hace el calculo de la resta del stock y lo guarda en la BD. Esto me asegura evitar el problema de la Carrera de Datos (cuando 2 usuarios están accediendo al stock del producto al mismo tiempo)
        producto.save()

# Señal 2: devolver el stock si se cancela un pedido
@receiver(pre_save, sender=Pedido)
def devolver_stock_al_cancelar(sender, instance, **kwargs):
    # Si un pedido cambia su estado a cancelado, devuelvo el stock de todos los productos que haya en ese pedido
    
    if instance.id: # se ejecuta solo si el pedido ya existe(es una edicion)
        try:
            # busco el pedido como está actualmente en la BD, antes de que cambie, para saber en que estado estaba
            # previo al cambio. Esto sirve por ejemplo para saber si el pedido ya estaba cancelado anteriormente y ahora solo
            # estoy modificando por ejemplo el tel del cliente, en este caso como el pedido ya estaba cancelado, no debo volver a sumar
            # el stock al producto
            
            pedido_previo = Pedido.objects.get(id=instance.id)

            # buscamos el cambio exacto: de cualquier estado a 'cancelado'
            if pedido_previo.estado != 'cancelado' and instance.estado == 'cancelado':
                print(f"Estoy cancelando el pedido: de {pedido_previo.estado} a {instance.estado}")
                # Busco todos los detallePedido de ese pedido (aca uso el related_name del modelo DetallePedido : pedido = models.ForeignKey(Pedido, related_name='items'.....
                productos_pedido = instance.items.all()
                for item in productos_pedido:
                    producto = item.producto
                    producto.stock = F('stock') + item.cantidad
                    producto.save()
            
            # Si el pedido estaba cancelado y lo vuelven a activar, resto el stock
            elif pedido_previo.estado == 'cancelado' and instance.estado != 'cancelado': 
                print(f"Estoy activando el pedido: de {pedido_previo.estado} a {instance.estado}")
                productos_pedido = instance.items.all()
                for item in productos_pedido:
                    producto = item.producto
                    producto.stock = F('stock') - item.cantidad
                    producto.save()
                    
        except Pedido.DoesNotExist:
            pass

# Señal 3: devuelvo el stock si se borra el pedido o el detallepedido:
@receiver(post_delete, sender=DetallePedido)
def devolver_stock_al_borrar(sender, instance, **kwargs):
    # Si se borra manualmente un pedido o detallePedido, regreso el stock al producto
    
    # Primero veo si el pedido no estaba cancelado, ya que si es asi no debo devolver el stock, ya se que hace en la señal anterior
    if instance.pedido.estado !='cancelado':
        print("Estoy borrando el detalle")
        producto = instance.producto
        producto.stock = F('stock') + instance.cantidad
        producto.save()

@receiver(pre_save, sender=Pedido)
def aplicar_descuento_cupon(sender, instance, **kwargs):
    #Tengo que verificar que el descuento ya no esté aplicado,
    #Porque esta señal se ejecuta nuevamente cuando se cambia el estado del cupón 
    #Entonces si el pedido tiene un cupón guardado es que ya se le hizo el descuento y no corresponde hacerlo nuevamente
    if instance.id:
        pedido_previo = Pedido.objects.get(id=instance.id)

        if pedido_previo.cupon: #Ya tiene un cupon guardado, no debo hacer el calculo de cupon de nuevo
            pass
        else:
                
            # Solo calculo el descuento si hay un cupon asignado
            if instance.cupon and instance.cupon.es_valido:
                # 1. Calculo el monto a descontar
                porcentaje = Decimal(instance.cupon.descuento_porcentaje)
                descuento = instance.total * (porcentaje / Decimal(100))
                
                # 2. Guardo para el registro cuánto descontó
                instance.descuento_aplicado = descuento
                
                # 3. Restamos el descuento al total del pedido
                instance.total = instance.total - descuento
            else:
                # No hay cupon, el descuento es 0
                instance.descuento_aplicado = 0

@receiver(pre_save, sender=Pedido)
def aumentar_uso_cupon(sender, instance, **kwargg):
    if instance.id:
        pedido_previo = Pedido.objects.get(id=instance.id)

        # Si el pedido pasa de cualquier estado a 'pagado'
        if pedido_previo.estado != 'pagado' and instance.estado == 'pagado':
            if instance.cupon:
                # uso F() para evitar colisiones
                instance.cupon.usos_actuales = F('usos_actuales') + 1
                instance.cupon.save()
                