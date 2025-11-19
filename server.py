"""
MiChaska - Sistema de Facturación y POS
Flask Backend API con geolocalización para entregas locales
"""
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv
import logging
from decimal import Decimal
import math

# Importaciones del proyecto
from database.models import (
    Producto, Venta, DetalleVenta, Categoria, GastoDiario, 
    CorteCaja, Vendedor, Carrito, ItemCarrito
)
# Usar conexión dual (SQLite local / PostgreSQL producción)
from database.connection_dual import execute_query, execute_update, execute_insert, get_db_type, test_connection
from utils.pdf_generator import TicketGenerator
from utils.timezone_utils import get_mexico_datetime, format_mexico_datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Habilitar CORS
CORS(app)

# Configuración de ubicación del negocio (para entregas locales)
UBICACION_NEGOCIO = {
    'lat': float(os.getenv('BUSINESS_LAT', '21.8853')),  # Aguascalientes
    'lng': float(os.getenv('BUSINESS_LNG', '-102.2916')),
    'direccion': os.getenv('BUSINESS_ADDRESS', 'Av. Valle de Los Romeros & Federico Méndez, Villas de Ntra. Sra. de la Asunción, 20126 Aguascalientes, Ags.')
}
RADIO_ENTREGA_KM = float(os.getenv('MAX_DELIVERY_DISTANCE_KM', '10'))  # Radio de entrega en kilómetros

# Helper para convertir objetos a dict
def safe_float(value):
    """Convierte de forma segura a float"""
    if isinstance(value, Decimal):
        return float(value)
    return float(value) if value is not None else 0.0

def producto_to_dict(producto):
    """Convierte un objeto Producto a diccionario"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': safe_float(producto.precio),
        'stock': producto.stock,
        'categoria_id': producto.categoria_id,
        'codigo_barras': producto.codigo_barras,
        'descripcion': producto.descripcion,
        'activo': producto.activo,
        'imagen_url': producto.imagen_url,
        'fecha_creacion': producto.fecha_creacion if isinstance(producto.fecha_creacion, str) else (producto.fecha_creacion.isoformat() if producto.fecha_creacion else None)
    }

def venta_to_dict(venta):
    """Convierte un objeto Venta a diccionario"""
    return {
        'id': venta.id,
        'total': safe_float(venta.total),
        'metodo_pago': venta.metodo_pago,
        'descuento': safe_float(venta.descuento),
        'impuestos': safe_float(venta.impuestos),
        'fecha': venta.fecha.isoformat() if venta.fecha else None,
        'vendedor': venta.vendedor,
        'observaciones': venta.observaciones,
        'estado': venta.estado
    }

def calcular_distancia(lat1, lng1, lat2, lng2):
    """
    Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine
    """
    R = 6371  # Radio de la Tierra en km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon - evita error 404"""
    return '', 204  # No Content

@app.route('/pos')
def pos():
    """Punto de venta"""
    return render_template('pos.html')

