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
