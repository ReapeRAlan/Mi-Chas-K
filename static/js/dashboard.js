/**
 * Dashboard - MiChaska POS
 * Visualización de estadísticas y métricas de ventas
 */

let currentPeriod = {
    inicio: new Date().toISOString().split('T')[0],
    fin: new Date().toISOString().split('T')[0]
};

document.addEventListener('DOMContentLoaded', async function() {
    await cargarEstadisticas();
    setupDateFilters();
});

function setupDateFilters() {
    // Aquí se pueden agregar filtros de fecha
    // Por ahora carga el día actual
}

async function cargarEstadisticas() {
    toggleLoading(true);
    
    try {
        const response = await axios.get('/api/estadisticas/ventas', {
            params: {
                fecha_inicio: currentPeriod.inicio,
                fecha_fin: currentPeriod.fin
            }
        });
        
        const data = response.data;
        
        // Actualizar tarjetas de resumen
        document.getElementById('ventasHoy').textContent = formatCurrency(data.resumen.total_ventas);
        document.getElementById('numVentas').textContent = data.resumen.num_ventas;
        document.getElementById('promedioVenta').textContent = formatCurrency(data.resumen.promedio_venta);
        
        // Calcular productos vendidos
        const totalProductos = data.productos_top.reduce((sum, p) => sum + p.cantidad_vendida, 0);
        document.getElementById('productosVendidos').textContent = totalProductos;
        
        // Renderizar últimas ventas
        await renderUltimasVentas();
        
        // Renderizar productos top
        renderProductosTop(data.productos_top);
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

async function renderUltimasVentas() {
    try {
        const response = await axios.get('/api/ventas');
        const ventas = response.data.ventas.slice(0, 10); // Últimas 10
        
        const container = document.getElementById('ventasRecientes');
        
        if (ventas.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-4">No hay ventas recientes</p>';
            return;
        }
        
        container.innerHTML = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Fecha</th>
                        <th>Total</th>
                        <th>Método</th>
                        <th>Vendedor</th>
                    </tr>
                </thead>
                <tbody>
                    ${ventas.map(v => `
                        <tr>
                            <td>${v.id}</td>
                            <td>${formatDate(v.fecha, true)}</td>
                            <td class="fw-bold text-success">${formatCurrency(v.total)}</td>
                            <td><span class="badge bg-info">${v.metodo_pago}</span></td>
                            <td>${v.vendedor || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Error cargando ventas:', error);
    }
}

function renderProductosTop(productos) {
    const container = document.getElementById('productosTop');
    
    if (productos.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No hay datos</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="list-group list-group-flush">
            ${productos.map((p, index) => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <span class="badge bg-primary rounded-pill me-2">${index + 1}</span>
                        <strong>${p.nombre}</strong>
                        <br>
                        <small class="text-muted">${p.cantidad_vendida} unidades</small>
                    </div>
                    <span class="text-success fw-bold">${formatCurrency(p.total_ventas)}</span>
                </div>
            `).join('')}
        </div>
    `;
}