@app.route('/inventario')
def inventario():
    """Gestión de inventario"""
    return render_template('inventario.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard de ventas"""
    return render_template('dashboard.html')

@app.route('/ordenes')
def ordenes():
    """Órdenes y entregas"""
    return render_template('ordenes.html')

@app.route('/configuracion')
def configuracion():
    """Configuración del sistema"""
    return render_template('configuracion.html')

@app.route('/vendedores')
def vendedores():
    """Gestión de vendedores"""
    return render_template('vendedores.html')

# ============================================================================
# API - PRODUCTOS
# ============================================================================

@app.route('/api/productos', methods=['GET'])
def get_productos():
    """Obtiene todos los productos"""
    try:
        categoria = request.args.get('categoria')
        busqueda = request.args.get('busqueda', '').lower()
        activos = request.args.get('activos', 'true').lower() == 'true'
        
        productos = Producto.get_all(activos_solamente=activos)
        
        # Filtrar por categoría si se especifica
        if categoria and categoria != 'Todas':
            try:
                categoria_id = int(categoria)
                productos = [p for p in productos if p.categoria_id == categoria_id]
            except ValueError:
                # Si no es un número válido, no filtrar
                pass
        
        # Filtrar por búsqueda
        if busqueda:
            productos = [p for p in productos if busqueda in p.nombre.lower() or 
                        (p.descripcion and busqueda in p.descripcion.lower())]
        
        return jsonify({
            'success': True,
            'productos': [producto_to_dict(p) for p in productos]
        })
    except Exception as e:
        logger.error(f"Error obteniendo productos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/productos/<int:producto_id>', methods=['GET'])
def get_producto(producto_id):
    """Obtiene un producto específico"""
    try:
        producto = Producto.get_by_id(producto_id)
        if producto:
            return jsonify({
                'success': True,
                'producto': producto_to_dict(producto)
            })
        return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
    except Exception as e:
        logger.error(f"Error obteniendo producto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    """Crea un nuevo producto"""
    try:
        data = request.json
        producto = Producto(
            nombre=data['nombre'],
            precio=float(data['precio']),
            stock=int(data.get('stock', 0)),
            categoria=data.get('categoria', 'General'),
            codigo_barras=data.get('codigo_barras'),
            descripcion=data.get('descripcion', ''),
            activo=data.get('activo', True)
        )
        producto_id = producto.save()
        
        return jsonify({
            'success': True,
            'producto_id': producto_id,
            'message': 'Producto creado exitosamente'
        }), 201
    except Exception as e:
        logger.error(f"Error creando producto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    """Actualiza un producto existente"""
    try:
        producto = Producto.get_by_id(producto_id)
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        data = request.json
        producto.nombre = data.get('nombre', producto.nombre)
        producto.precio = float(data.get('precio', producto.precio))
        producto.stock = int(data.get('stock', producto.stock))
        producto.categoria_id = data.get('categoria_id', producto.categoria_id)
        producto.codigo_barras = data.get('codigo_barras', producto.codigo_barras)
        producto.descripcion = data.get('descripcion', producto.descripcion)
        producto.activo = data.get('activo', producto.activo)
        
        producto.save()
        
        return jsonify({
            'success': True,
            'message': 'Producto actualizado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error actualizando producto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    """Elimina (desactiva) un producto"""
    try:
        producto = Producto.get_by_id(producto_id)
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        producto.activo = False
        producto.save()
        
        return jsonify({
            'success': True,
            'message': 'Producto desactivado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error eliminando producto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - CATEGORÍAS
# ============================================================================

@app.route('/api/categorias', methods=['GET'])
def get_categorias():
    """Obtiene todas las categorías"""
    try:
        activas = request.args.get('activas', 'true').lower() == 'true'
        categorias = Categoria.get_all(activas_solamente=activas)
        
        return jsonify({
            'success': True,
            'categorias': [{
                'id': c.id,
                'nombre': c.nombre,
                'descripcion': c.descripcion,
                'activo': c.activo
            } for c in categorias]
        })
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/categorias', methods=['POST'])
def crear_categoria():
    """Crea una nueva categoría"""
    try:
        data = request.json
        categoria = Categoria(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            activo=data.get('activo', True)
        )
        categoria_id = categoria.save()
        
        return jsonify({
            'success': True,
            'categoria_id': categoria_id,
            'message': 'Categoría creada exitosamente'
        }), 201
    except Exception as e:
        logger.error(f"Error creando categoría: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - VENTAS
# ============================================================================

@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    """Obtiene ventas con filtros opcionales"""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            ventas = Venta.get_by_fecha(fecha_inicio, fecha_fin)
        else:
            ventas = Venta.get_ventas_hoy()
        
        return jsonify({
            'success': True,
            'ventas': [venta_to_dict(v) for v in ventas]
        })
    except Exception as e:
        logger.error(f"Error obteniendo ventas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ventas/<int:venta_id>', methods=['GET'])
def get_venta(venta_id):
    """Obtiene una venta específica con sus detalles"""
    try:
        query = "SELECT * FROM ventas WHERE id = %s"
        rows = execute_query(query, (venta_id,))
        
        if not rows:
            return jsonify({'success': False, 'error': 'Venta no encontrada'}), 404
        
        venta_data = dict(rows[0])
        venta_data['total'] = safe_float(venta_data.get('total', 0))
        venta_data['descuento'] = safe_float(venta_data.get('descuento', 0))
        venta_data['impuestos'] = safe_float(venta_data.get('impuestos', 0))
        
        # Obtener detalles
        detalles = DetalleVenta.get_by_venta(venta_id)
        venta_data['detalles'] = []
        
        for detalle in detalles:
            producto = Producto.get_by_id(detalle.producto_id)
            venta_data['detalles'].append({
                'producto_id': detalle.producto_id,
                'producto_nombre': producto.nombre if producto else 'Producto no encontrado',
                'cantidad': detalle.cantidad,
                'precio_unitario': safe_float(detalle.precio_unitario),
                'subtotal': safe_float(detalle.subtotal)
            })
        
        return jsonify({
            'success': True,
            'venta': venta_data
        })
    except Exception as e:
        logger.error(f"Error obteniendo venta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ventas', methods=['POST'])
def crear_venta():
    """
    Crea una nueva venta
    Body: {
        "items": [{"producto_id": 1, "cantidad": 2}, ...],
        "metodo_pago": "Efectivo|Tarjeta",
        "vendedor": "Nombre",
        "observaciones": "...",
        "descuento": 0,
        "es_entrega": false,
        "direccion_entrega": {...}  // Opcional
    }
    """
    try:
        data = request.json
        items = data.get('items', [])
        
        if not items:
            return jsonify({'success': False, 'error': 'No hay productos en la venta'}), 400
        
        # Crear carrito temporal
        carrito = Carrito()
        
        # Agregar productos al carrito
        for item in items:
            producto = Producto.get_by_id(item['producto_id'])
            if not producto:
                return jsonify({'success': False, 'error': f'Producto {item["producto_id"]} no encontrado'}), 404
            
            if producto.stock < item['cantidad']:
                return jsonify({'success': False, 'error': f'Stock insuficiente para {producto.nombre}'}), 400
            
            carrito.agregar_producto(producto, item['cantidad'])
        
        # Validar entrega local si aplica
        es_entrega = data.get('es_entrega', False)
        distancia = None
        
        if es_entrega:
            direccion = data.get('direccion_entrega')
            if not direccion or 'lat' not in direccion or 'lng' not in direccion:
                return jsonify({'success': False, 'error': 'Dirección de entrega incompleta'}), 400
            
            # Calcular distancia
            distancia = calcular_distancia(
                UBICACION_NEGOCIO['lat'], UBICACION_NEGOCIO['lng'],
                float(direccion['lat']), float(direccion['lng'])
            )
            
            if distancia > RADIO_ENTREGA_KM:
                return jsonify({
                    'success': False, 
                    'error': f'La dirección está fuera del área de entrega ({RADIO_ENTREGA_KM}km). Distancia: {distancia:.2f}km'
                }), 400
        
        # Procesar venta
        venta = carrito.procesar_venta(
            metodo_pago=data.get('metodo_pago', 'Efectivo'),
            vendedor=data.get('vendedor', ''),
            observaciones=data.get('observaciones', '')
        )
        
        if not venta:
            return jsonify({'success': False, 'error': 'Error procesando la venta'}), 500
        
        # Si es entrega, guardar información de entrega
        if es_entrega:
            direccion = data['direccion_entrega']
            query = """
                INSERT INTO entregas (venta_id, direccion, latitud, longitud, distancia_km, estado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            execute_insert(query, (
                venta.id,
                direccion.get('direccion_completa', ''),
                direccion['lat'],
                direccion['lng'],
                distancia,
                'Pendiente'
            ))
        
        return jsonify({
            'success': True,
            'venta_id': venta.id,
            'total': safe_float(venta.total),
            'message': 'Venta procesada exitosamente',
            'es_entrega': es_entrega,
            'distancia_km': distancia if es_entrega else None
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando venta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - ENTREGAS LOCALES
# ============================================================================

@app.route('/api/entregas/validar-ubicacion', methods=['POST'])
def validar_ubicacion():
    """
    Valida si una ubicación está dentro del rango de entrega
    Body: {"lat": float, "lng": float}
    """
    try:
        data = request.json
        lat = float(data['lat'])
        lng = float(data['lng'])
        
        distancia = calcular_distancia(
            UBICACION_NEGOCIO['lat'], UBICACION_NEGOCIO['lng'],
            lat, lng
        )
        
        dentro_rango = distancia <= RADIO_ENTREGA_KM
        
        return jsonify({
            'success': True,
            'dentro_rango': dentro_rango,
            'distancia_km': round(distancia, 2),
            'radio_maximo_km': RADIO_ENTREGA_KM,
            'ubicacion_negocio': UBICACION_NEGOCIO
        })
    except Exception as e:
        logger.error(f"Error validando ubicación: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entregas', methods=['GET'])
def get_entregas():
    """Obtiene lista de entregas con filtros opcionales"""
    try:
        estado = request.args.get('estado')  # Pendiente, En Camino, Entregado
        fecha = request.args.get('fecha')
        
        query = """
            SELECT e.*, v.total, v.fecha, v.notas
            FROM entregas e
            JOIN ventas v ON e.venta_id = v.id
            WHERE 1=1
        """
        params = []
        
        if estado:
            query += " AND e.estado = %s"
            params.append(estado)
        
        if fecha:
            query += " AND DATE(v.fecha) = %s"
            params.append(fecha)
        
        query += " ORDER BY v.fecha DESC"
        
        rows = execute_query(query, tuple(params) if params else ())
        
        entregas = []
        for row in rows:
            entrega_data = dict(row)
            entrega_data['total'] = safe_float(entrega_data.get('total', 0))
            entrega_data['distancia_km'] = safe_float(entrega_data.get('distancia_km', 0))
            entregas.append(entrega_data)
        
        return jsonify({
            'success': True,
            'entregas': entregas
        })
    except Exception as e:
        logger.error(f"Error obteniendo entregas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entregas/<int:entrega_id>/estado', methods=['PUT'])
def actualizar_estado_entrega(entrega_id):
    """
    Actualiza el estado de una entrega
    Body: {"estado": "Pendiente|En Camino|Entregado|Cancelado"}
    """
    try:
        data = request.json
        nuevo_estado = data.get('estado')
        
        if nuevo_estado not in ['Pendiente', 'En Camino', 'Entregado', 'Cancelado']:
            return jsonify({'success': False, 'error': 'Estado inválido'}), 400
        
        query = "UPDATE entregas SET estado = %s, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = %s"
        execute_update(query, (nuevo_estado, entrega_id))
        
        return jsonify({
            'success': True,
            'message': f'Estado actualizado a {nuevo_estado}'
        })
    except Exception as e:
        logger.error(f"Error actualizando estado de entrega: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/entregas/<int:entrega_id>', methods=['GET'])
def get_entrega_detalle(entrega_id):
    """Obtiene el detalle de una entrega específica"""
    try:
        query = """
            SELECT e.*, v.total, v.fecha, v.notas, v.metodo_pago
            FROM entregas e
            JOIN ventas v ON e.venta_id = v.id
            WHERE e.id = %s
        """
        rows = execute_query(query, (entrega_id,))
        
        if not rows:
            return jsonify({'success': False, 'error': 'Entrega no encontrada'}), 404
        
        entrega_data = dict(rows[0])
        entrega_data['total'] = safe_float(entrega_data.get('total', 0))
        entrega_data['distancia_km'] = safe_float(entrega_data.get('distancia_km', 0))
        entrega_data['latitud'] = safe_float(entrega_data.get('latitud', 0))
        entrega_data['longitud'] = safe_float(entrega_data.get('longitud', 0))
        
        return jsonify({
            'success': True,
            'entrega': entrega_data
        })
    except Exception as e:
        logger.error(f"Error obteniendo detalle de entrega: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ventas/<int:venta_id>/detalle', methods=['GET'])
def get_venta_detalle(venta_id):
    """Obtiene el detalle de productos de una venta"""
    try:
        query = """
            SELECT dv.*, p.nombre as producto_nombre
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
            ORDER BY dv.id
        """
        rows = execute_query(query, (venta_id,))
        
        detalle = []
        for row in rows:
            item = dict(row)
            item['cantidad'] = int(item.get('cantidad', 1))
            item['precio_unitario'] = safe_float(item.get('precio_unitario', 0))
            item['subtotal'] = safe_float(item.get('subtotal', 0))
            detalle.append(item)
        
        return jsonify({
            'success': True,
            'detalle': detalle
        })
    except Exception as e:
        logger.error(f"Error obteniendo detalle de venta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - GASTOS
# ============================================================================

# ============================================================================
# API - BÚSQUEDA DE DIRECCIONES (Nominatim/OSM)
# ============================================================================

@app.route('/api/direcciones/buscar', methods=['GET'])
def buscar_direccion():
    """Busca direcciones usando Nominatim (OpenStreetMap)"""
    try:
        query = request.args.get('q', '')
        
        if not query or len(query) < 3:
            return jsonify({
                'success': False, 
                'error': 'La búsqueda debe tener al menos 3 caracteres'
            }), 400
        
        import requests
        
        # Agregar contexto de Aguascalientes para mejores resultados
        search_query = f"{query}, Aguascalientes, México"
        
        # Usar Nominatim API (OpenStreetMap)
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 5,
            'addressdetails': 1,
            'countrycodes': 'mx'
        }
        headers = {
            'User-Agent': 'MiChaska-POS/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        resultados = response.json()
        
        # Formatear resultados
        direcciones = []
        for r in resultados:
            direcciones.append({
                'display_name': r.get('display_name', ''),
                'lat': float(r.get('lat', 0)),
                'lon': float(r.get('lon', 0)),
                'type': r.get('type', ''),
                'address': r.get('address', {})
            })
        
        return jsonify({
            'success': True,
            'resultados': direcciones
        })
    except requests.RequestException as e:
        logger.error(f"Error en búsqueda de direcciones: {e}")
        return jsonify({
            'success': False, 
            'error': 'Error al buscar dirección. Intenta de nuevo.'
        }), 500
    except Exception as e:
        logger.error(f"Error buscando dirección: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/direcciones/reversa', methods=['POST'])
def geocodificacion_reversa():
    """Obtiene la dirección de unas coordenadas (reverse geocoding)"""
    try:
        data = request.json
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not lat or not lng:
            return jsonify({
                'success': False, 
                'error': 'Coordenadas requeridas'
            }), 400
        
        import requests
        
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'MiChaska-POS/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        resultado = response.json()
        
        return jsonify({
            'success': True,
            'direccion': resultado.get('display_name', ''),
            'address': resultado.get('address', {}),
            'lat': float(resultado.get('lat', lat)),
            'lon': float(resultado.get('lon', lng))
        })
    except requests.RequestException as e:
        logger.error(f"Error en geocodificación reversa: {e}")
        return jsonify({
            'success': False, 
            'error': 'Error al obtener dirección'
        }), 500
    except Exception as e:
        logger.error(f"Error en geocodificación reversa: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - GASTOS DIARIOS
# ============================================================================

@app.route('/api/gastos', methods=['GET'])
def get_gastos():
    """Obtiene gastos por fecha"""
    try:
        fecha = request.args.get('fecha', date.today().isoformat())
        gastos = GastoDiario.get_by_fecha(fecha)
        
        return jsonify({
            'success': True,
            'gastos': [{
                'id': g.id,
                'fecha': g.fecha,
                'concepto': g.concepto,
                'monto': safe_float(g.monto),
                'categoria': g.categoria,
                'descripcion': g.descripcion,
                'vendedor': g.vendedor
            } for g in gastos]
        })
    except Exception as e:
        logger.error(f"Error obteniendo gastos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/gastos', methods=['POST'])
def crear_gasto():
    """Crea un nuevo gasto"""
    try:
        data = request.json
        gasto = GastoDiario(
            fecha=data.get('fecha', date.today().isoformat()),
            concepto=data['concepto'],
            monto=float(data['monto']),
            categoria=data.get('categoria', 'Operación'),
            descripcion=data.get('descripcion', ''),
            vendedor=data.get('vendedor', '')
        )
        gasto_id = gasto.save()
        
        return jsonify({
            'success': True,
            'gasto_id': gasto_id,
            'message': 'Gasto registrado exitosamente'
        }), 201
    except Exception as e:
        logger.error(f"Error creando gasto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - CORTES DE CAJA
# ============================================================================

@app.route('/api/cortes', methods=['GET'])
def get_corte():
    """Obtiene el corte de caja de una fecha"""
    try:
        fecha = request.args.get('fecha', date.today().isoformat())
        corte = CorteCaja.get_by_fecha(fecha)
        
        if corte:
            return jsonify({
                'success': True,
                'corte': {
                    'id': corte.id,
                    'fecha': corte.fecha,
                    'dinero_inicial': safe_float(corte.dinero_inicial),
                    'dinero_final': safe_float(corte.dinero_final),
                    'ventas_efectivo': safe_float(corte.ventas_efectivo),
                    'ventas_tarjeta': safe_float(corte.ventas_tarjeta),
                    'total_gastos': safe_float(corte.total_gastos),
                    'diferencia': safe_float(corte.diferencia),
                    'observaciones': corte.observaciones,
                    'vendedor': corte.vendedor
                }
            })
        return jsonify({'success': True, 'corte': None})
    except Exception as e:
        logger.error(f"Error obteniendo corte: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cortes', methods=['POST'])
def crear_corte():
    """Crea un nuevo corte de caja"""
    try:
        data = request.json
        corte = CorteCaja(
            fecha=data.get('fecha', date.today().isoformat()),
            dinero_inicial=float(data['dinero_inicial']),
            dinero_final=float(data['dinero_final']),
            ventas_efectivo=float(data.get('ventas_efectivo', 0)),
            ventas_tarjeta=float(data.get('ventas_tarjeta', 0)),
            total_gastos=float(data.get('total_gastos', 0)),
            observaciones=data.get('observaciones', ''),
            vendedor=data.get('vendedor', '')
        )
        corte_id = corte.save()
        
        return jsonify({
            'success': True,
            'corte_id': corte_id,
            'diferencia': safe_float(corte.diferencia),
            'message': 'Corte de caja registrado exitosamente'
        }), 201
    except Exception as e:
        logger.error(f"Error creando corte: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - ESTADÍSTICAS Y DASHBOARD
# ============================================================================

@app.route('/api/estadisticas/ventas', methods=['GET'])
def get_estadisticas_ventas():
    """Obtiene estadísticas de ventas"""
    try:
        fecha_inicio = request.args.get('fecha_inicio', date.today().isoformat())
        fecha_fin = request.args.get('fecha_fin', date.today().isoformat())
        
        # Ventas totales
        query_total = """
            SELECT 
                COUNT(*) as num_ventas,
                COALESCE(SUM(total), 0) as total_ventas,
                COALESCE(AVG(total), 0) as promedio_venta
            FROM ventas
            WHERE DATE(fecha) BETWEEN %s AND %s
        """
        total_rows = execute_query(query_total, (fecha_inicio, fecha_fin))
        total_data = dict(total_rows[0]) if total_rows else {}
        
        # Ventas por método de pago
        query_metodos = """
            SELECT 
                metodo_pago,
                COUNT(*) as cantidad,
                COALESCE(SUM(total), 0) as total
            FROM ventas
            WHERE DATE(fecha) BETWEEN %s AND %s
            GROUP BY metodo_pago
        """
        metodos_rows = execute_query(query_metodos, (fecha_inicio, fecha_fin))
        
        # Productos más vendidos
        query_productos = """
            SELECT 
                p.nombre,
                SUM(dv.cantidad) as cantidad_vendida,
                COALESCE(SUM(dv.subtotal), 0) as total_ventas
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v ON dv.venta_id = v.id
            WHERE DATE(v.fecha) BETWEEN %s AND %s
            GROUP BY p.id, p.nombre
            ORDER BY cantidad_vendida DESC
            LIMIT 10
        """
        productos_rows = execute_query(query_productos, (fecha_inicio, fecha_fin))
        
        return jsonify({
            'success': True,
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'resumen': {
                'num_ventas': total_data.get('num_ventas', 0),
                'total_ventas': safe_float(total_data.get('total_ventas', 0)),
                'promedio_venta': safe_float(total_data.get('promedio_venta', 0))
            },
            'por_metodo_pago': [{
                'metodo': row['metodo_pago'],
                'cantidad': row['cantidad'],
                'total': safe_float(row['total'])
            } for row in metodos_rows],
            'productos_top': [{
                'nombre': row['nombre'],
                'cantidad_vendida': row['cantidad_vendida'],
                'total_ventas': safe_float(row['total_ventas'])
            } for row in productos_rows]
        })
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - VENDEDORES
# ============================================================================

@app.route('/api/vendedores', methods=['GET'])
def get_vendedores():
    """Obtiene lista de vendedores activos"""
    try:
        vendedores = Vendedor.get_all_activos()
        return jsonify({
            'success': True,
            'vendedores': [{
                'id': v.id,
                'nombre': v.nombre,
                'apellido': v.apellido,
                'email': v.email,
                'telefono': v.telefono,
                'activo': v.activo,
                'fecha_creacion': v.fecha_creacion if isinstance(v.fecha_creacion, str) else (v.fecha_creacion.isoformat() if v.fecha_creacion else None)
            } for v in vendedores]
        })
    except Exception as e:
        logger.error(f"Error obteniendo vendedores: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vendedores', methods=['POST'])
def crear_vendedor():
    """Crea un nuevo vendedor"""
    try:
        data = request.json
        nombre = data.get('nombre')
        apellido = data.get('apellido', '')
        email = data.get('email')
        telefono = data.get('telefono', '')
        
        if not nombre:
            return jsonify({'success': False, 'error': 'El nombre es requerido'}), 400
        
        query = """
            INSERT INTO vendedores (nombre, apellido, email, telefono, activo)
            VALUES (%s, %s, %s, %s, 1)
        """
        vendedor_id = execute_insert(query, (nombre, apellido, email, telefono))
        
        return jsonify({
            'success': True,
            'vendedor_id': vendedor_id,
            'message': 'Vendedor creado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error creando vendedor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vendedores/<int:vendedor_id>', methods=['PUT'])
def actualizar_vendedor(vendedor_id):
    """Actualiza un vendedor existente"""
    try:
        data = request.json
        
        query = """
            UPDATE vendedores 
            SET nombre = %s, apellido = %s, email = %s, telefono = %s
            WHERE id = %s
        """
        
        execute_update(query, (
            data.get('nombre'),
            data.get('apellido', ''),
            data.get('email'),
            data.get('telefono', ''),
            vendedor_id
        ))
        
        return jsonify({
            'success': True,
            'message': 'Vendedor actualizado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error actualizando vendedor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vendedores/<int:vendedor_id>', methods=['DELETE'])
def eliminar_vendedor(vendedor_id):
    """Desactiva un vendedor (soft delete)"""
    try:
        query = "UPDATE vendedores SET activo = 0 WHERE id = %s"
        execute_update(query, (vendedor_id,))
        
        return jsonify({
            'success': True,
            'message': 'Vendedor desactivado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error eliminando vendedor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - PDFs y REPORTES
# ============================================================================

@app.route('/api/ticket/<int:venta_id>', methods=['GET'])
def generar_ticket(venta_id):
    """Genera y descarga el ticket PDF de una venta"""
    try:
        # Obtener venta con detalle
        query = "SELECT * FROM ventas WHERE id = %s"
        rows = execute_query(query, (venta_id,))
        
        if not rows:
            return jsonify({'success': False, 'error': 'Venta no encontrada'}), 404
        
        venta_data = dict(rows[0])
        
        # Obtener detalle de productos
        query_detalle = """
            SELECT dv.*, p.nombre as producto_nombre
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
        """
        detalle_rows = execute_query(query_detalle, (venta_id,))
        
        # Generar PDF
        from utils.pdf_generator import TicketGenerator
        generator = TicketGenerator()
        pdf_bytes = generator.generar_ticket_memoria(venta_data, detalle_rows)
        
        # Enviar archivo
        from io import BytesIO
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ticket_{venta_id}.pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generando ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API - SALUD DEL SISTEMA
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint para Render"""
    try:
        # Verificar conexión a base de datos
        execute_query("SELECT 1")
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Manejo de error 404"""
    return jsonify({'success': False, 'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejo de error 500"""
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Iniciando MiChaska en puerto {port}")
    logger.info(f"Ubicación del negocio: {UBICACION_NEGOCIO}")
    logger.info(f"Radio de entrega: {RADIO_ENTREGA_KM}km")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
