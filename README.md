# 🌮 MiChaska - Sistema de Facturación

Sistema de punto de venta completo desarrollado en Python con Streamlit, diseñado para el restaurante MiChaska. **Adaptado para deployment en Render con PostgreSQL**.

## 🚀 Características Principales

- **Punto de Venta Intuitivo**: Interface con botones grandes para agregar productos
- **Gestión de Inventario**: Control completo de productos, stock y categorías  
- **Dashboard de Ventas**: Estadísticas en tiempo real con gráficos interactivos
- **Generación de Tickets**: PDFs automáticos listos para imprimir
- **Base de Datos en la Nube**: PostgreSQL para máxima confiabilidad
- **Responsive Design**: Optimizado para dispositivos móviles y desktop

## 🏪 Menú MiChaska

### Chascas
- Chasca Mini ($20.00)
- Chasca Chica ($25.00) 
- Chasca Chica Plus ($35.00)
- Chasca Mediana ($50.00)
- Chasca Grande ($60.00)

### DoriChascas ($65.00)
- DoriChasca, TostiChasca, ChetoChasca, RuffleChasca, SabriChasca

### Empapelados ($90.00 - $110.00)
- Champiñones, Bisteck, Salchicha, Tocino, 3 quesos, Carnes Frías, Cubano, Arrachera, Camarones

### Elotes ($18.00 - $40.00)
- Elote sencillo, ½ Elote, Elote Amarillo, Elote Asado, Elote Crunch

### Especialidades ($50.00 - $140.00)
- Elote Capricho, Chorriadas, Maruchascas variadas, Sabrimaruchan

## 🛠️ Tecnologías

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Base de Datos**: PostgreSQL (Render)
- **PDF**: ReportLab
- **Gráficos**: Plotly
- **Deployment**: Render

## 🌐 Deployment en Render

### Variables de Entorno Configuradas:
```
DATABASE_URL=postgresql://admin:***@dpg-***-a/chaskabd
DB_HOST=dpg-d13oam8dl3ps7392hfu0
DB_NAME=chaskabd
DB_USER=admin
DB_PASS=***
DB_PORT=5432
SECRET_KEY=***
```

### Configuración de Deploy:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
- **Plan**: Free Tier

## 📦 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/ReapeRAlan/Mi-Chas-K.git
cd Mi-Chas-K

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar aplicación
streamlit run app.py
```

## 🚀 Uso del Sistema

1. **Punto de Venta**: Selecciona productos → Agregar al carrito → Procesar venta
2. **Inventario**: Gestiona productos, precios y stock
3. **Dashboard**: Visualiza ventas, estadísticas y genera reportes
4. **Configuración**: Ajusta datos del negocio y sistema

## 📊 Funcionalidades del Dashboard

- 📈 Métricas de ventas diarias
- 📅 Gráficos de evolución temporal
- 🏆 Productos más vendidos
- 💳 Distribución por métodos de pago
- 🕐 Análisis por horarios de venta

## 🧾 Sistema de Tickets

- Generación automática en PDF
- Información completa de la venta
- Descarga inmediata
- Formato optimizado para impresión térmica

## 🔧 Configuración del Sistema

- Datos del negocio
- Métodos de pago
- Limpieza de ventas antiguas
- Configuraciones avanzadas

## 📱 Responsive Design

Optimizado para:
- 💻 Desktop (1920x1080+)
- 📱 Tablet (768x1024)
- 📱 Mobile (375x667+)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/ReapeRAlan/Mi-Chas-K/issues)
- **Documentación**: Este README
- **Email**: Contacta al administrador

---

**🌮 MiChaska - La mejor chasca de la ciudad** 

*Desarrollado con ❤️ para optimizar las ventas y brindar la mejor experiencia al cliente*
