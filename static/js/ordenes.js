/**
 * Gestión de Órdenes y Entregas - MiChaska POS
 */

let entregas = [];
let ordenActual = null;
let mapaRuta = null;
let rutaControl = null;
let marcadorRepartidor = null;
let watchId = null;
let ubicacionRepartidor = null;
const UBICACION_NEGOCIO = { lat: 21.8853, lng: -102.2916 };

document.addEventListener('DOMContentLoaded', async function() {
    await cargarEntregas();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('filtroEstado').addEventListener('change', filtrarEntregas);
}

async function cargarEntregas() {
    toggleLoading(true);
    
    try {
        const response = await axios.get('/api/entregas');
        entregas = response.data.entregas;
        
        actualizarEstadisticas();
        renderEntregas(entregas);
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

function actualizarEstadisticas() {
    const pendientes = entregas.filter(e => e.estado === 'Pendiente').length;
    const enCamino = entregas.filter(e => e.estado === 'En Camino').length;
    const entregadas = entregas.filter(e => e.estado === 'Entregado').length;
    const canceladas = entregas.filter(e => e.estado === 'Cancelado').length;
    
    document.getElementById('totalPendientes').textContent = pendientes;
    document.getElementById('totalEnCamino').textContent = enCamino;
    document.getElementById('totalEntregadas').textContent = entregadas;
    document.getElementById('totalCanceladas').textContent = canceladas;
}

function filtrarEntregas() {
    const estadoFiltro = document.getElementById('filtroEstado').value;
    
    if (!estadoFiltro) {
        renderEntregas(entregas);
    } else {
        const filtradas = entregas.filter(e => e.estado === estadoFiltro);
        renderEntregas(filtradas);
    }
}

function renderEntregas(lista) {
    const container = document.getElementById('entregasContainer');
    
    if (lista.length === 0) {
        container.innerHTML = '<p class="text-center text-muted py-5">No hay entregas registradas</p>';
        return;
    }
    
    const estadoColors = {
        'Pendiente': 'warning',
        'En Camino': 'info',
        'Entregado': 'success',
        'Cancelado': 'danger'
    };
    
    const estadoIcons = {
        'Pendiente': 'clock',
        'En Camino': 'truck',
        'Entregado': 'check-circle-fill',
        'Cancelado': 'x-circle-fill'
    };
    
    container.innerHTML = `
        <table class="table table-hover align-middle">
            <thead>
                <tr>
                    <th><i class="bi bi-hash"></i> Venta</th>
                    <th><i class="bi bi-calendar"></i> Fecha</th>
                    <th><i class="bi bi-geo-alt"></i> Dirección</th>
                    <th><i class="bi bi-rulers"></i> Distancia</th>
                    <th><i class="bi bi-currency-dollar"></i> Total</th>
                    <th><i class="bi bi-flag"></i> Estado</th>
                    <th><i class="bi bi-gear"></i> Acciones</th>
                </tr>
            </thead>
            <tbody>
                ${lista.map(e => `
                    <tr style="cursor: pointer;">
                        <td><strong style="font-size: 1.1rem;">#${e.venta_id}</strong></td>
                        <td>${formatDate(e.fecha, true)}</td>
                        <td><i class="bi bi-map-fill text-primary"></i> ${truncateText(e.direccion || 'N/A', 40)}</td>
                        <td><span class="badge bg-info">${e.distancia_km.toFixed(2)} km</span></td>
                        <td class="fw-bold" style="font-size: 1.1rem; color: #28a745;">${formatCurrency(e.total)}</td>
                        <td>
                            <span class="badge bg-${estadoColors[e.estado] || 'secondary'}">
                                <i class="bi bi-${estadoIcons[e.estado]}"></i> ${e.estado}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="verDetalleOrden(${e.id})">
                                <i class="bi bi-box-seam"></i> Ver Detalle
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function verDetalleOrden(entregaId) {
    toggleLoading(true);
    
    try {
        // Obtener detalle de la entrega
        const response = await axios.get(`/api/entregas/${entregaId}`);
        ordenActual = response.data.entrega;
        
        // Obtener productos de la venta
        const productosResponse = await axios.get(`/api/ventas/${ordenActual.venta_id}/detalle`);
        ordenActual.productos = productosResponse.data.detalle;
        
        // Mostrar vista detalle
        mostrarVistaDetalle();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

function mostrarVistaDetalle() {
    // Ocultar lista, mostrar detalle
    document.getElementById('vistaLista').style.display = 'none';
    document.getElementById('vistaDetalle').classList.add('active');
    
    // Rellenar información
    const estadoColors = {
        'Pendiente': 'warning',
        'En Camino': 'info',
        'Entregado': 'success',
        'Cancelado': 'danger'
    };
    
    document.getElementById('detalleVentaId').textContent = ordenActual.venta_id;
    document.getElementById('detalleFecha').textContent = formatDate(ordenActual.fecha, true);
    document.getElementById('detalleEstadoBadge').className = `badge orden-badge bg-${estadoColors[ordenActual.estado]}`;
    document.getElementById('detalleEstadoBadge').textContent = ordenActual.estado;
    document.getElementById('detalleDistancia').textContent = `${ordenActual.distancia_km.toFixed(2)} km`;
    document.getElementById('detalleDireccion').textContent = ordenActual.direccion;
    document.getElementById('detalleTotal').textContent = formatCurrency(ordenActual.total);
    
    // Calcular tiempo estimado (asumiendo 30 km/h promedio en ciudad)
    const tiempoMinutos = Math.ceil((ordenActual.distancia_km / 30) * 60);
    document.getElementById('detalleTiempoEstimado').textContent = `${tiempoMinutos} min`;
    
    // Mostrar notas si existen
    const notasDiv = document.getElementById('detalleNotas');
    if (ordenActual.notas) {
        const notasParte = ordenActual.notas.split('|')[1]?.trim() || ordenActual.notas;
        if (notasParte && notasParte !== 'Vendedor:') {
            notasDiv.innerHTML = `
                <div class="alert alert-warning">
                    <strong><i class="bi bi-sticky-fill"></i> Notas:</strong><br>
                    ${notasParte}
                </div>
            `;
        } else {
            notasDiv.innerHTML = '';
        }
    } else {
        notasDiv.innerHTML = '';
    }
    
    // Mostrar productos
    renderProductosEntrega();
    
    // Inicializar mapa
    setTimeout(() => {
        inicializarMapaRuta();
    }, 100);
}

function renderProductosEntrega() {
    const container = document.getElementById('listaProductosEntrega');
    
    if (!ordenActual.productos || ordenActual.productos.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No hay productos</p>';
        return;
    }
    
    container.innerHTML = ordenActual.productos.map((item, index) => `
        <div class="producto-item">
            <div class="d-flex justify-content-between align-items-center w-100">
                <div class="d-flex align-items-center gap-3">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                        <i class="bi bi-box-seam text-white" style="font-size: 1.5rem;"></i>
                    </div>
                    <div>
                        <h6 class="mb-1 fw-bold" style="font-size: 1.1rem;">
                            ${item.producto_nombre || 'Producto'}
                        </h6>
                        <small class="text-muted">
                            <i class="bi bi-cart-fill"></i> ${item.cantidad}x unidad${item.cantidad > 1 ? 'es' : ''} 
                            <span class="mx-1">•</span>
                            <i class="bi bi-tag-fill"></i> ${formatCurrency(item.precio_unitario)}
                        </small>
                    </div>
                </div>
                <div class="text-end">
                    <strong class="fs-4" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${formatCurrency(item.subtotal)}</strong>
                </div>
            </div>
        </div>
    `).join('');
}

function inicializarMapaRuta() {
    // Limpiar mapa anterior si existe
    if (mapaRuta) {
        mapaRuta.remove();
        mapaRuta = null;
    }
    
    // Detener seguimiento GPS anterior
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
    
    console.log('🗺️ Inicializando mapa de ruta...');
    
    // Crear contenedor del mapa
    const contenedorMapa = document.getElementById('mapaRuta');
    if (!contenedorMapa) {
        console.error('❌ Contenedor del mapa no encontrado');
        return;
    }
    
    // Asegurar que tenga altura
    contenedorMapa.style.height = '400px';
    
    // CRÍTICO: Configurar MutationObserver para eliminar paneles de Leaflet Routing
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Es un elemento
                    // Buscar y eliminar cualquier contenedor de routing
                    if (node.classList && (
                        node.classList.contains('leaflet-routing-container') ||
                        node.classList.contains('leaflet-routing-alternatives-container') ||
                        node.classList.contains('leaflet-routing-alt') ||
                        Array.from(node.classList).some(c => c.includes('leaflet-routing'))
                    )) {
                        console.log('🚫 Eliminando panel de routing:', node.className);
                        node.remove();
                    }
                    
                    // Buscar dentro del nodo añadido
                    const routingElements = node.querySelectorAll('[class*="leaflet-routing"]');
                    routingElements.forEach(el => {
                        console.log('🚫 Eliminando elemento de routing:', el.className);
                        el.remove();
                    });
                }
            });
        });
    });
    
    // Observar el contenedor del mapa
    observer.observe(contenedorMapa, {
        childList: true,
        subtree: true
    });
    
    try {
        // Crear mapa
        mapaRuta = L.map('mapaRuta').setView([UBICACION_NEGOCIO.lat, UBICACION_NEGOCIO.lng], 13);
        console.log('✅ Mapa creado');
        
        // Agregar tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(mapaRuta);
        console.log('✅ Tiles agregados');
        
        // Marcador del negocio
        const iconoNegocio = L.divIcon({
            html: '<div style="background-color: #0d6efd; width: 35px; height: 35px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;"><i class="bi bi-shop text-white fs-5"></i></div>',
            className: '',
            iconSize: [35, 35]
        });
        
        L.marker([UBICACION_NEGOCIO.lat, UBICACION_NEGOCIO.lng], {icon: iconoNegocio})
            .addTo(mapaRuta)
            .bindPopup('<strong>🏪 Mi Chas-K</strong><br>Punto de Partida');
        
        // Marcador del destino
        const iconoDestino = L.divIcon({
            html: '<div style="background-color: #dc3545; width: 35px; height: 35px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;"><i class="bi bi-house-fill text-white fs-5"></i></div>',
            className: '',
            iconSize: [35, 35]
        });
        
        L.marker([ordenActual.latitud, ordenActual.longitud], {icon: iconoDestino})
            .addTo(mapaRuta)
            .bindPopup(`<strong>🏠 Destino</strong><br>${ordenActual.direccion}`);
        
        console.log('✅ Marcadores agregados');
        
        // Iniciar seguimiento GPS del repartidor
        iniciarSeguimientoGPS();
        
        // Calcular ruta con Leaflet Routing Machine
        console.log('📍 Calculando ruta...');
        rutaControl = L.Routing.control({
            waypoints: [
                L.latLng(UBICACION_NEGOCIO.lat, UBICACION_NEGOCIO.lng),
                L.latLng(ordenActual.latitud, ordenActual.longitud)
            ],
            routeWhileDragging: false,
            showAlternatives: false,
            addWaypoints: false,
            fitSelectedRoutes: false,
            show: false,
            lineOptions: {
                styles: [{color: '#0d6efd', opacity: 0.8, weight: 6}]
            },
            createMarker: function() { return null; }, // No crear marcadores adicionales
            language: 'es',
            
            // CRÍTICO: Configurar el contenedor para que no se muestre
            container: null,
            collapsible: false,
            
            // Configuración del plan
            plan: L.Routing.plan([
                L.latLng(UBICACION_NEGOCIO.lat, UBICACION_NEGOCIO.lng),
                L.latLng(ordenActual.latitud, ordenActual.longitud)
            ], {
                createMarker: function() { return null; },
                show: false
            })
        }).addTo(mapaRuta);
        
        // Ocultar el contenedor inmediatamente después de agregarlo
        setTimeout(() => {
            const routingContainers = document.querySelectorAll('.leaflet-routing-container, .leaflet-routing-alt, .leaflet-routing-alternatives-container, [class*="leaflet-routing"]');
            routingContainers.forEach(container => {
                if (container) {
                    container.style.display = 'none';
                    container.style.visibility = 'hidden';
                    container.style.opacity = '0';
                    container.style.pointerEvents = 'none';
                    container.remove(); // Eliminar completamente del DOM
                }
            });
        }, 100);
        
        // Capturar instrucciones de ruta
        rutaControl.on('routesfound', function(e) {
            console.log('✅ Ruta encontrada');
            const routes = e.routes;
            const instrucciones = routes[0].instructions;
            
            mostrarInstruccionesRuta(instrucciones, routes[0].summary);
            
            // Volver a ocultar el panel después de encontrar la ruta
            setTimeout(() => {
                const routingContainers = document.querySelectorAll('.leaflet-routing-container, .leaflet-routing-alt, .leaflet-routing-alternatives-container, [class*="leaflet-routing"]');
                routingContainers.forEach(container => {
                    if (container) {
                        container.style.display = 'none';
                        container.remove();
                    }
                });
            }, 100);
        });
        
        // Ajustar vista para mostrar toda la ruta
        setTimeout(() => {
            mapaRuta.fitBounds([
                [UBICACION_NEGOCIO.lat, UBICACION_NEGOCIO.lng],
                [ordenActual.latitud, ordenActual.longitud]
            ], {padding: [50, 50]});
            console.log('✅ Mapa ajustado');
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error inicializando mapa:', error);
        const contenedor = document.getElementById('mapaRuta');
        contenedor.innerHTML = `
            <div class="alert alert-danger m-3">
                <strong>Error cargando mapa</strong><br>
                ${error.message}
            </div>
        `;
    }
}

function iniciarSeguimientoGPS() {
    if (!navigator.geolocation) {
        console.warn('⚠️ Geolocalización no disponible');
        return;
    }
    
    console.log('📡 Iniciando seguimiento GPS...');
    
    // Opciones de geolocalización
    const opciones = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
    };
    
    // Obtener posición inicial
    navigator.geolocation.getCurrentPosition(
        (position) => {
            console.log('✅ Ubicación obtenida:', position.coords);
            actualizarUbicacionRepartidor(position.coords.latitude, position.coords.longitude);
        },
        (error) => {
            console.warn('⚠️ Error obteniendo ubicación inicial:', error.message);
        },
        opciones
    );
    
    // Seguimiento continuo
    watchId = navigator.geolocation.watchPosition(
        (position) => {
            actualizarUbicacionRepartidor(position.coords.latitude, position.coords.longitude);
        },
        (error) => {
            console.warn('⚠️ Error en seguimiento GPS:', error.message);
        },
        opciones
    );
}

