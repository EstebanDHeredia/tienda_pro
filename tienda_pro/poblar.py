import os
import sys
import django
import random
import urllib.request

# Setup Django desde la carpeta correcta
script_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = tienda_pro/tienda_pro (donde está settings.py)
project_root = script_dir

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda_pro.settings')
sys.path.insert(0, project_root)
django.setup()

from catalogo.models import Producto, Categoria, ImagenProducto

# Rutas - MEDIA_ROOT debe coincidir con settings.py (BASE_DIR/media)
MEDIA_ROOT = os.path.join(project_root, 'media', 'productos')
os.makedirs(MEDIA_ROOT, exist_ok=True)

def descargar_imagen(palabras_clave, nombre_archivo):
    try:
        ruta = os.path.join(MEDIA_ROOT, nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
        
        # Convertir a keywords en inglés
        keywords_en = {
            'electrónica': 'electronics', 'hogar': 'home', 'deportes': 'sports',
            'juguetes': 'toys', 'ropa': 'clothing', 'libros': 'books', 'música': 'music',
            'smartphone': 'smartphone', 'laptop': 'laptop', 'auriculares': 'headphones',
            'smartwatch': 'smartwatch', 'tablet': 'tablet', 'cámara': 'camera',
            'consola': 'game console', 'altavoz': 'speaker', 'monitor': 'monitor',
            'teclado': 'keyboard', 'sofá': 'sofa', 'mesa': 'table', 'lámpara': 'lamp',
            'toallas': 'towels', 'colchón': 'mattress', 'silla': 'chair', 'cortinas': 'curtains',
            'espejo': 'mirror', 'organizador': 'organizer', 'maceta': 'pot',
            'pelota': 'ball', 'fútbol': 'football', 'tenis': 'tennis', 'yoga': 'yoga',
            'bandas': 'resistance bands', 'mancuernas': 'dumbbell', 'balón': 'basketball',
            'zapatillas': 'sneakers', 'guantes': 'gloves', 'cuerda': 'jump rope',
            'lego': 'lego', 'muñeca': 'doll', 'puzzle': 'puzzle', 'peluche': 'stuffed animal',
            'pintura': 'paint', 'drone': 'drone', 'campera': 'jacket', 'jeans': 'jeans',
            'vestido': 'dress', 'gorra': 'cap', 'bufanda': 'scarf', 'camisa': 'shirt',
            'shorts': 'shorts', 'medias': 'socks'
        }
        
        # Traducir palabras clave a inglés
        palabras = palabras_clave.lower().replace(',', ' ').split()
        keywords = [keywords_en.get(p, p) for p in palabras]
        keywords_str = ','.join(keywords)
        
        # Intentar con loremflickr (más confiable)
        url = f'https://loremflickr.com/400/400/{keywords_str}?random={random.randint(1,9999)}'
        
        import socket
        socket.setdefaulttimeout(10)
        
        urllib.request.urlretrieve(url, ruta)
        print(f"    📥 {keywords_str} -> {nombre_archivo}")
        return f'productos/{nombre_archivo}'
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:50]}")
        return None

