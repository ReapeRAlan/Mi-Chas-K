# 🚚 Flujo de Entrega a Domicilio - Mi Chas-K

## 📋 Resumen del Flujo Completo

### Escenario 1: Venta SIN Entrega (Local)
```
1. Usuario agrega productos al carrito
2. Selecciona vendedor
3. Selecciona método de pago
4. Clic en "Procesar Venta"
5. ✅ Venta procesada sin información de entrega
```

### Escenario 2: Venta CON Entrega a Domicilio
```
1. Usuario agrega productos al carrito
2. ✅ Marca checkbox "Entrega a domicilio"
3. Panel de dirección se muestra
4. Usuario selecciona ubicación (3 opciones):
   
   OPCIÓN A: Buscar dirección
   ├─ Escribe dirección
   ├─ Resultados de Nominatim (OSM)
   ├─ Selecciona de la lista
   └─ ✅ Se valida automáticamente
   
   OPCIÓN B: Usar GPS
   ├─ Clic "Usar mi ubicación GPS"
   ├─ Autoriza geolocalización
   ├─ Obtiene coordenadas
   ├─ Geocodificación reversa → dirección
   └─ ✅ Se valida automáticamente
   
   OPCIÓN C: Seleccionar en mapa
   ├─ Clic "Seleccionar en mapa"
   ├─ Mapa se muestra con negocio y radio
   ├─ Clic en punto deseado
   ├─ Geocodificación reversa → dirección
   └─ ✅ Se valida automáticamente

5. Validación de ubicación:
   ├─ Calcula distancia (Haversine)
   ├─ Verifica radio ≤ 10km
   ├─ Si VÁLIDO: ✅ Muestra mapa con ruta
   └─ Si INVÁLIDO: ❌ Muestra error "Fuera de área"

6. Usuario completa venta:
   ├─ Selecciona vendedor
   ├─ Selecciona método de pago
   └─ Clic "Procesar Venta"

7. Backend procesa:
   ├─ Valida productos y stock
   ├─ Re-valida distancia de entrega
   ├─ Crea registro en tabla 'ventas'
   ├─ Crea registro en tabla 'entregas'
   ├─ Actualiza stock productos
   └─ ✅ Retorna confirmación

8. Frontend muestra:
   ├─ Modal de venta exitosa
   ├─ ID de venta
   ├─ Total
   ├─ Info de entrega (distancia)
   └─ Opción descargar ticket PDF
```

## 🔍 Detalle Técnico del Flujo

### 1. Activar Entrega a Domicilio
**Frontend** (`pos.js`)
```javascript
// Evento: checkbox "Entrega a domicilio"
document.getElementById('esEntregaCheck').addEventListener('change', toggleEntrega);

function toggleEntrega() {
    const checked = this.checked;
    const panel = document.getElementById('direccionPanel');
    panel.style.display = checked ? 'block' : 'none';
    
    if (!checked) {
        // Limpiar datos de entrega
        state.ubicacionCliente = null;
        state.distanciaKm = null;
        document.getElementById('direccionInput').value = '';
    }
}
```

### 2. Buscar Dirección (OPCIÓN A)
**Frontend** → **Backend** → **Nominatim API**
```javascript
// Usuario escribe: "avenida valle"
async function buscarDireccion() {
    const query = document.getElementById('buscarDireccionInput').value;
    
    // 1. Petición a backend
    const response = await axios.get('/api/direcciones/buscar', {
        params: { q: query }
    });
    
    // 2. Mostrar resultados
    mostrarResultadosDireccion(response.data.resultados);
}
```

**Backend** (`server.py`)
```python
@app.route('/api/direcciones/buscar', methods=['GET'])
def buscar_direccion():
    query = request.args.get('q', '')
    
    # 1. Agregar contexto de Aguascalientes
    search_query = f"{query}, Aguascalientes, México"
    
    # 2. Llamar a Nominatim API
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': search_query,
        'format': 'json',
        'limit': 5,
        'addressdetails': 1,
        'countrycodes': 'mx'
    }
    
    response = requests.get(url, params=params, headers={'User-Agent': 'MiChaska-POS/1.0'})
    resultados = response.json()
    
    # 3. Retornar resultados formateados
    return jsonify({
        'success': True,
        'resultados': [{
            'display_name': r.get('display_name'),
            'lat': float(r.get('lat')),
            'lon': float(r.get('lon')),
            'address': r.get('address', {})
        } for r in resultados]
    })
```

