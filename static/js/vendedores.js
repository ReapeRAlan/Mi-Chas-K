/**
 * Gestión de Vendedores - Mi Chas-K
 */

let vendedores = [];
let modalVendedor = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    modalVendedor = new bootstrap.Modal(document.getElementById('modalVendedor'));
    cargarVendedores();
});

/**
 * Carga la lista de vendedores
 */
async function cargarVendedores() {
    try {
        toggleLoading(true);
        
        const response = await fetch('/api/vendedores');
        const data = await response.json();
        
        if (data.success) {
            vendedores = data.vendedores;
            renderizarVendedores();
        } else {
            showToast('Error al cargar vendedores: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar vendedores', 'error');
    } finally {
        toggleLoading(false);
    }
}

/**
 * Renderiza la lista de vendedores
 */
function renderizarVendedores() {
    const lista = document.getElementById('vendedoresLista');
    const emptyState = document.getElementById('emptyState');
    
    if (vendedores.length === 0) {
        lista.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    lista.innerHTML = vendedores.map(vendedor => `
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="vendedor-card">
                <div class="vendedor-header">
                    <div class="vendedor-nombre">
                        ${vendedor.nombre} ${vendedor.apellido || ''}
                    </div>
                    ${vendedor.activo ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-secondary">Inactivo</span>'}
                </div>
                
                <div class="vendedor-info">
                    ${vendedor.email ? `<div><i class="fas fa-envelope"></i> ${vendedor.email}</div>` : ''}
                    ${vendedor.telefono ? `<div><i class="fas fa-phone"></i> ${vendedor.telefono}</div>` : ''}
                    ${vendedor.fecha_creacion ? `<div><i class="fas fa-calendar"></i> ${formatDate(vendedor.fecha_creacion)}</div>` : ''}
                </div>
                
                <div class="vendedor-actions">
                    <button class="btn-action btn-edit" onclick="editarVendedor(${vendedor.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn-action btn-delete" onclick="confirmarEliminar(${vendedor.id}, '${vendedor.nombre}')">
                        <i class="fas fa-trash"></i> Eliminar
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Muestra el modal para crear nuevo vendedor
 */
function mostrarModalNuevo() {
    document.getElementById('modalTitle').textContent = 'Nuevo Vendedor';
    document.getElementById('formVendedor').reset();
    document.getElementById('vendedorId').value = '';
    modalVendedor.show();
}

/**
 * Edita un vendedor existente
 */
function editarVendedor(id) {
    const vendedor = vendedores.find(v => v.id === id);
    
    if (!vendedor) {
        showToast('Vendedor no encontrado', 'error');
        return;
    }
    
    document.getElementById('modalTitle').textContent = 'Editar Vendedor';
    document.getElementById('vendedorId').value = vendedor.id;
    document.getElementById('nombre').value = vendedor.nombre;
    document.getElementById('apellido').value = vendedor.apellido || '';
    document.getElementById('email').value = vendedor.email || '';
    document.getElementById('telefono').value = vendedor.telefono || '';
    
    modalVendedor.show();
}

/**
 * Guarda un vendedor (crear o actualizar)
 */
async function guardarVendedor() {
    const vendedorId = document.getElementById('vendedorId').value;
    const nombre = document.getElementById('nombre').value.trim();
    const apellido = document.getElementById('apellido').value.trim();
    const email = document.getElementById('email').value.trim();
    const telefono = document.getElementById('telefono').value.trim();
    
    if (!nombre) {
        showToast('El nombre es requerido', 'error');
        return;
    }
    
    const vendedorData = {
        nombre,
        apellido,
        email,
        telefono
    };
    
    try {
        toggleLoading(true);
        
        let response;
        if (vendedorId) {
            // Actualizar
            response = await fetch(`/api/vendedores/${vendedorId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(vendedorData)
            });
        } else {
            // Crear nuevo
            response = await fetch('/api/vendedores', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(vendedorData)
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast(vendedorId ? 'Vendedor actualizado' : 'Vendedor creado', 'success');
            modalVendedor.hide();
            cargarVendedores();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al guardar vendedor', 'error');
    } finally {
        toggleLoading(false);
    }
}

/**
 * Confirma la eliminación de un vendedor
 */
function confirmarEliminar(id, nombre) {
    if (confirm(`¿Estás seguro de eliminar al vendedor "${nombre}"?\n\nEsta acción desactivará al vendedor pero mantendrá su historial.`)) {
        eliminarVendedor(id);
    }
}

/**
 * Elimina (desactiva) un vendedor
 */
async function eliminarVendedor(id) {
    try {
        toggleLoading(true);
        
        const response = await fetch(`/api/vendedores/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Vendedor desactivado', 'success');
            cargarVendedores();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar vendedor', 'error');
    } finally {
        toggleLoading(false);
    }
}

/**
 * Formatea una fecha
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
