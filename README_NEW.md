# 🛒 MiChaska - Sistema de Facturación y POS

Sistema moderno de punto de venta con entregas locales integradas. Desarrollado con Flask, Bootstrap 5 y PostgreSQL.

## ✨ Características Principales

- **🛍️ Punto de Venta Moderno**: Interfaz intuitiva y responsive optimizada para tablets
- **📍 Entregas Locales**: Validación de ubicación en tiempo real con radio de 10km
- **📦 Gestión de Inventario**: Control completo de productos, stock y categorías
- **📊 Dashboard Analítico**: Estadísticas y reportes de ventas en tiempo real
- **🧾 Tickets PDF**: Generación automática de tickets de venta
- **🗺️ Mapas Interactivos**: Visualización de ubicaciones de entrega con Leaflet
- **📱 100% Responsive**: Optimizado para móvil, tablet y escritorio

## 🚀 Tecnologías

### Backend
- **Flask** 3.0+ - Framework web Python
- **PostgreSQL** - Base de datos relacional
- **Gunicorn** - Servidor WSGI para producción

### Frontend
- **Bootstrap 5.3** - Framework CSS responsive
- **Vanilla JavaScript** - Sin dependencias pesadas
- **Leaflet** - Mapas interactivos
- **Axios** - Cliente HTTP

### Utilidades
- **ReportLab** - Generación de PDFs
- **pytz** - Manejo de zonas horarias
- **python-dotenv** - Variables de entorno

## 📂 Estructura del Proyecto

```
Mi-Chas-K/
├── server.py                 # Aplicación Flask principal
├── database/
│   ├── models.py            # Modelos de datos (ORM)
│   ├── connection.py        # Conexión a PostgreSQL
│   └── create_entregas_table.sql
├── templates/               # Templates HTML (Jinja2)
│   ├── base.html           # Template base
│   ├── index.html          # Página principal
│   ├── pos.html            # Punto de venta
│   ├── ordenes.html        # Gestión de entregas
│   ├── inventario.html     # Gestión de inventario
│   ├── dashboard.html      # Estadísticas
│   └── configuracion.html  # Configuración
├── static/
│   ├── css/
│   │   └── main.css        # Estilos personalizados
│   └── js/
│       ├── utils.js        # Utilidades generales
│       └── pos.js          # Lógica punto de venta
├── utils/
│   ├── pdf_generator.py    # Generador de tickets
│   ├── timezone_utils.py   # Utilidades de fecha/hora
│   └── helpers.py
├── requirements.txt        # Dependencias Python
├── render.yaml            # Configuración Render
├── Procfile               # Configuración despliegue
└── .env.example           # Variables de entorno ejemplo
```

## 🔧 Instalación Local

### Requisitos Previos
- Python 3.11+
- PostgreSQL 14+
- Git

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/ReapeRAlan/Mi-Chas-K.git
cd Mi-Chas-K
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL
```

5. **Crear la tabla de entregas**
```bash
psql -U admin -d chaskabd -f database/create_entregas_table.sql
```

6. **Ejecutar la aplicación**
```bash
# Modo desarrollo
python server.py

# Modo producción con Gunicorn
gunicorn server:app --bind 0.0.0.0:5000
```

7. **Abrir en navegador**
```
http://localhost:5000
```

## ☁️ Despliegue en Render

### Opción 1: Despliegue Automático

1. Haz fork del repositorio
2. Crea una cuenta en [Render.com](https://render.com)
3. Conecta tu repositorio de GitHub
4. Render detectará automáticamente `render.yaml`
5. Configura las variables de entorno en el dashboard de Render
6. ¡Despliega!

### Opción 2: Despliegue Manual

1. En Render Dashboard, crea un nuevo **Web Service**
2. Conecta tu repositorio
3. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2`
   - **Environment**: Python 3
4. Agrega variables de entorno:
   ```
   FLASK_ENV=production
   DATABASE_URL=tu_conexion_postgresql
   SECRET_KEY=tu_clave_secreta
   BUSINESS_LAT=19.4326
   BUSINESS_LNG=-99.1332
   ```
5. Despliega

## 🌍 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL conexión PostgreSQL | `postgresql://user:pass@host/db` |
| `DB_HOST` | Host de PostgreSQL | `localhost` |
| `DB_NAME` | Nombre de la base de datos | `chaskabd` |
| `DB_USER` | Usuario de PostgreSQL | `admin` |
| `DB_PASSWORD` | Contraseña | `password` |
| `DB_PORT` | Puerto PostgreSQL | `5432` |
| `FLASK_ENV` | Entorno Flask | `development` / `production` |
| `SECRET_KEY` | Clave secreta Flask | `random-secret-key` |
| `BUSINESS_LAT` | Latitud del negocio | `19.4326` |
| `BUSINESS_LNG` | Longitud del negocio | `-99.1332` |
| `PORT` | Puerto del servidor | `5000` |

## 📡 API Endpoints

### Productos
- `GET /api/productos` - Listar productos
- `GET /api/productos/{id}` - Obtener producto
- `POST /api/productos` - Crear producto
- `PUT /api/productos/{id}` - Actualizar producto
- `DELETE /api/productos/{id}` - Eliminar producto

### Ventas
- `GET /api/ventas` - Listar ventas
- `GET /api/ventas/{id}` - Obtener venta con detalles
- `POST /api/ventas` - Crear venta
- `GET /api/ticket/{venta_id}` - Descargar ticket PDF

### Entregas
- `POST /api/entregas/validar-ubicacion` - Validar ubicación
- `GET /api/entregas` - Listar entregas
- `PUT /api/entregas/{id}/estado` - Actualizar estado

### Categorías
- `GET /api/categorias` - Listar categorías
- `POST /api/categorias` - Crear categoría

### Estadísticas
- `GET /api/estadisticas/ventas` - Estadísticas de ventas
- `GET /api/health` - Health check

## 🗺️ Sistema de Entregas Locales

El sistema incluye validación de ubicación en tiempo real:

1. **Activar entrega** en el carrito de compra
2. **Usar mi ubicación** para obtener coordenadas GPS
3. **Validación automática** del radio de 10km
4. **Visualización en mapa** de la ruta
5. **Procesamiento** de la venta con información de entrega

### Cálculo de Distancia

Se utiliza la **fórmula de Haversine** para calcular la distancia entre dos puntos geográficos:

```python
def calcular_distancia(lat1, lng1, lat2, lng2):
    R = 6371  # Radio de la Tierra en km
    # ... cálculo Haversine
    return distancia_km
```

## 🎨 Personalización

### Cambiar Ubicación del Negocio
Edita las variables de entorno:
```bash
BUSINESS_LAT=tu_latitud
BUSINESS_LNG=tu_longitud
```

### Modificar Radio de Entrega
En `server.py`:
```python
RADIO_ENTREGA_KM = 10  # Cambiar según necesidad
```

### Personalizar Estilos
Edita `static/css/main.css` para modificar colores, fuentes y diseño.

## 🧪 Testing

```bash
# Verificar conectividad
curl http://localhost:5000/api/health
```

## 📝 Licencia

Este proyecto es de uso privado para MiChaska.

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📞 Soporte

Para reportar problemas o sugerencias, abre un issue en GitHub.

---

Desarrollado con ❤️ para MiChaska
