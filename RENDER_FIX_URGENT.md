# 🚨 INSTRUCCIONES URGENTES PARA RENDER 🚨

## Variables de Entorno a Actualizar en Render Dashboard

**IMPORTANTE**: Ve al dashboard de Render y actualiza estas variables de entorno:

### ✅ Variables Correctas:

```
DATABASE_URL = postgresql://admin:wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd

DB_HOST = dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com

DB_NAME = chaskabd

DB_USER = admin

DB_PASS = wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu

DB_PASSWORD = wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu

DB_PORT = 5432

SECRET_KEY = bd5d56cac14e32603c3e26296d88f26d
```

### 🔧 Cambios Necesarios:

1. **DATABASE_URL**: Cambiar de hostname interno a externo
   - ❌ Actual: `@dpg-d13oam8dl3ps7392hfu0-a/chaskabd`
   - ✅ Correcto: `@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd`

2. **DB_HOST**: Agregar el sufijo completo
   - ❌ Actual: `dpg-d13oam8dl3ps7392hfu0`
   - ✅ Correcto: `dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com`

3. **Agregar DB_PASSWORD**: Para compatibilidad
   - ✅ Nuevo: `DB_PASSWORD = wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu`

### 📱 Pasos en Render Dashboard:

1. Ve a tu servicio `mi-chaska` en Render
2. Haz clic en "Environment" en el menú lateral
3. Actualiza cada variable con los valores correctos de arriba
4. Haz clic en "Save Changes"
5. Render redesplegará automáticamente

### 🔍 Verificación:

Después de actualizar, los logs deberían mostrar:
- ✅ "Connected to PostgreSQL database successfully"
- ✅ "Database initialized successfully"

### ⚡ Problema Identificado:

El error `database "chaskabd " does not exist` se debe a que:
- Render está usando el hostname interno en lugar del externo
- El hostname interno no es accesible desde el servicio web
- Necesitas usar el hostname externo con `.oregon-postgres.render.com`

### 📞 Si Persiste el Problema:

1. Verificar que la base de datos PostgreSQL esté corriendo en Render
2. Comprobar que las credenciales no hayan cambiado
3. Revisar los logs de la base de datos en Render
4. Contactar soporte de Render si es necesario
