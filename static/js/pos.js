/**
 * Punto de Venta - MiChaska POS
 * Manejo del carrito, productos y procesamiento de ventas con geolocalización
 */

// Estado global
const state = {
    productos: [],
    categorias: [],
    vendedores: [],
    carrito: [],
    total: 0,
    ubicacionNegocio: null,
    ubicacionCliente: null,
    distanciaKm: null,
    map: null,
    markers: []
};

// Inicialización
document.addEventListener('DOMContentLoaded', async function() {
    await init();
    setupEventListeners();
});

/**
 * Inicializa la aplicación
 */
async function init() {
    toggleLoading(true);
    
    try {
        await Promise.all([
            cargarCategorias(),
            cargarProductos(),
            cargarVendedores()
        ]);
        
        renderProductos();
        actualizarCarrito();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

/**
 * Configura event listeners
 */
function setupEventListeners() {
    // Filtro de categoría
    document.getElementById('categoriaFilter').addEventListener('change', filterProductos);
    
    // Búsqueda con debounce
    document.getElementById('searchInput').addEventListener('input', 
        debounce(filterProductos, 300)
    );
    
    // Checkbox de entrega
    document.getElementById('esEntregaCheck').addEventListener('change', toggleEntrega);
    
    // Botón de usar ubicación GPS
    document.getElementById('usarUbicacionBtn').addEventListener('click', obtenerUbicacion);
    
    // Botón de seleccionar en mapa
    document.getElementById('seleccionarMapaBtn').addEventListener('click', mostrarMapaSeleccion);
    
    // Buscador de direcciones
    document.getElementById('buscarDireccionBtn').addEventListener('click', buscarDireccion);
    document.getElementById('buscarDireccionInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarDireccion();
        }
    });
    
    // Ocultar resultados al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#buscarDireccionInput') && !e.target.closest('#resultadosDireccion')) {
            document.getElementById('resultadosDireccion').style.display = 'none';
        }
    });
    
    // Botones del carrito
    document.getElementById('limpiarCarritoBtn').addEventListener('click', limpiarCarrito);
    document.getElementById('procesarVentaBtn').addEventListener('click', procesarVenta);
    
    // Descargar ticket desde modal
    document.getElementById('descargarTicketBtn').addEventListener('click', descargarTicket);
}

/**
 * Carga categorías desde la API
 */
async function cargarCategorias() {
    try {
        const response = await axios.get('/api/categorias');
        state.categorias = response.data.categorias;
        
        const select = document.getElementById('categoriaFilter');
        state.categorias.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.nombre;
            option.textContent = cat.nombre;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error cargando categorías:', error);
    }
}

/**
 * Carga productos desde la API
 */
async function cargarProductos() {
    try {
        const response = await axios.get('/api/productos?activos=true');
        state.productos = response.data.productos;
    } catch (error) {
        console.error('Error cargando productos:', error);
        throw error;
    }
}

/**
 * Carga vendedores desde la API
 */
async function cargarVendedores() {
    try {
        const response = await axios.get('/api/vendedores');
        state.vendedores = response.data.vendedores;
        
        const select = document.getElementById('vendedorSelect');
        state.vendedores.forEach(v => {
            const option = document.createElement('option');
            option.value = v.nombre;
            option.textContent = v.nombre;
            select.appendChild(option);
        });
        
        // Cargar vendedor en turno si existe
        cargarVendedorEnTurno();
    } catch (error) {
        console.error('Error cargando vendedores:', error);
    }
}

/**
 * Configurar vendedor en turno
 */
function configurarVendedorEnTurno() {
    const select = document.getElementById('vendedorSelect');
    const vendedorSeleccionado = select.value;
    
    if (!vendedorSeleccionado) {
        mostrarNotificacion('Por favor selecciona un vendedor primero', 'warning');
        return;
    }
    
    // Guardar en localStorage
    localStorage.setItem('vendedorEnTurno', vendedorSeleccionado);
    
    // Actualizar UI
    actualizarUIVendedorEnTurno(vendedorSeleccionado);
    
    mostrarNotificacion(`${vendedorSeleccionado} configurado como vendedor en turno`, 'success');
}

/**
 * Quitar vendedor en turno
 */
