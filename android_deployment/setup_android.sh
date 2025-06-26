#!/bin/bash

# Script de configuración para App Android MiChaska
# Opción PWA + Capacitor

echo "🚀 Configurando MiChaska para Android..."

# Crear directorio del proyecto
mkdir -p michaska-android
cd michaska-android

# Inicializar proyecto Node.js
echo "📦 Inicializando proyecto..."
npm init -y

# Instalar Capacitor
echo "⚡ Instalando Capacitor..."
npm install @capacitor/core @capacitor/cli @capacitor/android

# Instalar plugins para Bluetooth
echo "📶 Instalando plugins Bluetooth..."
npm install @capacitor-community/bluetooth-le
npm install @awesome-cordova-plugins/bluetooth-serial

# Inicializar Capacitor
echo "🔧 Configurando Capacitor..."
npx cap init MiChaska com.michaska.pos

# Agregar plataforma Android
echo "📱 Agregando plataforma Android..."
npx cap add android

# Crear estructura de archivos
echo "📁 Creando estructura de archivos..."
mkdir -p src/{components,services,assets}
mkdir -p public

# Crear archivo de configuración PWA
cat > public/manifest.json << 'EOF'
{
  "name": "MiChaska POS",
  "short_name": "MiChaska",
  "description": "Sistema de Punto de Venta MiChaska",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0066cc",
  "orientation": "landscape",
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
  ],
  "categories": ["business", "productivity"],
  "shortcuts": [
    {
      "name": "Nueva Venta",
      "short_name": "Venta",
      "description": "Iniciar nueva venta",
      "url": "/punto-venta",
      "icons": [{ "src": "shortcut-venta.png", "sizes": "96x96" }]
    },
    {
      "name": "Inventario",
      "short_name": "Stock",
      "description": "Ver inventario",
      "url": "/inventario",
      "icons": [{ "src": "shortcut-inventario.png", "sizes": "96x96" }]
    }
  ]
}
EOF

# Crear configuración de Capacitor
cat > capacitor.config.ts << 'EOF'
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.michaska.pos',
  appName: 'MiChaska POS',
  webDir: 'dist',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    BluetoothLe: {
      displayStrings: {
        scanning: "Buscando impresoras...",
        cancel: "Cancelar",
        availableDevices: "Dispositivos disponibles",
        noDeviceFound: "No se encontraron dispositivos"
      }
    },
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#0066cc",
      showSpinner: true,
      spinnerColor: "#ffffff"
    }
  },
  android: {
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: true
  }
};

export default config;
EOF

# Crear servicio de impresora
cat > src/services/printer.js << 'EOF'
class ESCPOSPrinter {
  constructor() {
    this.device = null;
    this.isConnected = false;
  }

  async connectBluetooth() {
    try {
      // Solicitar dispositivo Bluetooth
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['0000ff00-0000-1000-8000-00805f9b34fb']
      });

      this.device = device;
      
      // Conectar al GATT server
      const server = await device.gatt.connect();
      this.server = server;
      this.isConnected = true;
      
      console.log('Impresora conectada:', device.name);
      return true;
    } catch (error) {
      console.error('Error conectando impresora:', error);
      this.isConnected = false;
      return false;
    }
  }

  async disconnect() {
    if (this.device && this.device.gatt.connected) {
      await this.device.gatt.disconnect();
      this.isConnected = false;
    }
  }

  // Comandos ESC/POS
  ESC = 0x1B;
  GS = 0x1D;
  
  // Comandos básicos
  INIT = [this.ESC, 0x40];
  CUT = [this.GS, 0x56, 0x42, 0x00];
  
  // Alineación
  ALIGN_LEFT = [this.ESC, 0x61, 0x00];
  ALIGN_CENTER = [this.ESC, 0x61, 0x01];
  ALIGN_RIGHT = [this.ESC, 0x61, 0x02];
  
  // Texto
  BOLD_ON = [this.ESC, 0x45, 0x01];
  BOLD_OFF = [this.ESC, 0x45, 0x00];
  
  // Tamaño
  SIZE_NORMAL = [this.GS, 0x21, 0x00];
  SIZE_DOUBLE = [this.GS, 0x21, 0x11];

  textToBytes(text) {
    return Array.from(new TextEncoder().encode(text));
  }

  generateTicket(ventaData) {
    let commands = [];
    
    // Inicializar
    commands.push(...this.INIT);
    
    // Encabezado centrado
    commands.push(...this.ALIGN_CENTER);
    commands.push(...this.BOLD_ON);
    commands.push(...this.SIZE_DOUBLE);
    commands.push(...this.textToBytes("MICHASKA\n"));
    commands.push(...this.SIZE_NORMAL);
    commands.push(...this.BOLD_OFF);
    
    commands.push(...this.textToBytes("Sistema de Punto de Venta\n"));
    commands.push(...this.textToBytes("================================\n"));
    
    // Información de la venta - izquierda
    commands.push(...this.ALIGN_LEFT);
    commands.push(...this.textToBytes(`Ticket No: ${ventaData.id}\n`));
    commands.push(...this.textToBytes(`Fecha: ${ventaData.fecha}\n`));
    commands.push(...this.textToBytes(`Vendedor: ${ventaData.vendedor}\n`));
    commands.push(...this.textToBytes(`Metodo: ${ventaData.metodo_pago}\n`));
    commands.push(...this.textToBytes("--------------------------------\n"));
    
    // Productos
    commands.push(...this.textToBytes("PRODUCTOS:\n"));
    ventaData.productos.forEach(item => {
      commands.push(...this.textToBytes(`${item.nombre}\n`));
      commands.push(...this.textToBytes(`  ${item.cantidad} x $${item.precio_unitario.toFixed(2)} = $${item.subtotal.toFixed(2)}\n`));
    });
    
    commands.push(...this.textToBytes("--------------------------------\n"));
    
    // Total
    commands.push(...this.BOLD_ON);
    commands.push(...this.SIZE_DOUBLE);
    commands.push(...this.textToBytes(`TOTAL: $${ventaData.total.toFixed(2)}\n`));
    commands.push(...this.SIZE_NORMAL);
    commands.push(...this.BOLD_OFF);
    
    // Footer
    commands.push(...this.ALIGN_CENTER);
    commands.push(...this.textToBytes("\n¡Gracias por su compra!\n"));
    commands.push(...this.textToBytes("Vuelva pronto\n"));
    
    // Espacios y corte
    commands.push(...this.textToBytes("\n\n\n"));
    commands.push(...this.CUT);
    
    return new Uint8Array(commands.flat());
  }

  async print(ventaData) {
    if (!this.isConnected || !this.device) {
      throw new Error('Impresora no conectada');
    }

    try {
      const service = await this.server.getPrimaryService('0000ff00-0000-1000-8000-00805f9b34fb');
      const characteristic = await service.getCharacteristic('0000ff02-0000-1000-8000-00805f9b34fb');
      
      const ticketData = this.generateTicket(ventaData);
      
      // Enviar datos en chunks para evitar overflow
      const chunkSize = 20;
      for (let i = 0; i < ticketData.length; i += chunkSize) {
        const chunk = ticketData.slice(i, i + chunkSize);
        await characteristic.writeValue(chunk);
        await new Promise(resolve => setTimeout(resolve, 50)); // Pequeña pausa
      }
      
      return true;
    } catch (error) {
      console.error('Error imprimiendo:', error);
      throw error;
    }
  }
}