def poblar_50():
    print("🧹 Limpiando imágenes anteriores...")
    # Eliminar todas las imágenes de productos
    for f in os.listdir(MEDIA_ROOT):
        if f.startswith('prod_'):
            try:
                os.remove(os.path.join(MEDIA_ROOT, f))
            except:
                pass
    print("✅ Imágenes anteriores eliminadas\n")
    
    print("📥 Descargando imágenes relacionadas con cada producto...")
    
    # Limpiar
    Producto.objects.all().delete()
    print("🗑️ Productos anteriores eliminados\n")

    # Categorías
    categorias_nombres = ['Electrónica', 'Hogar', 'Deportes', 'Juguetes', 'Ropa', 'Libros', 'Música']
    for nombre in categorias_nombres:
        Categoria.objects.get_or_create(nombre=nombre)

    # 50 productos
    productos_data = [
        ('Smartphone Galaxy Ultra', 'Teléfono móvil de última generación con pantalla AMOLED 6.8"', 250000, 15, 'Electrónica'),
        ('Laptop Pro 15 pulgadas', 'Computadora portátil con procesador i7 y 16GB RAM', 320000, 10, 'Electrónica'),
        ('Auriculares Inalámbricos', 'Auriculares Bluetooth con cancelación de ruido activa', 45000, 30, 'Electrónica'),
        ('Smartwatch Series 8', 'Reloj inteligente con monitor de frecuencia cardíaca', 65000, 20, 'Electrónica'),
        ('Tablet 10 pulgadas', 'Tablet android con pantalla Full HD', 89000, 12, 'Electrónica'),
        ('Cámara Digital 4K', 'Cámara profesional para fotografía y video', 150000, 8, 'Electrónica'),
        ('Consola Videojuegos', 'Consola de última generación con mando dual', 180000, 25, 'Electrónica'),
        ('Altavoz Bluetooth', 'Parlante resistente al agua con graves potentes', 28000, 40, 'Electrónica'),
        ('Monitor Curvo 27"', 'Monitor gaming con tasa de refresco 144Hz', 95000, 15, 'Electrónica'),
        ('Teclado Mecánico RGB', 'Teclado gamer con switches azules retroiluminado', 35000, 22, 'Electrónica'),
        
        ('Sofá Cama 3 Plazas', 'Sofá cama de tela lavable color gris moderno', 125000, 8, 'Hogar'),
        ('Mesa de Centro', 'Mesa de centro de madera MDF elegante', 45000, 15, 'Hogar'),
        ('Lámpara de Pie LED', 'Lámpara moderna regulable en altura', 22000, 25, 'Hogar'),
        ('Juego de Toallas 6 piezas', 'Toallas de algodón egipcio suaves', 18000, 35, 'Hogar'),
        ('Colchón Espuma 2 plazas', 'Colchón de espuma viscoelástica', 98000, 10, 'Hogar'),
        ('Silla de Escritorio', 'Silla ergonómica con soporte lumbar', 55000, 18, 'Hogar'),
        ('Cortinas Blackout', 'Cortinas oscurantes 2x1 metros', 15000, 40, 'Hogar'),
        ('Espejo Decorativo', 'Espejo ovalado con marco dorado', 28000, 20, 'Hogar'),
        ('Organizador de Ropa', 'Armario organizador extensible', 12000, 30, 'Hogar'),
        ('Maceta Cerámica Moderna', 'Maceta decorativa para interior', 5500, 50, 'Hogar'),
        
        ('Pelota de Fútbol Adidas', 'Balón profesional certificado FIFA', 8500, 45, 'Deportes'),
        ('Raqueta de Tenis Pro', 'Raqueta carbono profesional', 32000, 15, 'Deportes'),
        ('Esterilla de Yoga', 'Mat de yoga antideslizante 6mm', 7500, 60, 'Deportes'),
        ('Bandas Elásticas Set', 'Kit de 5 bandas resistencia media', 4500, 55, 'Deportes'),
        ('Mancuernas 10kg Par', 'Mancuernas vinyl ajustables', 12000, 25, 'Deportes'),
        ('Balón de Basketball', 'Balón oficial tamaño regulación', 6500, 30, 'Deportes'),
        ('Zapatillas Running', 'Zapatillas amortiguación Runner', 42000, 20, 'Deportes'),
        ('Guantes de Boxeo', 'Guantes boxeo cuero sintético', 15000, 18, 'Deportes'),
        ('Cuerda para Saltar', 'Cuerda velocidad profesional', 3500, 70, 'Deportes'),
        ('Pelota de Voley Playa', 'Voley playa resistente agua salada', 4800, 35, 'Deportes'),
        
        ('Lego City Completo', 'Kit construcción 500 piezas niños', 18500, 20, 'Juguetes'),
        ('Muñeca Barbie', 'Muñeca fashion con accesorios', 12000, 25, 'Juguetes'),
        ('Auto a Control Remoto', 'Coche RC velocidad media', 15000, 18, 'Juguetes'),
        ('Puzzle 1000 piezas', 'Puzzle paisaje montaña', 4500, 40, 'Juguetes'),
        ('Juego de Mesa Damas', 'Tablero damas clásico madera', 5500, 30, 'Juguetes'),
        ('Peluche Gigante 1m', 'Oso de peluche suave', 9500, 22, 'Juguetes'),
        ('Kit de Pintura', 'Acuarelas 24 colores profesional', 7800, 28, 'Juguetes'),
        ('Drone Mini Cámara', 'Dron amateur con cámara HD', 45000, 12, 'Juguetes'),
        ('Rompecabezas 3D', 'Puzzle esferas mundial', 8500, 15, 'Juguetes'),
        ('Juego de Construcción', 'Blocks ingeniería 200 piezas', 11000, 20, 'Juguetes'),
        
        ('Campera de Cuero', 'Campera cuero moto caballero', 85000, 10, 'Ropa'),
        ('Jeans Slim Fit', 'Pantalón denim stretch hombre', 22000, 35, 'Ropa'),
        ('Vestido Fiesta', 'Vestido elegante femenino larga', 32000, 18, 'Ropa'),
        ('Zapatillas Urbanas', 'Zapatillas canvas unisex', 18500, 40, 'Ropa'),
        ('Gorra Baseball', 'Gorra sport ajustable', 4500, 50, 'Ropa'),
        ('Bufanda Lana', 'Bufanda tejida invierno', 6500, 30, 'Ropa'),
        ('Camisa Oxford', 'Camisa manga larga cotton', 15000, 25, 'Ropa'),
        ('Shorts Deportivo', 'Shorts runner dry-fit', 9500, 45, 'Ropa'),
        ('Medias Pack x6', 'Medias algodón deportivo', 3500, 80, 'Ropa'),
        ('Gorra Running', 'Gorra sudor absorción', 4200, 55, 'Ropa'),
    ]

    print("📦 Creando productos con imágenes...")
    
    for i, (nombre, desc, precio, stock, cat_nombre) in enumerate(productos_data):
        cat = Categoria.objects.get(nombre=cat_nombre)
        
        # Generar palabras clave del producto (nombre + categoría)
        palabras_clave = f'{nombre},{cat_nombre}'.replace(' ', ',').lower()
        
        # 3 imágenes distintas por producto
        imagenes_producto = []
        for j in range(3):
            nombre_img = f'prod_{i+1}_{j+1}.jpg'
            ruta = descargar_imagen(palabras_clave, nombre_img)
            if ruta:
                imagenes_producto.append(ruta)
        
        img_principal = imagenes_producto[0] if imagenes_producto else None
        
        producto = Producto.objects.create(
            nombre=nombre,
            descripcion=desc,
            precio=precio,
            stock=stock,
            categoria=cat,
            imagen=img_principal
        )
        
        # Galería
        for img_path in imagenes_producto[1:]:
            ImagenProducto.objects.create(producto=producto, imagen=img_path)
        
        print(f"  ✅ {nombre}")

    print(f"\n🎉 ¡50 productos creados con imágenes!")

if __name__ == '__main__':
    poblar_50()
