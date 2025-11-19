# 🧪 Guía de Testing - MiChaska POS

Esta guía te ayudará a probar todas las funcionalidades del sistema antes y después del despliegue.

## 📋 Checklist de Testing

### ✅ 1. Testing Local (Antes de Deploy)

#### Backend / API
- [ ] **Health Check**
  ```bash
  curl http://localhost:5000/api/health
  # Debe retornar: {"success": true, "status": "healthy"}
  ```

- [ ] **Listar Productos**
  ```bash
  curl http://localhost:5000/api/productos
  # Debe retornar array de productos
  ```

- [ ] **Listar Categorías**
  ```bash
  curl http://localhost:5000/api/categorias
  # Debe retornar array de categorías
  ```

- [ ] **Estadísticas de Ventas**
  ```bash
  curl "http://localhost:5000/api/estadisticas/ventas?fecha_inicio=2024-01-01&fecha_fin=2024-12-31"
  ```

#### Frontend / UI
- [ ] **Página Principal** (http://localhost:5000)
  - Cards de navegación visibles
  - Links funcionando
  - Responsive en diferentes tamaños

- [ ] **Punto de Venta** (http://localhost:5000/pos)
  - Grid de productos carga correctamente
  - Filtro por categoría funciona
  - Búsqueda de productos funciona
  - Agregar al carrito funciona
  - Carrito muestra items correctos
  - Total se calcula bien
  - Procesamiento de venta exitoso

- [ ] **Dashboard** (http://localhost:5000/dashboard)
  - Estadísticas cargan
  - Últimas ventas visibles
  - Productos top mostrados
  - Sin errores en consola

- [ ] **Inventario** (http://localhost:5000/inventario)
  - Tabla de productos carga
  - Modal de crear producto funciona
  - Editar producto funciona
  - Eliminar producto funciona

- [ ] **Órdenes** (http://localhost:5000/ordenes)
  - Lista de entregas carga (puede estar vacía)
  - Filtros funcionan
  - Estados se actualizan

### ✅ 2. Testing de Geolocalización

#### Configuración Previa
1. Asegúrate de estar en HTTPS o localhost
2. Navegador con permisos de ubicación habilitados

#### Tests
- [ ] **Activar Entrega**
  1. Ir a Punto de Venta
  2. Agregar producto al carrito
  3. Activar checkbox "Entrega a domicilio"
  4. Panel de dirección debe aparecer

- [ ] **Obtener Ubicación**
  1. Click en "Usar mi ubicación"
  2. Permitir acceso a ubicación
  3. Debe mostrar estado de validación
  4. Mapa debe aparecer si está dentro del radio

- [ ] **Validar Radio de Entrega**
  - Si estás dentro de 10km: Estado verde ✅
  - Si estás fuera de 10km: Estado rojo ❌
  - Distancia calculada correcta

- [ ] **Procesamiento con Entrega**
  1. Activar entrega y validar ubicación
  2. Ingresar dirección
  3. Seleccionar vendedor
  4. Procesar venta
  5. Verificar venta en Dashboard
  6. Verificar entrega en Órdenes

### ✅ 3. Testing de Responsiveness

#### Desktop (1920x1080)
- [ ] Navbar completa visible
- [ ] Grid de productos en 4 columnas
- [ ] Carrito en sidebar
- [ ] Todas las funcionalidades accesibles

#### Tablet (768x1024)
- [ ] Navbar colapsa a hamburger
- [ ] Grid de productos en 2-3 columnas
- [ ] Botones tamaño adecuado
- [ ] Inputs grandes para touch

#### Móvil (375x667)
- [ ] Una columna de productos
- [ ] Botones grandes
- [ ] Carrito ocupa full width
- [ ] Navbar responsive

### ✅ 4. Testing de Base de Datos

```sql
-- Verificar tabla de entregas existe
SELECT * FROM entregas LIMIT 1;

-- Verificar índices
SELECT indexname FROM pg_indexes WHERE tablename = 'entregas';

-- Verificar categorías
SELECT * FROM categorias;

-- Verificar productos
SELECT COUNT(*) FROM productos;

-- Verificar ventas del día
SELECT * FROM ventas WHERE DATE(fecha) = CURRENT_DATE;
```

### ✅ 5. Testing Post-Deploy (Producción)

#### Health Check Remoto
```bash
curl https://tu-app.onrender.com/api/health
```

#### HTTPS Verificación
- [ ] URL usa HTTPS (candado verde)
- [ ] Certificado válido
- [ ] No hay warnings de seguridad

#### Geolocalización en Producción
- [ ] Navegador pide permiso de ubicación
- [ ] Ubicación se obtiene correctamente
- [ ] Mapa carga sin errores

#### Performance
- [ ] Página principal carga < 2 segundos
- [ ] API responde < 500ms
- [ ] Sin errores 500 en logs

### ✅ 6. Testing de Flujos Completos

#### Flujo 1: Venta Simple
1. [ ] Ir a Punto de Venta
2. [ ] Seleccionar categoría
3. [ ] Agregar 3 productos al carrito
4. [ ] Verificar total correcto
5. [ ] Seleccionar vendedor
6. [ ] Elegir método de pago
7. [ ] Procesar venta
8. [ ] Ver modal de éxito
9. [ ] Descargar ticket PDF
10. [ ] Verificar en Dashboard

#### Flujo 2: Venta con Entrega
1. [ ] Agregar productos al carrito
2. [ ] Activar "Entrega a domicilio"
3. [ ] Usar ubicación GPS
4. [ ] Verificar dentro de radio
5. [ ] Ingresar dirección completa
6. [ ] Ver mapa con ruta
7. [ ] Procesar venta
8. [ ] Verificar en Órdenes
9. [ ] Cambiar estado a "En Camino"
10. [ ] Cambiar estado a "Entregado"

#### Flujo 3: Gestión de Inventario
1. [ ] Ir a Inventario
2. [ ] Crear nuevo producto
3. [ ] Editar producto existente
4. [ ] Verificar cambios en Punto de Venta
5. [ ] Procesar venta (stock debe disminuir)
6. [ ] Verificar stock actualizado

### ✅ 7. Testing de Errores

#### Manejo de Errores API
- [ ] Producto inexistente
  ```bash
  curl http://localhost:5000/api/productos/99999
  # Debe retornar 404
  ```

- [ ] Entrega fuera de radio
  - Simular ubicación lejana (>10km)
  - Debe mostrar error y no permitir venta

- [ ] Sin stock
  - Intentar vender producto sin stock
  - Debe mostrar error

- [ ] Campos vacíos
  - Intentar crear producto sin nombre
  - Debe validar y mostrar error

#### Manejo de Errores UI
- [ ] Sin conexión a internet
  - Desconectar red
  - Debe mostrar error amigable

- [ ] Base de datos caída
  - Simular error de BD
  - Debe mostrar mensaje apropiado

### ✅ 8. Testing de Seguridad

- [ ] **SQL Injection**
  - Intentar inyectar SQL en búsqueda
  - Debe sanitizar correctamente

- [ ] **XSS**
  - Intentar inyectar `<script>` en campos
  - Debe escapar HTML

- [ ] **CORS**
  ```bash
  curl -H "Origin: http://malicious.com" http://localhost:5000/api/productos
  # Debe permitir solo si CORS configurado
  ```

### ✅ 9. Testing de Compatibilidad

#### Navegadores
- [ ] Chrome (último)
- [ ] Firefox (último)
- [ ] Safari (último)
- [ ] Edge (último)
- [ ] Chrome Mobile
- [ ] Safari Mobile

#### Sistemas Operativos
- [ ] Windows 10/11
- [ ] macOS
- [ ] Linux (Ubuntu)
- [ ] Android
- [ ] iOS

### ✅ 10. Testing de PDFs

- [ ] Ticket se genera correctamente
- [ ] PDF se descarga sin errores
- [ ] Contenido del PDF es correcto:
  - Datos del negocio
  - Productos vendidos
  - Total correcto
  - Fecha/hora
  - Método de pago

## 🐛 Reporte de Bugs

Si encuentras un error, documenta:

```markdown
### Bug: [Título descriptivo]

**Severidad**: Alta / Media / Baja

**Descripción**:
Descripción clara del problema

**Pasos para reproducir**:
1. Paso 1
2. Paso 2
3. Paso 3

**Resultado esperado**:
Qué debería pasar

**Resultado actual**:
Qué está pasando

**Screenshots**:
(Si aplica)

**Entorno**:
- Navegador: Chrome 120
- OS: Windows 11
- URL: https://...
```

## 📊 Métricas de Éxito

### Performance
- [ ] Carga inicial < 2s
- [ ] Time to Interactive < 3s
- [ ] API response < 500ms
- [ ] Sin errores en consola

### Funcionalidad
- [ ] 100% de funcionalidades trabajando
- [ ] Todas las páginas accesibles
- [ ] Sin errores críticos
- [ ] Geolocalización funcional

### UX/UI
- [ ] Navegación intuitiva
- [ ] Diseño consistente
- [ ] Responsive en todos los dispositivos
- [ ] Feedback visual apropiado

## 🎯 Test de Aceptación

### Criterios Mínimos para Producción

1. **Funcionalidad Core** ✅
   - Ventas se procesan correctamente
   - Stock se actualiza
   - PDFs se generan

2. **Entregas Locales** ✅
   - Geolocalización funciona
   - Validación de radio correcta
   - Estados se actualizan

3. **Estabilidad** ✅
   - No hay errores 500
   - BD responde correctamente
   - Sin memory leaks

4. **Seguridad** ✅
   - HTTPS en producción
   - Datos sanitizados
   - Variables sensibles protegidas

---

## 🚀 Comandos Útiles

### Testing Local
```bash
# Verificar Python
python --version

# Verificar dependencias
pip list

# Ejecutar servidor
python server.py

# Probar API
curl http://localhost:5000/api/health
```

### Testing Base de Datos
```bash
# Conectar a PostgreSQL
psql -U admin -d chaskabd -h localhost

# Ver tablas
\dt

# Verificar entregas
SELECT COUNT(*) FROM entregas;

# Ver últimas ventas
SELECT * FROM ventas ORDER BY fecha DESC LIMIT 5;
```

### Logs de Producción (Render)
```bash
# Ver logs en tiempo real
render logs --tail

# Descargar logs
render logs > app.log
```

---

**¡Buena suerte con el testing! 🧪**

Si todos los tests pasan, el sistema está listo para producción.
