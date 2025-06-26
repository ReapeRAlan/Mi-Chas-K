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