### 3. Seleccionar Dirección de Resultados
```javascript
function seleccionarDireccion(index) {
    const direccion = state.resultadosBusqueda[index];
    
    // Validar y mostrar ubicación
    await validarYMostrarUbicacion(
        direccion.lat, 
        direccion.lon, 
        direccion.display_name
    );
}
```

### 4. Validar Ubicación
**Frontend** → **Backend**
```javascript
async function validarYMostrarUbicacion(lat, lng, direccion) {
    // 1. Enviar a backend para validar
    const response = await axios.post('/api/entregas/validar-ubicacion', {
        lat: lat,
        lng: lng
    });
    
    const data = response.data;
    
    // 2. Guardar en estado
    state.ubicacionNegocio = data.ubicacion_negocio;
    state.ubicacionCliente = { lat: lat, lng: lng };
    state.distanciaKm = data.distancia_km;
    
    // 3. Actualizar UI
    document.getElementById('direccionInput').value = direccion;
    
    // 4. Mostrar mapa con ruta
    if (data.dentro_rango) {
        mostrarMapaConRuta(lat, lng);
    }
}
```

**Backend** (cálculo de distancia)
```python
@app.route('/api/entregas/validar-ubicacion', methods=['POST'])
def validar_ubicacion():
    data = request.json
    lat_cliente = float(data['lat'])
    lng_cliente = float(data['lng'])
    
    # Calcular distancia con fórmula de Haversine
    distancia = calcular_distancia(
        UBICACION_NEGOCIO['lat'], 
        UBICACION_NEGOCIO['lng'],
        lat_cliente, 
        lng_cliente
    )
    
    dentro_rango = distancia <= RADIO_ENTREGA_KM
    
    return jsonify({
        'success': True,
        'dentro_rango': dentro_rango,
        'distancia_km': round(distancia, 2),
        'radio_maximo_km': RADIO_ENTREGA_KM,
        'ubicacion_negocio': UBICACION_NEGOCIO
    })
```

### 5. Procesar Venta con Entrega
```javascript
async function procesarVenta() {
    const esEntrega = document.getElementById('esEntregaCheck').checked;
    
    // Validaciones
    if (esEntrega && !state.ubicacionCliente) {
        showToast('Debe validar la ubicación de entrega', 'warning');
        return;
    }
    
    // Preparar datos
    const ventaData = {
        items: state.carrito.map(item => ({
            producto_id: item.producto.id,
            cantidad: item.cantidad
        })),
        metodo_pago: metodoPago,
        vendedor: vendedor,
        es_entrega: esEntrega
    };
    
    // Agregar datos de entrega si aplica
    if (esEntrega) {
        ventaData.direccion_entrega = {
            direccion_completa: document.getElementById('direccionInput').value,
            lat: state.ubicacionCliente.lat,
            lng: state.ubicacionCliente.lng
        };
    }
    
    // Enviar al servidor
    const response = await axios.post('/api/ventas', ventaData);
}
```