function quitarVendedorEnTurno() {
    localStorage.removeItem('vendedorEnTurno');
    
    // Limpiar selección
    document.getElementById('vendedorSelect').value = '';
    
    // Ocultar info
    document.getElementById('vendedorEnTurnoInfo').style.display = 'none';
    
    mostrarNotificacion('Vendedor en turno removido', 'info');
}

/**
 * Cargar vendedor en turno desde localStorage
 */
function cargarVendedorEnTurno() {
    const vendedorEnTurno = localStorage.getItem('vendedorEnTurno');
    
    if (vendedorEnTurno) {
        // Pre-seleccionar en el dropdown
        const select = document.getElementById('vendedorSelect');
        select.value = vendedorEnTurno;
        
        // Actualizar UI
        actualizarUIVendedorEnTurno(vendedorEnTurno);
    }
}

/**
 * Actualizar UI de vendedor en turno
 */
function actualizarUIVendedorEnTurno(nombreVendedor) {
    const infoDiv = document.getElementById('vendedorEnTurnoInfo');
    const nombreSpan = document.getElementById('vendedorEnTurnoNombre');
    
    nombreSpan.textContent = nombreVendedor;
    infoDiv.style.display = 'block';
}

/**
 * Filtra y renderiza productos
 */
function filterProductos() {
    const categoria = document.getElementById('categoriaFilter').value;
    const busqueda = document.getElementById('searchInput').value.toLowerCase();
    
    let productosFiltrados = state.productos;
    
    // Filtrar por categoría
    if (categoria !== 'Todas') {
        productosFiltrados = productosFiltrados.filter(p => p.categoria === categoria);
    }
    
    // Filtrar por búsqueda
    if (busqueda) {
        productosFiltrados = productosFiltrados.filter(p => 
            p.nombre.toLowerCase().includes(busqueda) ||
            (p.descripcion && p.descripcion.toLowerCase().includes(busqueda))
        );
    }
    
    renderProductos(productosFiltrados);
}

/**
 * Renderiza la lista de productos
 */
