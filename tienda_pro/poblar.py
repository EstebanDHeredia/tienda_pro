import os
import django
import random

# 1. Configurar el entorno de Django para que el script pueda usar los modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda_pro.settings')
django.setup()

from catalogo.models import Producto, Categoria
from faker import Faker

fake = Faker('es_ES') # 'es_ES' genera datos en español

def crear_datos(n=20):
    # Creamos algunas categorías fijas primero
    nombres_categorias = ['Electrónica', 'Hogar', 'Deportes', 'Juguetes']
    for nombre in nombres_categorias:
        Categoria.objects.get_or_create(nombre=nombre)

    categorias = Categoria.objects.all()

    for _ in range(n):
        # Generamos datos aleatorios con Faker
        nombre_fake = fake.catch_phrase() # Nombres que suenan a productos/marcas
        desc_fake = fake.paragraph(nb_sentences=3)
        precio_fake = random.uniform(5.0, 999.0)
        stock_fake = random.randint(0, 50)
        categoria_fake = random.choice(categorias)

        # Guardamos en la base de datos
        Producto.objects.create(
            nombre=nombre_fake,
            descripcion=desc_fake,
            precio=round(precio_fake, 2),
            stock=stock_fake,
            categoria=categoria_fake
        )
    
    print(f"✅ ¡Se han creado {n} productos exitosamente!")

if __name__ == '__main__':
    crear_datos(50) # Cambia este número por la cantidad que quieras