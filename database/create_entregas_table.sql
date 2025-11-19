-- Tabla para gestionar entregas locales
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

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_entregas_venta_id ON entregas(venta_id);
CREATE INDEX IF NOT EXISTS idx_entregas_estado ON entregas(estado);
CREATE INDEX IF NOT EXISTS idx_entregas_fecha ON entregas(fecha_creacion);

-- Trigger para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION actualizar_fecha_entregas()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actualizar_fecha_entregas
BEFORE UPDATE ON entregas
FOR EACH ROW
EXECUTE FUNCTION actualizar_fecha_entregas();
