# 📱 Guía Completa: MiChaska Android App

## 🎯 Objetivo
Convertir tu sistema MiChaska a una aplicación Android nativa que pueda:
- ✅ Funcionar completamente offline
- ✅ Imprimir automáticamente en impresoras Bluetooth ESC/POS
- ✅ Optimizada para tablets
- ✅ Instalable como app nativa

## 🚀 Proceso de Implementación

### Paso 1: Configuración Inicial
```bash
cd /home/ghost/Escritorio/Mi-Chas-K/android_deployment
./setup_android.sh
```

### Paso 2: Personalización
1. **Iconos de la App:**
   - Crea iconos de 192x192 y 512x512 pixels
   - Guárdalos en `public/` como `icon-192.png` e `icon-512.png`

2. **Configuración de Impresora:**
   - La app buscará impresoras con UUID estándar ESC/POS
   - Compatible con la mayoría de impresoras térmicas Bluetooth

3. **Ajustar URL del Servidor:**
   - En `public/index.html`, cambia `streamlitUrl` por tu servidor
   - Para desarrollo local: `http://localhost:8501`
   - Para producción: `https://tu-servidor.com`

### Paso 3: Desarrollo y Pruebas

#### Prueba en Navegador (Desarrollo)
```bash
cd michaska-android
python -m http.server 8080
# Visita http://localhost:8080
```

#### Prueba en Android (Desarrollo)
```bash
npx cap run android
```

### Paso 4: Construcción para Producción

#### Crear APK de Desarrollo
```bash
npx cap sync
npx cap open android
# En Android Studio: Build > Build Bundle(s)/APK(s) > Build APK(s)
```

#### Crear APK Firmado (Producción)
```bash
# En Android Studio:
# Build > Generate Signed Bundle/APK
# Selecciona APK, crea keystore, firma
```

## 🔧 Configuración de Impresora

### Impresoras Compatibles
- Cualquier impresora térmica con Bluetooth
- Protocolo ESC/POS estándar
- Marcas populares: Epson, Star, Zebra, Bixolon

### Configuración Bluetooth
1. Emparejar impresora con la tablet desde Configuración Android
2. Abrir MiChaska app
3. Tocar "Conectar Impresora Bluetooth"
4. Seleccionar impresora de la lista
5. Probar con "Imprimir Prueba"

### Formato de Ticket
```
        MICHASKA
    Sistema de Punto de Venta
    ================================
    Ticket No: 12345
    Fecha: 2025-06-26 14:30:00
    Vendedor: Juan Pérez
    Método: Efectivo
    --------------------------------
    PRODUCTOS:
    Producto A
      2 x $50.00 = $100.00
    Producto B
      1 x $25.50 = $25.50
    --------------------------------
    TOTAL: $125.50
    
    ¡Gracias por su compra!
    Vuelva pronto
```

## 📱 Características de la App

### Funcionalidades Principales
- ✅ Punto de venta táctil optimizado
- ✅ Gestión de inventario
- ✅ Dashboard de ventas
- ✅ Impresión automática de tickets
- ✅ Funcionamiento offline
- ✅ Sincronización cuando hay internet

### Optimizaciones para Tablet
- **Botones grandes** para uso táctil
- **Layout adaptativo** para pantallas horizontales
- **Navegación simplificada** 
- **Controles de impresión** integrados
- **Estados visuales claros** (conectado/desconectado)

### Configuraciones de Impresión
- **Impresión automática:** Se imprime al completar venta
- **Impresión manual:** Botón para imprimir cuando se desee
- **Ticket de prueba:** Para verificar conexión
- **Estado de impresora:** Indicador visual de conexión

## 🔒 Permisos Android Necesarios

La app solicita estos permisos:
- `BLUETOOTH` - Para conectar impresoras
- `BLUETOOTH_ADMIN` - Para gestionar conexiones
- `ACCESS_COARSE_LOCATION` - Requerido para Bluetooth LE
- `ACCESS_FINE_LOCATION` - Requerido para Bluetooth LE
- `BLUETOOTH_CONNECT` - Android 12+
- `BLUETOOTH_SCAN` - Android 12+

## 🚀 Distribución

### Instalación Directa (APK)
1. Generar APK firmado
2. Transferir a tablet
3. Habilitar "Fuentes desconocidas"
4. Instalar APK

### Google Play Store (Opcional)
1. Crear cuenta de desarrollador
2. Preparar assets (iconos, screenshots)
3. Subir bundle firmado
4. Proceso de revisión (~3 días)

## 🛠️ Solución de Problemas

### Impresora No Conecta
1. Verificar que esté emparejada en Android
2. Reiniciar Bluetooth en tablet
3. Verificar que impresora esté en modo ESC/POS
4. Probar con otra app de impresión primero

### App No Carga
1. Verificar conexión a internet (si usa servidor remoto)
2. Comprobar URL del servidor en config
3. Revisar logs en Android Studio

### Problemas de Rendimiento
1. Cerrar otras apps para liberar memoria
2. Verificar que tablet tenga suficiente almacenamiento
3. Reiniciar app si está lenta

## 📞 Soporte Técnico

Para problemas específicos:
1. Revisar logs en Android Studio
2. Probar en navegador web primero
3. Verificar compatibilidad de impresora
4. Consultar documentación de Capacitor

---

**¡Tu sistema MiChaska está listo para tablets Android! 🎉**