**Backend** (crear venta y entrega)
```python
@app.route('/api/ventas', methods=['POST'])
def crear_venta():
    data = request.json
    es_entrega = data.get('es_entrega', False)
    distancia = None
    
    # 1. Validar productos y stock
    carrito = Carrito()
    for item in data.get('items', []):
        producto = Producto.get_by_id(item['producto_id'])
        carrito.agregar_producto(producto, item['cantidad'])
    
    # 2. Validar entrega si aplica
    if es_entrega:
        direccion = data.get('direccion_entrega')
        distancia = calcular_distancia(
            UBICACION_NEGOCIO['lat'], UBICACION_NEGOCIO['lng'],
            float(direccion['lat']), float(direccion['lng'])
        )
        
        if distancia > RADIO_ENTREGA_KM:
            return jsonify({'success': False, 'error': 'Fuera de área'}), 400
    
    # 3. Procesar venta
    venta = carrito.procesar_venta(
        metodo_pago=data.get('metodo_pago'),
        vendedor=data.get('vendedor')
    )
    
    # 4. Guardar entrega si aplica
    if es_entrega:
        query = """
            INSERT INTO entregas (venta_id, direccion, lat, lng, distancia_km, estado)
            VALUES (%s, %s, %s, %s, %s, 'Pendiente')
        """
        execute_update(query, (
            venta.id,
            direccion.get('direccion_completa'),
            direccion['lat'],
            direccion['lng'],
            distancia
        ))
    
    return jsonify({
        'success': True,
        'venta_id': venta.id,
        'total': venta.total,
        'es_entrega': es_entrega,
        'distancia_km': distancia
    })
```

## 📊 Estado del Sistema

### Variables de Estado (Frontend)
```javascript
const state = {
    productos: [],           // Lista de productos disponibles
    categorias: [],          // Categorías
    vendedores: [],          // Vendedores activos
    carrito: [],             // Items en el carrito
    total: 0,                // Total de la venta
    ubicacionNegocio: null,  // {lat, lng, direccion}
    ubicacionCliente: null,  // {lat, lng}
    distanciaKm: null,       // Distancia calculada
    map: null,               // Instancia de Leaflet
    resultadosBusqueda: []   // Resultados de búsqueda de direcciones
};
```

### Validaciones Importantes

✅ **Frontend**:
- Carrito no vacío
- Vendedor seleccionado
- Si entrega: ubicación validada
- Si entrega: dirección no vacía

✅ **Backend**:
- Productos existen y tienen stock
- Si entrega: coordenadas válidas
- Si entrega: distancia ≤ 10km
- Transacción de base de datos exitosa

## 🗺️ Mapa Interactivo

### Elementos Visuales
- 🔵 **Marcador Azul**: Ubicación Mi Chas-K (negocio)
- 🔴 **Marcador Rojo**: Punto de entrega (cliente)
- 🟢 **Círculo Verde**: Radio de cobertura (10km, semi-transparente)
- ➖ **Línea Roja Punteada**: Ruta de entrega
- 📏 **Popup**: Información de distancia

### Interacciones del Mapa
1. **Zoom automático**: Ajusta para mostrar ambos puntos
2. **Click en mapa**: Selecciona nueva ubicación
3. **Click en marcador**: Muestra información
4. **Click en línea**: Muestra distancia

## 🔄 Ciclo de Vida de una Entrega

```
Estado: Pendiente
  ↓ (Venta procesada)
Estado: En Camino
  ↓ (Repartidor actualiza)
Estado: Entregado
  ↓ (Confirmación)
✅ Completado
```

## 📝 Notas Importantes

1. **Sin entrega**: `distancia = None`, no se crea registro en tabla `entregas`
2. **Con entrega**: Se crea registro automático con estado "Pendiente"
3. **Geocodificación**: Usa Nominatim (OpenStreetMap) - gratis, sin API key
4. **Límite de búsquedas**: Respeta políticas de uso de Nominatim (1 req/segundo)
5. **Timeout**: 5 segundos para peticiones a Nominatim
6. **User-Agent**: `MiChaska-POS/1.0` (requerido por Nominatim)

## ✅ Checklist de Prueba

- [ ] Venta sin entrega funciona
- [ ] Activar checkbox muestra panel
- [ ] Buscar dirección muestra resultados
- [ ] Seleccionar dirección valida ubicación
- [ ] GPS obtiene ubicación y valida
- [ ] Mapa permite seleccionar punto
- [ ] Ubicación fuera de rango muestra error
- [ ] Ubicación válida muestra mapa con ruta
- [ ] Venta con entrega se procesa correctamente
- [ ] Registro de entrega se crea en BD
- [ ] Modal muestra información de entrega

---

**Última actualización**: Noviembre 18, 2025
