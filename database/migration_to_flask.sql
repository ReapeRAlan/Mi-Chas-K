-- Script de migración para actualizar la base de datos existente
-- Ejecutar este script para agregar funcionalidades de entregas locales

-- 1. Crear tabla de entregas (si no existe)
CREATE TABLE IF NOT EXISTS entregas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    direccion TEXT NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    distancia_km DECIMAL(5, 2) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    notas TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_estado CHECK (estado IN ('Pendiente', 'En Camino', 'Entregado', 'Cancelado'))
);

-- 2. Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_entregas_venta_id ON entregas(venta_id);
CREATE INDEX IF NOT EXISTS idx_entregas_estado ON entregas(estado);
CREATE INDEX IF NOT EXISTS idx_entregas_fecha ON entregas(fecha_creacion);

-- 3. Trigger para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION actualizar_fecha_entregas()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_fecha_entregas ON entregas;
CREATE TRIGGER trg_actualizar_fecha_entregas
BEFORE UPDATE ON entregas
FOR EACH ROW
EXECUTE FUNCTION actualizar_fecha_entregas();

-- 4. Verificar que las tablas necesarias existen (no las crea si ya existen)
-- Estas tablas ya deberían existir de la aplicación anterior

-- productos
-- ventas
-- detalle_ventas
-- categorias
-- gastos_diarios
-- cortes_caja
-- vendedores

-- 5. Agregar campo 'estado' a tabla ventas si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ventas' AND column_name = 'estado'
    ) THEN
        ALTER TABLE ventas ADD COLUMN estado VARCHAR(50) DEFAULT 'Completada';
    END IF;
END $$;

-- 6. Índices adicionales para optimización
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_vendedor ON ventas(vendedor);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);

-- 7. Insertar categorías por defecto si no existen
INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'Chascas', 'Nuestros productos principales: chascas tradicionales', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'Chascas');

INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'DoriChascas', 'Chascas especiales con frituras populares', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'DoriChascas');

INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'Empapelados', 'Tortillas rellenas y empapeladas al gusto', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'Empapelados');

INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'Elotes', 'Elotes preparados en diferentes estilos', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'Elotes');

INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'Especialidades', 'Productos especiales y combinaciones únicas', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'Especialidades');

INSERT INTO categorias (nombre, descripcion, activo)
SELECT 'Extras', 'Porciones adicionales y complementos', TRUE
WHERE NOT EXISTS (SELECT 1 FROM categorias WHERE nombre = 'Extras');

-- 8. Mensaje de éxito
DO $$
BEGIN
    RAISE NOTICE '✅ Migración completada exitosamente';
    RAISE NOTICE '📊 Tabla de entregas creada/verificada';
    RAISE NOTICE '🔍 Índices optimizados';
    RAISE NOTICE '📁 Categorías por defecto agregadas';
END $$;
