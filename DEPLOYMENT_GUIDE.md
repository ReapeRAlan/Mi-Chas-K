# Guía de Deployment en Render

## Configuración Automática

Este proyecto está configurado para hacer deployment automático en Render usando el archivo `render.yaml`. La base de datos PostgreSQL ya está configurada con las credenciales reales.

## Pasos para el Deployment

### 1. Conectar el Repositorio
- Ve a [Render Dashboard](https://dashboard.render.com/)
- Haz clic en "New +"
- Selecciona "Web Service"
- Conecta tu repositorio de GitHub: `https://github.com/ReapeRAlan/Mi-Chas-K`

### 2. Configuración Automática
Render debería detectar automáticamente el archivo `render.yaml` y configurar:
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false`
- **Environment**: Python 3.9
- **Plan**: Free

### 3. Variables de Entorno
Las siguientes variables están pre-configuradas en `render.yaml`:

```
DATABASE_URL=postgresql://admin:wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd
DB_HOST=dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com
DB_NAME=chaskabd
DB_USER=admin
DB_PASSWORD=wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu
DB_PORT=5432
```

### 4. Deploy
- Haz clic en "Deploy"
- Render comenzará el proceso de build e instalación
- El proceso tomará unos minutos la primera vez

## Verificación del Deployment

### Logs a Revisar
1. **Build Logs**: Verificar que todas las dependencias se instalen correctamente
2. **Runtime Logs**: Confirmar que:
   - La conexión a PostgreSQL sea exitosa
   - Las tablas se creen automáticamente
   - La aplicación Streamlit inicie correctamente

### Señales de Éxito
- ✅ "Connected to PostgreSQL database successfully"
- ✅ "Database initialized successfully"  
- ✅ "Streamlit server started on port XXXX"

### Posibles Errores y Soluciones

#### Error de Conexión a Base de Datos
```
psycopg2.OperationalError: could not connect to server
```
**Solución**: Verificar que las credenciales de la base de datos estén correctas en las variables de entorno.

#### Error de Dependencias
```
ModuleNotFoundError: No module named 'xxx'
```
**Solución**: Verificar que todas las dependencias estén en `requirements.txt`.

#### Error de Puerto
```
OSError: [Errno 98] Address already in use
```
**Solución**: Verificar que el comando de inicio use `--server.port=$PORT`.

## URLs de Acceso

Una vez desplegado, tu aplicación estará disponible en:
- **URL de Render**: `https://mi-chaska.onrender.com` (o similar)
- **Dashboard**: Panel de control principal
- **POS**: Sistema de punto de venta
- **Inventario**: Gestión de productos

## Mantenimiento

### Actualizaciones Automáticas
- Cada push al branch `main` activará un nuevo deployment
- Render reconstruirá y redesplegará automáticamente

### Monitoreo
- Revisar logs regularmente en el dashboard de Render
- Configurar notificaciones de errores si es necesario

### Backup de Base de Datos
La base de datos PostgreSQL en Render está gestionada automáticamente, pero considera:
- Exportar datos importantes periódicamente
- Mantener una copia local de desarrollo para testing

## Contacto y Soporte

Para cualquier problema con el deployment:
1. Revisar los logs en Render Dashboard
2. Verificar este archivo de documentación
3. Comprobar las variables de entorno
4. Contactar soporte técnico si es necesario

---

**Última actualización**: $(date)
**Estado**: Listo para producción ✅
