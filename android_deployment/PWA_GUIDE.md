# Guía para Crear App Android - Sistema MiChaska

## Opción 1: PWA + Capacitor (RECOMENDADA)

### Ventajas:
- Reutiliza todo el código Python/Streamlit actual
- Acceso nativo a Bluetooth y impresoras
- Instalación como app nativa
- Funciona offline (con algunas modificaciones)

### Pasos:

#### 1. Preparar la App Web
```bash
# Instalar dependencias para PWA
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android
npm install @capacitor-community/bluetooth-le
npm install @awesome-cordova-plugins/bluetooth-serial
```

#### 2. Configurar Capacitor
```bash
npx cap init MiChaska com.michaska.pos
npx cap add android
```

#### 3. Crear manifest.json para PWA
```json
{
  "name": "MiChaska POS",
  "short_name": "MiChaska",
  "description": "Sistema de Punto de Venta",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0066cc",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

#### 4. Configurar capacitor.config.ts
```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.michaska.pos',
  appName: 'MiChaska POS',
  webDir: 'dist',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    BluetoothSerial: {
      requestPermission: true
    }
  }
};

export default config;
```

### 5. Integración con Impresoras ESC/POS
Agregar JavaScript para manejar impresión:

```javascript
// printer.js
class ESCPOSPrinter {
  constructor() {
    this.device = null;
  }

  async connectBluetooth() {
    try {
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ services: ['12345678-1234-1234-1234-123456789abc'] }]
      });
      this.device = device;
      return true;
    } catch (error) {
      console.error('Error conectando impresora:', error);
      return false;
    }
  }

  generateTicket(ventaData) {
    let commands = [];
    
    // Inicializar impresora
    commands.push([0x1B, 0x40]); // ESC @
    
    // Centrar texto
    commands.push([0x1B, 0x61, 0x01]); // ESC a 1
    
    // Título en negrita
    commands.push([0x1B, 0x45, 0x01]); // ESC E 1 (negrita ON)
    commands.push(...this.textToBytes("MICHASKA\n"));
    commands.push([0x1B, 0x45, 0x00]); // ESC E 0 (negrita OFF)
    
    // Línea separadora
    commands.push(...this.textToBytes("--------------------------------\n"));
    
    // Alinear a la izquierda
    commands.push([0x1B, 0x61, 0x00]); // ESC a 0
    
    // Datos de la venta
    commands.push(...this.textToBytes(`Ticket: ${ventaData.id}\n`));
    commands.push(...this.textToBytes(`Fecha: ${ventaData.fecha}\n`));
    commands.push(...this.textToBytes(`Vendedor: ${ventaData.vendedor}\n`));
    commands.push(...this.textToBytes("--------------------------------\n"));
    
    // Productos
    ventaData.productos.forEach(item => {
      commands.push(...this.textToBytes(`${item.nombre}\n`));
      commands.push(...this.textToBytes(`  ${item.cantidad} x $${item.precio} = $${item.subtotal}\n`));
    });
    
    commands.push(...this.textToBytes("--------------------------------\n"));
    
    // Total
    commands.push([0x1B, 0x45, 0x01]); // Negrita
    commands.push(...this.textToBytes(`TOTAL: $${ventaData.total}\n`));
    commands.push([0x1B, 0x45, 0x00]);
    
    // Método de pago
    commands.push(...this.textToBytes(`Método: ${ventaData.metodo_pago}\n`));
    
    // Espacios finales
    commands.push(...this.textToBytes("\n\n\n"));
    
    // Cortar papel
    commands.push([0x1D, 0x56, 0x42, 0x00]); // GS V B 0
    
    return new Uint8Array(commands.flat());
  }

  textToBytes(text) {
    return Array.from(new TextEncoder().encode(text));
  }

  async print(ventaData) {
    if (!this.device) {
      throw new Error('No hay impresora conectada');
    }

    const server = await this.device.gatt.connect();
    const service = await server.getPrimaryService('12345678-1234-1234-1234-123456789abc');
    const characteristic = await service.getCharacteristic('87654321-4321-4321-4321-cba987654321');
    
    const ticketData = this.generateTicket(ventaData);
    await characteristic.writeValue(ticketData);
  }
}
```