function renderProductos(productos = state.productos) {
    const grid = document.getElementById('productosGrid');
    
    if (productos.length === 0) {
        grid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="mt-2 text-muted">No se encontraron productos</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = productos.map(producto => `
        <div class="col-md-6 col-lg-4 col-xl-3 fade-in">
            <div class="producto-card" onclick="agregarAlCarrito(${producto.id})">
                <span class="categoria-badge">${sanitizeHTML(producto.categoria)}</span>
                <div class="nombre">${sanitizeHTML(producto.nombre)}</div>
                ${producto.descripcion ? `<small class="text-muted d-block mb-2">${sanitizeHTML(truncateText(producto.descripcion, 50))}</small>` : ''}
                <div class="d-flex justify-content-between align-items-end mt-2">
                    <div class="precio">${formatCurrency(producto.precio)}</div>
                    <div class="stock ${producto.stock < 5 ? 'bajo' : ''}">
                        <i class="bi bi-box"></i> ${producto.stock}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Agrega un producto al carrito
 */
function agregarAlCarrito(productoId) {
    const producto = state.productos.find(p => p.id === productoId);
    
    if (!producto) {
        showToast('Producto no encontrado', 'error');
        return;
    }
    
    if (producto.stock <= 0) {
        showToast('Producto sin stock', 'warning');
        return;
    }
    
    // Buscar si ya está en el carrito
    const itemExistente = state.carrito.find(item => item.producto.id === productoId);
    
    if (itemExistente) {
        if (itemExistente.cantidad >= producto.stock) {
            showToast('No hay más stock disponible', 'warning');
            return;
        }
        itemExistente.cantidad++;
    } else {
        state.carrito.push({
            producto: producto,
            cantidad: 1
        });
    }
    
    actualizarCarrito();
    showToast(`${producto.nombre} agregado al carrito`, 'success');
}

/**
 * Actualiza la visualización del carrito
 */
function actualizarCarrito() {
    const container = document.getElementById('carritoItems');
    const totalDisplay = document.getElementById('totalDisplay');
    const procesarBtn = document.getElementById('procesarVentaBtn');
    
    if (state.carrito.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-cart-x fs-1"></i>
                <p class="mt-2">Carrito vacío</p>
            </div>
        `;
        state.total = 0;
        totalDisplay.textContent = formatCurrency(0);
        procesarBtn.disabled = true;
        return;
    }
    
    // Renderizar items
    container.innerHTML = state.carrito.map((item, index) => {
        const subtotal = item.producto.precio * item.cantidad;
        return `
            <div class="carrito-item">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="flex-grow-1">
                        <div class="item-nombre">${sanitizeHTML(item.producto.nombre)}</div>
                        <div class="item-precio">${formatCurrency(item.producto.precio)} c/u</div>
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="eliminarDelCarrito(${index})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <div class="cantidad-control">
                        <button class="btn btn-sm btn-outline-secondary" onclick="cambiarCantidad(${index}, -1)">
                            <i class="bi bi-dash"></i>
                        </button>
                        <input type="number" class="form-control form-control-sm" 
                               value="${item.cantidad}" min="1" max="${item.producto.stock}"
                               onchange="actualizarCantidad(${index}, this.value)" readonly>
                        <button class="btn btn-sm btn-outline-secondary" onclick="cambiarCantidad(${index}, 1)">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                    <div class="item-subtotal">${formatCurrency(subtotal)}</div>
                </div>
            </div>
        `;
    }).join('');
    
    // Calcular total
    state.total = state.carrito.reduce((sum, item) => 
        sum + (item.producto.precio * item.cantidad), 0
    );
    
    totalDisplay.textContent = formatCurrency(state.total);
    procesarBtn.disabled = false;
}

/**
 * Elimina un item del carrito
 */
function eliminarDelCarrito(index) {
    state.carrito.splice(index, 1);
    actualizarCarrito();
    showToast('Producto eliminado del carrito', 'info');
}

/**
 * Cambia la cantidad de un item
 */
function cambiarCantidad(index, delta) {
    const item = state.carrito[index];
    const nuevaCantidad = item.cantidad + delta;
    
    if (nuevaCantidad <= 0) {
        eliminarDelCarrito(index);
        return;
    }
    
    if (nuevaCantidad > item.producto.stock) {
        showToast('No hay más stock disponible', 'warning');
        return;
    }
    
    item.cantidad = nuevaCantidad;
    actualizarCarrito();
}

/**
 * Actualiza directamente la cantidad
 */
function actualizarCantidad(index, valor) {
    const cantidad = parseInt(valor);
    const item = state.carrito[index];
    
    if (isNaN(cantidad) || cantidad <= 0) {
        eliminarDelCarrito(index);
        return;
    }
    
    if (cantidad > item.producto.stock) {
        showToast('No hay suficiente stock', 'warning');
        return;
    }
    
    item.cantidad = cantidad;
    actualizarCarrito();
}

/**
 * Limpia el carrito
 */
function limpiarCarrito() {
    if (state.carrito.length === 0) return;
    
    if (confirm('¿Desea limpiar el carrito?')) {
        state.carrito = [];
        actualizarCarrito();
        
        // Restaurar vendedor en turno si existe
        const vendedorEnTurno = localStorage.getItem('vendedorEnTurno');
        if (vendedorEnTurno) {
            document.getElementById('vendedorSelect').value = vendedorEnTurno;
        }
        
        showToast('Carrito limpiado', 'info');
    }
}

/**
 * Toggle panel de entrega
 */
function toggleEntrega() {
    const isChecked = document.getElementById('esEntregaCheck').checked;
    const panel = document.getElementById('direccionPanel');
    
    panel.style.display = isChecked ? 'block' : 'none';
    
    if (!isChecked) {
        // Limpiar datos de ubicación
        state.ubicacionCliente = null;
        state.distanciaKm = null;
        document.getElementById('ubicacionStatus').innerHTML = '';
        document.getElementById('mapContainer').style.display = 'none';
        document.getElementById('distanciaInfo').style.display = 'none';
        
        if (state.map) {
            state.map.remove();
            state.map = null;
        }
    }
}

/**
 * Obtiene la ubicación del cliente usando GPS
 */
async function obtenerUbicacion() {
    toggleLoading(true);
    
    try {
        const ubicacion = await getUserLocation();
        
        // Obtener dirección de las coordenadas
        try {
            const geoResponse = await axios.post('/api/direcciones/reversa', {
                lat: ubicacion.lat,
                lng: ubicacion.lng
            });
            
            if (geoResponse.data.success) {
                document.getElementById('direccionInput').value = geoResponse.data.direccion;
            }
        } catch (geoError) {
            console.log('No se pudo obtener la dirección, usando coordenadas');
            document.getElementById('direccionInput').value = `${ubicacion.lat.toFixed(6)}, ${ubicacion.lng.toFixed(6)}`;
        }
        
        // Validar y mostrar ubicación
        await validarYMostrarUbicacion(ubicacion.lat, ubicacion.lng, document.getElementById('direccionInput').value);
        
    } catch (error) {
        handleApiError(error);
        document.getElementById('ubicacionStatus').innerHTML = `
            <div class="alert alert-danger alert-sm">
                <i class="bi bi-x-circle"></i> ${error.message}
            </div>
        `;
    } finally {
        toggleLoading(false);
    }
}

/**
 * Muestra el mapa con la ruta de entrega
 */
function mostrarMapaConRuta(lat, lng) {
    const mapContainer = document.getElementById('mapContainer');
    mapContainer.style.display = 'block';
    
    // Limpiar mapa anterior si existe
    if (state.map) {
        state.map.remove();
    }
    
    // Crear nuevo mapa
    state.map = createMap('mapContainer', lat, lng, 14);
    
    // Marcar ubicación del negocio
    const markerNegocio = addMapMarker(
        state.map, 
        state.ubicacionNegocio.lat, 
        state.ubicacionNegocio.lng,
        `<div style="text-align: center;">
            <b>🍴 Mi Chas-K</b><br>
            <small>${state.ubicacionNegocio.direccion || 'Ubicación del negocio'}</small>
        </div>`
    );
    
    // Ícono personalizado para el negocio (azul)
    markerNegocio.setIcon(L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }));
    
    // Marcar ubicación del cliente (punto de entrega)
    const markerCliente = addMapMarker(
        state.map,
        lat,
        lng,
        `<div style="text-align: center;">
            <b>📍 Punto de Entrega</b><br>
            <small>Distancia: ${state.distanciaKm} km</small>
        </div>`
    );
    
    // Ícono personalizado para el cliente (rojo)
    markerCliente.setIcon(L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }));
    
    // Línea de ruta entre negocio y cliente
    const rutaLine = L.polyline([
        [state.ubicacionNegocio.lat, state.ubicacionNegocio.lng],
        [lat, lng]
    ], {
        color: '#dc3545',
        weight: 3,
        opacity: 0.7,
        dashArray: '10, 10',
        lineJoin: 'round'
    }).addTo(state.map);
    
    // Agregar popup a la línea con la distancia
    rutaLine.bindPopup(`
        <div style="text-align: center;">
            <b>Ruta de Entrega</b><br>
            <small>Distancia: ${state.distanciaKm} km</small>
        </div>
    `);
    
    // Círculo de radio de entrega (verde semi-transparente)
    addMapCircle(
        state.map,
        state.ubicacionNegocio.lat,
        state.ubicacionNegocio.lng,
        10,
        '#198754'
    );
    
    // Ajustar vista para mostrar ambos puntos con padding
    const bounds = L.latLngBounds(
        [state.ubicacionNegocio.lat, state.ubicacionNegocio.lng],
        [lat, lng]
    );
    state.map.fitBounds(bounds, { padding: [50, 50] });
    
    // Abrir popup del cliente automáticamente
    setTimeout(() => {
        markerCliente.openPopup();
    }, 500);
}

