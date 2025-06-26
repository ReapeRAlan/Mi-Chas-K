# Lista de Impresoras Bluetooth ESC/POS Compatibles

## ✅ Impresoras Térmicas Recomendadas

### Gama Económica ($50-$150 USD)
1. **MUNBYN ITPP941**
   - 58mm, Bluetooth + USB
   - Velocidad: 90mm/s
   - Compatible Android/iOS
   - Muy popular para POS

2. **Rongta RPP02N**
   - 58mm, Bluetooth 4.0
   - Batería recargable
   - Económica y confiable

3. **NETUM NT-1809DD**
   - 58mm, Bluetooth + USB
   - Compatible con ESC/POS
   - Buena relación precio/calidad

### Gama Media ($150-$300 USD)
1. **Epson TM-P20**
   - 58mm, Bluetooth + WiFi
   - Batería larga duración
   - Excelente calidad de impresión

2. **Star Micronics SM-L200**
   - 58mm, Bluetooth + USB
   - Muy robusta
   - Amplia compatibilidad

3. **Bixolon SPP-R200III**
   - 58mm, Bluetooth + WiFi
   - Resistente al agua
   - Ideal para uso intensivo

### Gama Alta ($300+ USD)
1. **Epson TM-P80**
   - 80mm, Bluetooth + WiFi + Ethernet
   - Alta velocidad
   - Uso profesional intensivo

2. **Star Micronics TSP143IIIBI**
   - 80mm, Bluetooth + USB
   - Muy rápida
   - Excelente para restaurantes

## 🔧 Configuración por Marca

### Epson (TM-P20, TM-P80)
```javascript
// UUID específicos Epson
const EPSON_SERVICE = '18f0';
const EPSON_WRITE = '2af1';

// Configuración en printer.js
const epsomConfig = {
  serviceUUID: '18f0',
  characteristicUUID: '2af1',
  baudRate: 115200
};
```

### Star Micronics
```javascript
// UUID Star Micronics
const STAR_SERVICE = '00001101-0000-1000-8000-00805f9b34fb';
const STAR_WRITE = '00001101-0000-1000-8000-00805f9b34fb';
```

### Genéricas (MUNBYN, NETUM, etc.)
```javascript
// UUID estándar ESC/POS
const STANDARD_SERVICE = '0000ff00-0000-1000-8000-00805f9b34fb';
const STANDARD_WRITE = '0000ff02-0000-1000-8000-00805f9b34fb';
```

## 📋 Comandos ESC/POS por Impresora

### Comandos Universales (Funcionan en todas)
```javascript
// Inicializar
ESC @ (0x1B, 0x40)

// Texto normal
Texto + LF (0x0A)

// Cortar papel
GS V B 0 (0x1D, 0x56, 0x42, 0x00)

// Alineación
ESC a 0/1/2 (0x1B, 0x61, 0x00/0x01/0x02)
```

### Comandos Específicos por Marca

#### Epson
```javascript
// Doble altura/ancho
GS ! 0x11 (0x1D, 0x21, 0x11)

// Negrita
ESC E 1 (0x1B, 0x45, 0x01)

// Subrayado
ESC - 1 (0x1B, 0x2D, 0x01)
```

#### Star Micronics
```javascript
// Enfasis
ESC E (0x1B, 0x45)

// Doble ancho
ESC W 1 (0x1B, 0x57, 0x01)

// Corte parcial
ESC d 3 (0x1B, 0x64, 0x03)
```

## 🛒 Dónde Comprar

### Online (Internacional)
- **Amazon** - Amplia selección, envío rápido
- **AliExpress** - Precios económicos, envío lento
- **eBay** - Nuevas y usadas

### Distribuidores Especializados
- **POS Supply** - Especialista en equipos POS
- **Barcodes Inc** - Amplio catálogo
- **IDAutomation** - Soporte técnico incluido

### Tiendas Locales (México/Latinoamérica)
- **Mercado Libre** - Variedad local
- **Linio** - Envío rápido
- **Tiendas de POS locales** - Soporte presencial

## ⚡ Configuración Rápida por Modelo

### MUNBYN ITPP941 (Más Popular)
1. Emparejar: Mantener botón power 3 segundos
2. LED azul parpadeante = modo pairing
3. UUID: `0000ff00-0000-1000-8000-00805f9b34fb`
4. Ancho papel: 58mm (384 puntos)

### Epson TM-P20
1. Emparejar: Menu > Bluetooth > Pairing
2. PIN: 0000 (si solicita)
3. UUID: `18f0` / `2af1`
4. Configurar en app Epson primero

### Star SM-L200
1. Emparejar: Botón Bluetooth 3 segundos
2. UUID estándar SPP
3. Muy estable, raramente se desconecta

## 🔍 Verificar Compatibilidad

### Antes de Comprar
✅ **Debe tener:** Bluetooth  
✅ **Debe soportar:** ESC/POS  
✅ **Ancho recomendado:** 58mm o 80mm  
✅ **Tipo de papel:** Térmico  
❌ **Evitar:** Solo WiFi (sin Bluetooth)  
❌ **Evitar:** Protocolos propietarios  

### Prueba de Compatibilidad
1. Descargar app "Bluetooth Terminal"
2. Conectar a impresora
3. Enviar comando: `1B 40` (ESC @)
4. Si responde = Compatible

## 💡 Consejos de Uso

### Optimizar Duración de Papel
- Usar logo pequeño o solo texto
- Reducir espacios entre líneas
- Ticket compacto pero legible

### Mantener Conexión Estable
- Mantener tablet cerca de impresora (< 5 metros)
- Evitar interferencias WiFi
- Cargar impresora regularmente

### Solución de Problemas Comunes
1. **No imprime:** Verificar papel térmico
2. **Cortes parciales:** Revisar configuración de corte
3. **Texto borroso:** Limpiar cabezal térmico
4. **Se desconecta:** Verificar batería impresora

---

**Recomendación:** Para empezar, la **MUNBYN ITPP941** ofrece la mejor relación calidad-precio y compatibilidad garantizada con el código que hemos desarrollado.
