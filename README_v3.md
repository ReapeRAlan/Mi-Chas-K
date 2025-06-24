# Mi Chas-K v3.0.0 - Sistema Híbrido

## 🚀 Características Principales

### ✅ **MODO HÍBRIDO**
- **Funciona OFFLINE**: Base de datos SQLite local
- **Sincronización automática**: Se conecta a la nube cuando hay internet
- **Instalación automática**: Un solo archivo instala todo en Windows

### ✅ **FUNCIONALIDADES COMPLETAS**
- 🛒 **Punto de Venta**: Sistema simplificado y rápido
- 📦 **Inventario**: Gestión de productos y categorías  
- 📊 **Dashboard**: Reportes y estadísticas en tiempo real
- ⚙️ **Configuración**: Estado de sincronización y mantenimiento

### ✅ **NUEVA ARQUITECTURA**
- **Conexión inteligente**: Remoto preferido, local como respaldo
- **Cola de sincronización**: Cambios se guardan y sincronizan después
- **Verificación automática**: Chequeo de conectividad cada 30 segundos
- **Interfaz mejorada**: Diseño moderno y funcional

---

## 🔧 Instalación en Windows

### **Opción 1: Instalación Automática (Recomendada)**

1. **Descargar** el instalador:
   ```
   https://github.com/ReapeRAlan/Mi-Chas-K/raw/main/install_windows.bat
   ```

2. **Ejecutar** como administrador:
   - Clic derecho → "Ejecutar como administrador"
   - El script instalará Python si es necesario

3. **Configurar** base de datos:
   - Edita el archivo `.env` que se abre automáticamente
   - Agrega tu `DATABASE_URL` de Render

4. **Iniciar** el sistema:
   - Doble clic en `menu.bat`
   - Selecciona "1. Iniciar Sistema"

### **Opción 2: Instalación Manual**

```bash
# 1. Instalar Python 3.9+ desde python.org
# 2. Clonar repositorio
git clone https://github.com/ReapeRAlan/Mi-Chas-K.git
cd Mi-Chas-K

# 3. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements_simple.txt

# 5. Configurar variables de entorno
# Editar .env con tu DATABASE_URL

# 6. Iniciar sistema
streamlit run app_hybrid.py
```

---

## ⚙️ Configuración

### **Variables de Entorno (.env)**

```env
# Base de datos remota (Render)
DATABASE_URL=postgresql://usuario:password@host:5432/database

# Configuración local (alternativa)
DB_HOST=localhost
DB_NAME=chaskabd
DB_USER=admin
DB_PASSWORD=tu_password
DB_PORT=5432
```

### **Estructura del Proyecto**

```
Mi-Chas-K/
├── app_hybrid.py                 # Aplicación principal
├── database/
│   └── connection_hybrid.py      # Sistema híbrido de BD
├── pages/
│   ├── punto_venta_simple.py     # POS simplificado
│   ├── inventario_simple.py      # Gestión de productos
│   ├── dashboard_simple.py       # Reportes y métricas
│   └── configuracion_simple.py   # Configuración del sistema
├── data/
│   ├── local_database.db         # BD local SQLite
│   └── sync_queue.json          # Cola de sincronización
├── requirements_simple.txt       # Dependencias Python
├── install_windows.bat          # Instalador automático
├── menu.bat                     # Menú de opciones
└── iniciar.bat                  # Inicio directo
```

---

## 📱 Uso del Sistema

### **1. 🛒 Punto de Venta**
- **Grid visual** de productos disponibles
- **Carrito intuitivo** con cantidad y subtotales
- **Finalización rápida** con vendedor y método de pago
- **Actualización automática** de stock

### **2. 📦 Inventario**
- **Lista completa** de productos con stock
- **Agregar productos** con categorías
- **Actualizar stock** en tiempo real
- **Gestión de categorías**

### **3. 📊 Dashboard**
- **Métricas del día**: Ventas e ingresos
- **Productos top**: Más vendidos
- **Ventas recientes**: Historial
- **Métodos de pago**: Distribución
- **Exportar reportes**: CSV descargable

### **4. ⚙️ Configuración**
- **Estado de sincronización**: Online/Offline
- **Cola de sincronización**: Elementos pendientes
- **Gestión de vendedores**: Agregar/ver
- **Estadísticas de BD**: Contadores de tablas
- **Mantenimiento**: Limpieza y verificación

---

## 🔄 Sistema de Sincronización

### **Cómo Funciona**

1. **Operación local**: Todos los cambios se guardan en SQLite
2. **Cola de sincronización**: Cambios se agregan a una cola
3. **Verificación automática**: Cada 30 segundos chequea conectividad
4. **Sincronización automática**: Envía cambios pendientes a la nube
5. **Reintento automático**: Hasta 3 intentos por operación fallida

### **Estados del Sistema**

- 🟢 **Online**: Conectado a la nube, cambios directos
- 🟡 **Offline**: Modo local, cambios en cola
- 🔄 **Sincronizando**: Enviando cambios pendientes

### **Ventajas**

- ✅ **Funciona sin internet**
- ✅ **No pierde datos**
- ✅ **Sincronización transparente**
- ✅ **Rendimiento óptimo**

---

## 🛠️ Solución de Problemas

### **Problema: No inicia el sistema**
```bash
# Verificar Python
python --version

# Verificar dependencias
pip list

# Reinstalar dependencias
pip install -r requirements_simple.txt
```

### **Problema: Error de base de datos**
```bash
# Verificar archivo .env
notepad .env

# Probar conexión
python -c "from database.connection_hybrid import db_hybrid; print(db_hybrid.get_sync_status())"
```

### **Problema: No sincroniza**
```bash
# Verificar internet
ping google.com

# Forzar sincronización
# Usar la opción en Configuración → Sincronizar Ahora
```

### **Problema: Datos perdidos**
```bash
# Los datos locales están en:
data/local_database.db

# Verificar integridad
# Usar Configuración → Verificar Integridad
```

---

## 📈 Mejoras de la v3.0.0

### **🔄 Sistema Híbrido**
- Conexión inteligente local/remoto
- Sincronización automática en segundo plano
- Cola de operaciones pendientes
- Verificación de conectividad

### **🎨 Interfaz Renovada**
- Diseño moderno y limpio
- Navegación simplificada
- Indicadores de estado claros
- Métricas visuales mejoradas

### **⚡ Rendimiento Optimizado**
- Consultas más eficientes
- Menos llamadas a base de datos
- Carga asíncrona de datos
- Logging inteligente

### **🔧 Instalación Simplificada**
- Instalador automático para Windows
- Configuración guiada
- Menú de opciones integrado
- Detección automática de dependencias

### **📊 Dashboard Mejorado**
- Métricas en tiempo real
- Reportes exportables
- Gráficos intuitivos
- Historial de ventas

---

## 🔮 Próximas Mejoras

- 📱 **App móvil** para vendedores
- 🧾 **Generación de facturas** PDF
- 📊 **Gráficos avanzados** con Plotly
- 👥 **Gestión de clientes** frecuentes
- 🏪 **Multi-tienda** soporte
- 🔔 **Notificaciones** push
- 📦 **Control de stock** avanzado
- 💰 **Caja chica** integrada

---

## 📞 Soporte

- **GitHub**: https://github.com/ReapeRAlan/Mi-Chas-K
- **Issues**: https://github.com/ReapeRAlan/Mi-Chas-K/issues
- **Documentación**: README.md del repositorio

---

**Mi Chas-K v3.0.0** - Sistema de Punto de Venta Híbrido  
*Desarrollado con ❤️ para pequeños negocios*
