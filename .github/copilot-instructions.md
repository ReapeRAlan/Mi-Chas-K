<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Sistema de Facturación MiChaska

## Descripción del Proyecto
Sistema de punto de venta y facturación desarrollado en Python con Streamlit. Incluye:
- Interfaz de punto de venta con carrito de compras
- Gestión de inventario y productos
- Base de datos SQLite local
- Dashboard de ventas y estadísticas
- Generación de tickets/facturas en PDF

## Tecnologías Utilizadas
- **Frontend**: Streamlit
- **Backend**: Python
- **Base de datos**: SQLite
- **PDF**: ReportLab
- **Gráficos**: Plotly

## Arquitectura
- `app.py`: Aplicación principal Streamlit con navegación multi-página
- `database/`: Módulos para manejo de base de datos
- `pages/`: Páginas individuales de la aplicación
- `utils/`: Utilidades y funciones auxiliares
- `assets/`: Recursos estáticos

## Instrucciones para Copilot
- Mantener código Python limpio y bien documentado
- Usar convenciones PEP 8
- Implementar manejo de errores apropiado
- Priorizar funcionalidad y usabilidad
- Mantener la base de datos SQLite optimizada