function actualizarUbicacionRepartidor(lat, lng) {
    if (!mapaRuta) return;
    
    ubicacionRepartidor = { lat, lng };
    console.log('📍 Ubicación repartidor actualizada:', lat.toFixed(6), lng.toFixed(6));
    
    // Crear o actualizar marcador del repartidor
    if (marcadorRepartidor) {
        marcadorRepartidor.setLatLng([lat, lng]);
    } else {
        const iconoRepartidor = L.divIcon({
            html: `
                <div style="position: relative;">
                    <div style="background-color: #28a745; width: 40px; height: 40px; border-radius: 50%; border: 4px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; animation: pulse 2s infinite;">
                        <i class="bi bi-geo-alt-fill text-white fs-4"></i>
                    </div>
                    <div style="position: absolute; top: -8px; right: -8px; background-color: #28a745; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; animation: ping 1.5s infinite;"></div>
                </div>
                <style>
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                    }
                    @keyframes ping {
                        0% { transform: scale(1); opacity: 1; }
                        100% { transform: scale(2); opacity: 0; }
                    }
                </style>
            `,
            className: '',
            iconSize: [40, 40]
        });
        
        marcadorRepartidor = L.marker([lat, lng], {
            icon: iconoRepartidor,
            zIndexOffset: 1000
        }).addTo(mapaRuta);
        
        marcadorRepartidor.bindPopup('<strong>📍 Tu ubicación</strong><br>Repartidor en tiempo real');
    }
    
    // Actualizar ruta si está en camino
    if (ordenActual && ordenActual.estado === 'En Camino' && rutaControl) {
        rutaControl.setWaypoints([
            L.latLng(lat, lng),
            L.latLng(ordenActual.latitud, ordenActual.longitud)
        ]);
    }
}

