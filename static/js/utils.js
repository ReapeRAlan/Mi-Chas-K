/**
 * Utilidades generales para MiChaska POS
 */

// Configuración axios
axios.defaults.headers.common['Content-Type'] = 'application/json';

/**
 * Muestra un toast de notificación
 */
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('mainToast');
    const toast = new bootstrap.Toast(toastEl);
    
    const toastBody = toastEl.querySelector('.toast-body');
    const toastHeader = toastEl.querySelector('.toast-header');
    
    // Remover clases previas
    toastHeader.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info', 'text-white');
    
    // Configurar según tipo
    const icons = {
        success: 'bi-check-circle-fill',
        error: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill'
    };
    
    const bgClasses = {
        success: 'bg-success text-white',
        error: 'bg-danger text-white',
        warning: 'bg-warning',
        info: 'bg-info'
    };
    
    const icon = toastHeader.querySelector('i');
    icon.className = `bi ${icons[type] || icons.info} me-2`;
    
    toastHeader.className = `toast-header ${bgClasses[type] || bgClasses.info}`;
    toastBody.textContent = message;
    
    toast.show();
}

/**
 * Muestra/oculta el spinner de carga
 */
function toggleLoading(show = true) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'flex' : 'none';
}

/**
 * Formatea un número como moneda
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

/**
 * Formatea una fecha
 */
function formatDate(date, includeTime = true) {
    const d = new Date(date);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        ...(includeTime && {
            hour: '2-digit',
            minute: '2-digit'
        })
    };
    return d.toLocaleDateString('es-MX', options);
}

/**
 * Maneja errores de API
 */
function handleApiError(error) {
    console.error('API Error:', error);
    
    let message = 'Ocurrió un error inesperado';
    
    if (error.response) {
        message = error.response.data.error || error.response.data.message || message;
    } else if (error.request) {
        message = 'No se pudo conectar con el servidor';
    } else {
        message = error.message;
    }
    
    showToast(message, 'error');
    toggleLoading(false);
    
    return message;
}

/**
 * Debounce function para optimizar búsquedas
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Valida un formulario
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    form.classList.add('was-validated');
    return form.checkValidity();
}

/**
 * Resetea la validación de un formulario
 */
function resetFormValidation(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.classList.remove('was-validated');
        form.reset();
    }
}

/**
 * Obtiene la ubicación del usuario
 */
function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocalización no soportada'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
            },
            (error) => {
                let message = 'Error obteniendo ubicación';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'Permiso de ubicación denegado';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Ubicación no disponible';
                        break;
                    case error.TIMEOUT:
                        message = 'Tiempo de espera agotado';
                        break;
                }
                reject(new Error(message));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
}

/**
 * Crea un mapa Leaflet
 */
function createMap(containerId, lat, lng, zoom = 15) {
    const map = L.map(containerId).setView([lat, lng], zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19
    }).addTo(map);
    
    return map;
}

/**
 * Agrega un marcador al mapa
 */
function addMapMarker(map, lat, lng, popup = null) {
    const marker = L.marker([lat, lng]).addTo(map);
    if (popup) {
        marker.bindPopup(popup);
    }
    return marker;
}

/**
 * Agrega un círculo al mapa (para radio de entrega)
 */
function addMapCircle(map, lat, lng, radiusKm, color = '#0d6efd') {
    const circle = L.circle([lat, lng], {
        color: color,
        fillColor: color,
        fillOpacity: 0.1,
        radius: radiusKm * 1000 // Convertir km a metros
    }).addTo(map);
    return circle;
}

/**
 * Genera un ID único
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Convierte base64 a blob
 */
function b64toBlob(b64Data, contentType = '', sliceSize = 512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);
        const byteNumbers = new Array(slice.length);
        
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: contentType });
}

/**
 * Descarga un archivo
 */
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Sanitiza HTML para prevenir XSS
 */
function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

/**
 * Trunca texto
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Verifica si está en modo móvil
 */
function isMobile() {
    return window.innerWidth <= 768;
}

/**
 * Verifica si está en modo tablet
 */
function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

// Event listeners globales
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar navbar en mobile al hacer click en un link
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (isMobile() && navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
});