// Instancia global
window.printerService = new ESCPOSPrinter();
EOF

# Crear archivo HTML principal
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>MiChaska POS</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0066cc">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            overflow-x: hidden;
        }
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #0066cc;
            color: white;
            font-size: 1.2rem;
        }
        .app-container {
            max-width: 100vw;
            height: 100vh;
            overflow: auto;
        }
        iframe {
            width: 100%;
            height: 100vh;
            border: none;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="loading">
            <div>
                <h2>🚀 MiChaska POS</h2>
                <p>Cargando sistema...</p>
            </div>
        </div>
    </div>
    
    <script src="/src/services/printer.js"></script>
    <script>
        // Cargar la aplicación Streamlit
        document.addEventListener('DOMContentLoaded', function() {
            const appDiv = document.getElementById('app');
            
            // URL del servidor Streamlit (puedes cambiar esto)
            const streamlitUrl = 'http://localhost:8501';
            
            // Crear iframe para cargar Streamlit
            const iframe = document.createElement('iframe');
            iframe.src = streamlitUrl;
            iframe.onload = function() {
                appDiv.innerHTML = '';
                appDiv.appendChild(iframe);
            };
            
            iframe.onerror = function() {
                appDiv.innerHTML = `
                    <div class="loading">
                        <div>
                            <h2>❌ Error de Conexión</h2>
                            <p>No se pudo conectar al servidor</p>
                            <button onclick="location.reload()">Reintentar</button>
                        </div>
                    </div>
                `;
            };
        });

        // Registrar Service Worker para PWA
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => console.log('SW registrado:', registration))
                .catch(error => console.log('Error SW:', error));
        }

        // Función global para imprimir desde Streamlit
        window.imprimirTicket = async function(ventaData) {
            try {
                if (!window.printerService.isConnected) {
                    const connected = await window.printerService.connectBluetooth();
                    if (!connected) {
                        alert('No se pudo conectar a la impresora');
                        return false;
                    }
                }
                
                await window.printerService.print(ventaData);
                return true;
            } catch (error) {
                console.error('Error imprimiendo:', error);
                alert('Error al imprimir: ' + error.message);
                return false;
            }
        };

        // Función para conectar impresora manualmente
        window.conectarImpresora = async function() {
            try {
                const connected = await window.printerService.connectBluetooth();
                if (connected) {
                    alert('Impresora conectada exitosamente');
                } else {
                    alert('No se pudo conectar a la impresora');
                }
                return connected;
            } catch (error) {
                alert('Error conectando impresora: ' + error.message);
                return false;
            }
        };
    </script>
</body>
</html>
EOF

# Crear Service Worker
cat > public/sw.js << 'EOF'
const CACHE_NAME = 'michaska-v1';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/src/services/printer.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
EOF

echo "✅ Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. cd michaska-android"
echo "2. npm run build (cuando tengas el build)"
echo "3. npx cap sync"
echo "4. npx cap open android"
echo ""
echo "🔧 Para desarrollo:"
echo "1. Ejecuta tu servidor Streamlit en puerto 8501"
echo "2. Cambia la URL en public/index.html si es necesario"
echo "3. Prueba la app en navegador primero"
echo ""
echo "📱 Para generar APK:"
echo "1. Abre Android Studio"
echo "2. Build > Generate Signed Bundle/APK"
echo "3. Selecciona APK y sigue el wizard"
