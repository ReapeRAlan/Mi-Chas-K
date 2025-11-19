# 🔄 Guía de Migración de Streamlit a Flask

Esta guía te ayudará a migrar de la versión anterior (Streamlit) a la nueva versión moderna (Flask + Bootstrap).

## 📋 Resumen de Cambios

### Tecnología Anterior
- **Framework**: Streamlit
- **UI**: Componentes de Streamlit
- **Arquitectura**: Aplicación monolítica
- **Despliegue**: Limitado a servidor Streamlit

### Tecnología Nueva
- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5 + JavaScript vanilla
- **Arquitectura**: API REST
- **Despliegue**: Flexible (Render, Heroku, AWS, etc.)

## ✨ Nuevas Características

1. **🗺️ Sistema de Entregas Locales**
   - Validación de ubicación GPS
   - Radio de entrega de 10km
   - Visualización en mapas interactivos

2. **🎨 Interfaz Moderna**
   - Diseño responsive 100%
   - Optimizado para tablets y móviles
   - Mejor experiencia de usuario (UX/UI)

3. **⚡ Rendimiento**
   - Carga más rápida
   - API REST eficiente
   - Mejor manejo de recursos

## 🚀 Pasos de Migración

### 1. Backup de Datos Actual

**IMPORTANTE**: Antes de migrar, haz backup de tu base de datos PostgreSQL:

```bash
pg_dump -U admin -d chaskabd > backup_antes_migracion.sql
```

### 2. Ejecutar Migración de Base de Datos

La migración SQL agregará la tabla de entregas y optimizará índices:

```bash
psql -U admin -d chaskabd -f database/migration_to_flask.sql
```

### 3. Actualizar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp .env.example .env
```

Edita `.env` con:
- Credenciales de PostgreSQL
- Ubicación del negocio (lat/lng)
- Secret key para Flask

### 5. Probar Localmente

```bash
# Windows
start_dev.bat

# Linux/Mac
chmod +x start_dev.sh
./start_dev.sh
```

Abre http://localhost:5000

### 6. Verificar Funcionalidades

- ✅ Login a base de datos PostgreSQL
- ✅ Listado de productos
- ✅ Creación de ventas
- ✅ Dashboard de estadísticas
- ✅ Sistema de entregas (nueva)

## 📊 Migración de Datos

### Compatibilidad con Datos Existentes

✅ **100% Compatible** - La nueva versión usa las mismas tablas:
- `productos`
- `categorias`
- `ventas`
- `detalle_ventas`
- `gastos_diarios`
- `cortes_caja`
- `vendedores`

🆕 **Tabla Nueva**:
- `entregas` - Para gestionar entregas locales

### Datos NO Migrados

Si usabas SQLite local antes, necesitas migrar manualmente a PostgreSQL:

```bash
# Exportar datos de SQLite (si aplica)
sqlite3 database.db .dump > sqlite_export.sql

# Convertir a PostgreSQL
# (requiere ajustes manuales de sintaxis)
```

## 🔧 Configuración Post-Migración

### 1. Ubicación del Negocio

Configura la ubicación exacta para el sistema de entregas:

```env
BUSINESS_LAT=19.4326  # Tu latitud
BUSINESS_LNG=-99.1332 # Tu longitud
```

Puedes obtener estas coordenadas desde Google Maps:
1. Busca tu dirección en maps.google.com
2. Click derecho → "¿Qué hay aquí?"
3. Copia las coordenadas que aparecen

### 2. Radio de Entrega

Edita `server.py` si necesitas cambiar el radio:

```python
RADIO_ENTREGA_KM = 10  # Cambiar según necesidad
```

### 3. Personalizar Colores/Estilos

Edita `static/css/main.css`:

```css
:root {
    --primary-color: #0d6efd;  /* Color principal */
    --success-color: #198754;  /* Color de éxito */
    /* ... más colores */
}
```

## 🌐 Despliegue en Producción

### Render.com (Recomendado)

1. **Conectar repositorio** en Render Dashboard
2. **Seleccionar** el archivo `render.yaml`
3. **Configurar** variables de entorno
4. **Desplegar**

Render detectará automáticamente:
- Build command
- Start command
- Python runtime

### Variables de Entorno Críticas

```
FLASK_ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=tu-clave-secreta-segura
BUSINESS_LAT=19.4326
BUSINESS_LNG=-99.1332
```

## 🆘 Solución de Problemas

### Error: "No se puede conectar a la base de datos"

**Solución**:
```bash
# Verificar conexión
psql -U admin -d chaskabd -h dpg-xxx.oregon-postgres.render.com

# Verificar variables de entorno
echo $DATABASE_URL
```

### Error: "Tabla 'entregas' no existe"

**Solución**:
```bash
# Ejecutar migración
psql -U admin -d chaskabd -f database/migration_to_flask.sql
```

### Error: "Módulo no encontrado"

**Solución**:
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Problemas con Geolocalización

**Solución**:
- Asegúrate de usar HTTPS en producción
- Los navegadores solo permiten geolocalización en conexiones seguras
- Render proporciona HTTPS automáticamente

## 📱 Diferencias en Uso

### Antes (Streamlit)

```python
# Código Streamlit
st.button("Agregar al carrito")
st.selectbox("Categoría", categorias)
```

### Ahora (Flask)

```javascript
// Frontend JavaScript
<button onclick="agregarAlCarrito(productoId)">
document.getElementById('categoria').value
```

## ✅ Checklist Post-Migración

- [ ] Base de datos migrada exitosamente
- [ ] Todas las ventas anteriores visibles
- [ ] Productos cargados correctamente
- [ ] Sistema de entregas funcionando
- [ ] Generación de PDFs operativa
- [ ] Dashboard mostrando estadísticas
- [ ] Aplicación desplegada en producción
- [ ] Variables de entorno configuradas
- [ ] Backup de datos realizado
- [ ] Team capacitado en nueva interfaz

## 🎓 Capacitación del Equipo

### Cambios Clave para Usuarios

1. **Interfaz más intuitiva**: Botones más grandes, diseño más limpio
2. **Entregas locales**: Nueva opción en punto de venta
3. **Mapas interactivos**: Visualización de ubicaciones
4. **Más rápido**: Carga instantánea de páginas

### Videos de Capacitación (Recomendado)

- Grabar video de 5 minutos mostrando:
  - Nuevo punto de venta
  - Cómo procesar entrega local
  - Gestión de órdenes
  - Dashboard actualizado

## 📞 Soporte

Si tienes problemas durante la migración:

1. Revisa los logs: `gunicorn.log` o consola del servidor
2. Verifica la conexión a PostgreSQL
3. Consulta la documentación en `README_NEW.md`
4. Abre un issue en GitHub

## 🔄 Rollback (Por si acaso)

Si necesitas volver a la versión anterior:

1. Restaura el backup de la base de datos:
```bash
psql -U admin -d chaskabd < backup_antes_migracion.sql
```

2. Cambia el branch de Git:
```bash
git checkout anterior-version
```

3. Despliega la versión anterior en Render

---

**¡Éxito en tu migración! 🎉**

La nueva versión te brindará una mejor experiencia, mayor flexibilidad y nuevas capacidades para tu negocio.
