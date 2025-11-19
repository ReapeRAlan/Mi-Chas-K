/**
 * Gestión de Inventario - MiChaska POS
 */

let productos = [];
let categorias = [];
let productoEditando = null;

document.addEventListener('DOMContentLoaded', async function() {
    await init();
});

async function init() {
    toggleLoading(true);
    
    try {
        await Promise.all([
            cargarCategorias(),
            cargarProductos()
        ]);
        
        renderProductosTable();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

async function cargarCategorias() {
    try {
        const response = await axios.get('/api/categorias');
        categorias = response.data.categorias;
        
        // Llenar select de categorías en el modal
        const select = document.getElementById('productoCategoria');
        select.innerHTML = categorias.map(c => 
            `<option value="${c.nombre}">${c.nombre}</option>`
        ).join('');
        
    } catch (error) {
        console.error('Error cargando categorías:', error);
    }
}

async function cargarProductos() {
    try {
        const response = await axios.get('/api/productos?activos=true');
        productos = response.data.productos;
    } catch (error) {
        console.error('Error cargando productos:', error);
        throw error;
    }
}

function renderProductosTable() {
    const container = document.getElementById('productosTable');
    
    if (productos.length === 0) {
        container.innerHTML = '<p class="text-center text-muted py-5">No hay productos registrados</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Categoría</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                ${productos.map(p => `
                    <tr>
                        <td>${p.id}</td>
                        <td>${sanitizeHTML(p.nombre)}</td>
                        <td><span class="badge bg-info">${p.categoria}</span></td>
                        <td class="fw-bold">${formatCurrency(p.precio)}</td>
                        <td>
                            <span class="badge ${p.stock < 5 ? 'bg-danger' : 'bg-success'}">
                                ${p.stock}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="editarProducto(${p.id})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="eliminarProducto(${p.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function editarProducto(id) {
    const producto = productos.find(p => p.id === id);
    if (!producto) return;
    
    productoEditando = producto;
    
    document.getElementById('productoNombre').value = producto.nombre;
    document.getElementById('productoPrecio').value = producto.precio;
    document.getElementById('productoStock').value = producto.stock;
    document.getElementById('productoCategoria').value = producto.categoria;
    
    document.querySelector('#nuevoProductoModal .modal-title').textContent = 'Editar Producto';
    
    const modal = new bootstrap.Modal(document.getElementById('nuevoProductoModal'));
    modal.show();
}

async function guardarProducto() {
    const nombre = document.getElementById('productoNombre').value.trim();
    const precio = parseFloat(document.getElementById('productoPrecio').value);
    const stock = parseInt(document.getElementById('productoStock').value);
    const categoria = document.getElementById('productoCategoria').value;
    
    if (!nombre || !precio || !stock || !categoria) {
        showToast('Complete todos los campos', 'warning');
        return;
    }
    
    toggleLoading(true);
    
    try {
        const data = { nombre, precio, stock, categoria };
        
        if (productoEditando) {
            // Actualizar
            await axios.put(`/api/productos/${productoEditando.id}`, data);
            showToast('Producto actualizado exitosamente', 'success');
        } else {
            // Crear
            await axios.post('/api/productos', data);
            showToast('Producto creado exitosamente', 'success');
        }
        
        // Cerrar modal y recargar
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevoProductoModal'));
        modal.hide();
        
        productoEditando = null;
        document.getElementById('productoForm').reset();
        
        await cargarProductos();
        renderProductosTable();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

async function eliminarProducto(id) {
    if (!confirm('¿Está seguro de eliminar este producto?')) return;
    
    toggleLoading(true);
    
    try {
        await axios.delete(`/api/productos/${id}`);
        showToast('Producto eliminado exitosamente', 'success');
        
        await cargarProductos();
        renderProductosTable();
        
    } catch (error) {
        handleApiError(error);
    } finally {
        toggleLoading(false);
    }
}

// Reset modal al cerrar
document.getElementById('nuevoProductoModal').addEventListener('hidden.bs.modal', function() {
    productoEditando = null;
    document.getElementById('productoForm').reset();
    document.querySelector('#nuevoProductoModal .modal-title').textContent = 'Nuevo Producto';
});