function centrarEnRepartidor() {
    if (!mapaRuta || !ubicacionRepartidor) {
        mostrarNotificacion('No se ha detectado tu ubicación aún', 'warning');
        return;
    }
    
    mapaRuta.setView([ubicacionRepartidor.lat, ubicacionRepartidor.lng], 16, {
        animate: true,
        duration: 0.5
    });
    
    if (marcadorRepartidor) {
        marcadorRepartidor.openPopup();
    }
    
    mostrarNotificacion('Mapa centrado en tu ubicación', 'success');
}

function mostrarInstruccionesRuta(instrucciones, summary) {
    const container = document.getElementById('instruccionesRuta');
    
    const distanciaTotal = (summary.totalDistance / 1000).toFixed(2);
    const tiempoTotal = Math.ceil(summary.totalTime / 60);
    
    let html = `
        <div class="ruta-info-card mb-3">
            <div class="row text-center">
                <div class="col-6">
                    <i class="bi bi-geo-alt-fill" style="font-size: 2.5rem; opacity: 0.9;"></i>
                    <h3 class="tiempo-estimado mb-0" style="color: white;">${distanciaTotal}</h3>
                    <p class="mb-0" style="opacity: 0.9; font-size: 1.1rem;">KILÓMETROS</p>
                </div>
                <div class="col-6">
                    <i class="bi bi-clock-fill" style="font-size: 2.5rem; opacity: 0.9;"></i>
                    <h3 class="tiempo-estimado mb-0" style="color: white;">${tiempoTotal}</h3>
                    <p class="mb-0" style="opacity: 0.9; font-size: 1.1rem;">MINUTOS</p>
                </div>
            </div>
        </div>
        <div style="max-height: 400px; overflow-y: auto; padding-right: 10px;">
    `;
    
    instrucciones.forEach((inst, index) => {
        const distancia = inst.distance > 1000 
            ? `${(inst.distance / 1000).toFixed(1)} km` 
            : `${Math.round(inst.distance)} m`;
        
        const icono = obtenerIconoInstruccion(inst.type);
        
        html += `
            <div class="instruccion-paso">
                <div class="d-flex align-items-start">
                    <span class="numero">${index + 1}</span>
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <i class="bi bi-${icono} me-2 fs-5" style="color: #667eea;"></i>
                            <strong style="font-size: 1.05rem;">${inst.text}</strong>
                        </div>
                        ${inst.distance > 0 ? `
                            <small class="text-muted d-flex align-items-center">
                                <i class="bi bi-rulers me-1"></i> ${distancia}
                            </small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function obtenerIconoInstruccion(tipo) {
    const iconos = {
        'Straight': 'arrow-up',
        'SlightRight': 'arrow-up-right',
        'Right': 'arrow-right',
        'SharpRight': 'arrow-right',
        'TurnAround': 'arrow-repeat',
        'SharpLeft': 'arrow-left',
        'Left': 'arrow-left',
        'SlightLeft': 'arrow-up-left',
        'WaypointReached': 'flag-fill',
        'Roundabout': 'arrow-clockwise'
    };
    
    return iconos[tipo] || 'arrow-up';
}

function volverALista() {
    // Detener seguimiento GPS
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
        console.log('🛑 Seguimiento GPS detenido');
    }
    
    // Limpiar mapa
    if (mapaRuta) {
        mapaRuta.remove();
        mapaRuta = null;
    }
    if (rutaControl) {
        rutaControl = null;
    }
    marcadorRepartidor = null;
    ubicacionRepartidor = null;
    
    // Mostrar lista, ocultar detalle
    document.getElementById('vistaLista').style.display = 'block';
    document.getElementById('vistaDetalle').classList.remove('active');
    ordenActual = null;
}

async function iniciarEntrega() {
    if (!ordenActual) return;
    
    if (ordenActual.estado === 'En Camino') {
        showToast('Esta entrega ya está en camino', 'info');
        return;
    }
    
    if (!confirm('¿Iniciar esta entrega?')) return;
    
    await cambiarEstadoOrden('En Camino');
}

async function completarEntrega() {
    if (!ordenActual) return;
    
    if (ordenActual.estado === 'Entregado') {
        showToast('Esta entrega ya fue completada', 'info');
        return;
    }
    
    if (!confirm('¿Marcar como entregada?')) return;
    
    await cambiarEstadoOrden('Entregado');
    showToast('¡Entrega completada exitosamente!', 'success');
    
    // Volver a lista después de completar
    setTimeout(volverALista, 1500);
}

async function cancelarEntrega() {
    if (!ordenActual) return;
    
    if (ordenActual.estado === 'Cancelado') {
        showToast('Esta entrega ya fue cancelada', 'info');
        return;
    }
    
    const motivo = prompt('Motivo de cancelación:');
    if (!motivo) return;
    
    await cambiarEstadoOrden('Cancelado');
    showToast('Entrega cancelada', 'warning');
    
    setTimeout(volverALista, 1500);
}

async function cambiarEstadoOrden(nuevoEstado) {
    toggleLoading(true);
    
    try {
        await axios.put(`/api/entregas/${ordenActual.id}/estado`, {
            estado: nuevoEstado
        });
        
        ordenActual.estado = nuevoEstado;
        
        // Actualizar badge
        const estadoColors = {
            'Pendiente': 'warning',
            'En Camino': 'info',
            'Entregado': 'success',
            'Cancelado': 'danger'
        };
        
        document.getElementById('detalleEstadoBadge').className = `badge orden-badge bg-${estadoColors[nuevoEstado]}`;
        document.getElementById('detalleEstadoBadge').textContent = nuevoEstado;
        
        showToast(`Estado actualizado a ${nuevoEstado}`, 'success');
        
        // Recargar lista en background
        cargarEntregas();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}