/**
 * Procesa la venta
 */
async function procesarVenta() {
    if (state.carrito.length === 0) {
        showToast('El carrito está vacío', 'warning');
        return;
    }
    
    const vendedor = document.getElementById('vendedorSelect').value;
    const metodoPago = document.getElementById('metodoPagoSelect').value;
    const esEntrega = document.getElementById('esEntregaCheck').checked;
    
    if (!vendedor) {
        showToast('Seleccione un vendedor', 'warning');
        return;
    }
    
    // Validar entrega si está activada
    if (esEntrega) {
        if (!state.ubicacionCliente) {
            showToast('Debe validar la ubicación de entrega', 'warning');
            return;
        }
        
        const direccion = document.getElementById('direccionInput').value.trim();
        if (!direccion) {
            showToast('Ingrese la dirección de entrega', 'warning');
            return;
        }
    }
    
    toggleLoading(true);
    
    try {
        // Preparar datos de la venta
        const ventaData = {
            items: state.carrito.map(item => ({
                producto_id: item.producto.id,
                cantidad: item.cantidad
            })),
            metodo_pago: metodoPago,
            vendedor: vendedor,
            observaciones: '',
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
        
        // Enviar venta al servidor
        const response = await axios.post('/api/ventas', ventaData);
        
        if (response.data.success) {
            mostrarVentaExitosa(response.data);
            
            // Guardar vendedor actual antes de limpiar
            const vendedorEnTurno = localStorage.getItem('vendedorEnTurno');
            
            // Limpiar carrito y formulario
            state.carrito = [];
            state.ubicacionCliente = null;
            state.distanciaKm = null;
            actualizarCarrito();
            
            document.getElementById('esEntregaCheck').checked = false;
            document.getElementById('direccionInput').value = '';
            toggleEntrega();
            
            // Restaurar vendedor en turno si existe
            if (vendedorEnTurno) {
                document.getElementById('vendedorSelect').value = vendedorEnTurno;
            } else {
                document.getElementById('vendedorSelect').value = '';
            }
            
            // Recargar productos para actualizar stock
            await cargarProductos();
            renderProductos();
        }
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

/**
 * Muestra modal de venta exitosa
 */
function mostrarVentaExitosa(data) {
    document.getElementById('ventaIdDisplay').textContent = data.venta_id;
    document.getElementById('ventaTotalDisplay').textContent = data.total.toFixed(2);
    
    const entregaInfo = document.getElementById('entregaInfoDisplay');
    if (data.es_entrega) {
        entregaInfo.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-truck"></i> <strong>Entrega a domicilio</strong>
                <br><small>Distancia: ${data.distancia_km} km</small>
            </div>
        `;
    } else {
        entregaInfo.innerHTML = '';
    }
    
    // Guardar ID de venta para descargar ticket
    state.ultimaVentaId = data.venta_id;
    
    const modal = new bootstrap.Modal(document.getElementById('ventaExitosaModal'));
    modal.show();
}

/**
 * Descarga el ticket PDF
 */
async function descargarTicket() {
    if (!state.ultimaVentaId) {
        showToast('No hay ticket para descargar', 'error');
        return;
    }
    
    toggleLoading(true);
    
    try {
        const response = await axios.get(`/api/ticket/${state.ultimaVentaId}`, {
            responseType: 'blob'
        });
        
        const blob = new Blob([response.data], { type: 'application/pdf' });
        downloadFile(blob, `ticket_${state.ultimaVentaId}.pdf`);
        
        showToast('Ticket descargado exitosamente', 'success');
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

// ============================================================================
// BÚSQUEDA DE DIRECCIONES CON NOMINATIM
// ============================================================================

/**
 * Busca direcciones usando la API de Nominatim
 */
async function buscarDireccion() {
    const query = document.getElementById('buscarDireccionInput').value.trim();
    
    if (query.length < 3) {
        showToast('Escribe al menos 3 caracteres para buscar', 'warning');
        return;
    }
    
    toggleLoading(true);
    
    try {
        const response = await axios.get('/api/direcciones/buscar', {
            params: { q: query }
        });
        
        if (response.data.success && response.data.resultados.length > 0) {
            mostrarResultadosDireccion(response.data.resultados);
        } else {
            showToast('No se encontraron direcciones', 'info');
            document.getElementById('resultadosDireccion').style.display = 'none';
        }
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

/**
 * Muestra los resultados de búsqueda de direcciones
 */
function mostrarResultadosDireccion(resultados) {
    const container = document.getElementById('resultadosDireccion');
    
    container.innerHTML = resultados.map((r, index) => `
        <button type="button" class="list-group-item list-group-item-action" onclick="seleccionarDireccion(${index})">
            <div class="d-flex w-100 justify-content-between">
                <small class="text-truncate">${r.display_name}</small>
            </div>
        </button>
    `).join('');
    
    container.style.display = 'block';
    
    // Guardar resultados en estado
    state.resultadosBusqueda = resultados;
}

/**
 * Selecciona una dirección de los resultados
 */
async function seleccionarDireccion(index) {
    const direccion = state.resultadosBusqueda[index];
    
    // Ocultar resultados
    document.getElementById('resultadosDireccion').style.display = 'none';
    
    // Validar ubicación
    await validarYMostrarUbicacion(direccion.lat, direccion.lon, direccion.display_name);
}

/**
 * Muestra el mapa para seleccionar ubicación manualmente
 */
function mostrarMapaSeleccion() {
    const mapContainer = document.getElementById('mapContainer');
    mapContainer.style.display = 'block';
    
    // Limpiar mapa anterior si existe
    if (state.map) {
        state.map.remove();
    }
    
    // Crear mapa centrado en el negocio o Aguascalientes
    const lat = state.ubicacionNegocio ? state.ubicacionNegocio.lat : 21.8853;
    const lng = state.ubicacionNegocio ? state.ubicacionNegocio.lng : -102.2916;
    
    state.map = createMap('mapContainer', lat, lng, 13);
    
    // Marcar ubicación del negocio
    if (state.ubicacionNegocio) {
        const markerNegocio = addMapMarker(
            state.map,
            state.ubicacionNegocio.lat,
            state.ubicacionNegocio.lng,
            '<b>🍴 Mi Chas-K</b>'
        );
        markerNegocio.setIcon(L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }));
        
        // Círculo de radio de entrega
        addMapCircle(state.map, state.ubicacionNegocio.lat, state.ubicacionNegocio.lng, 10, '#198754');
    }
    
    // Evento de clic en el mapa
    state.map.on('click', async function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        
        toggleLoading(true);
        
        // Obtener dirección de las coordenadas
        try {
            const response = await axios.post('/api/direcciones/reversa', {
                lat: lat,
                lng: lng
            });
            
            if (response.data.success) {
                await validarYMostrarUbicacion(lat, lng, response.data.direccion);
            }
        } catch (error) {
            // Si falla la geocodificación reversa, validar igual
            await validarYMostrarUbicacion(lat, lng, `${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        } finally {
            toggleLoading(false);
        }
    });
}

/**
 * Valida una ubicación y muestra en el mapa
 */
async function validarYMostrarUbicacion(lat, lng, direccion) {
    try {
        toggleLoading(true);
        
        // Validar ubicación con el servidor
        const response = await axios.post('/api/entregas/validar-ubicacion', {
            lat: lat,
            lng: lng
        });
        
        const data = response.data;
        state.ubicacionNegocio = data.ubicacion_negocio;
        state.ubicacionCliente = { lat: lat, lng: lng };
        state.distanciaKm = data.distancia_km;
        
        // Actualizar campo de dirección
        document.getElementById('direccionInput').value = direccion;
        
        const statusDiv = document.getElementById('ubicacionStatus');
        const distanciaInfo = document.getElementById('distanciaInfo');
        
        if (data.dentro_rango) {
            statusDiv.innerHTML = `
                <div class="alert alert-success alert-sm">
                    <i class="bi bi-check-circle"></i> Ubicación válida
                </div>
            `;
            distanciaInfo.textContent = `📍 Distancia: ${data.distancia_km} km`;
            distanciaInfo.style.display = 'block';
            
            // Mostrar mapa con ambas ubicaciones
            mostrarMapaConRuta(lat, lng);
            
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-danger alert-sm">
                    <i class="bi bi-x-circle"></i> Fuera del área de entrega
                    <br><small>Distancia: ${data.distancia_km} km (máx: ${data.radio_maximo_km} km)</small>
                </div>
            `;
            distanciaInfo.style.display = 'none';
            state.ubicacionCliente = null;
        }
        
    } catch (error) {
        handleApiError(error);
        document.getElementById('ubicacionStatus').innerHTML = `
            <div class="alert alert-danger alert-sm">
                <i class="bi bi-x-circle"></i> Error al validar ubicación
            </div>
        `;
    } finally {
        toggleLoading(false);
    }
}
