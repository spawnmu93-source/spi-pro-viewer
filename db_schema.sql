-- ====================================================================
-- ESQUEMA DE BASE DE DATOS SPI CACHORRAS (POSTGRESQL)
-- ====================================================================

-- 1. Tabla de Usuarios y PINs
CREATE TABLE cachorras_usuarios (
    usuario VARCHAR(100) PRIMARY KEY,
    pin VARCHAR(10) NOT NULL
);

-- 2. Tabla de Destinatarios de Reportes
CREATE TABLE mails_corpo (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    mail VARCHAR(150) NOT NULL UNIQUE
);

-- 3. Tabla de Lotes (Sementeras iniciales de origen)
CREATE TABLE cachorras_lotes (
    id_cerda VARCHAR(50) PRIMARY KEY,
    lote VARCHAR(100) NOT NULL,
    raza VARCHAR(100),
    edad_ingreso INT, -- Edad cargada inicialmente en días
    fecha_nacimiento DATE,
    timestamp_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    is_deleted BOOLEAN DEFAULT FALSE, -- Control para baja o pase a plantel
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 4. Tabla de Plantel Reproductor (Cerdas activas)
CREATE TABLE cachorras_plantel (
    id_cerda VARCHAR(50) PRIMARY KEY,
    raza VARCHAR(100),
    edad INT, -- Edad actual en días (calculada o actualizada)
    peso NUMERIC(10,2), -- Último peso registrado
    tfi VARCHAR(50),
    tfd VARCHAR(50),
    numero_de_celo INT DEFAULT 1,
    lote_origen VARCHAR(100),
    timestamp_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    fecha_nacimiento DATE,
    is_deleted BOOLEAN DEFAULT FALSE, -- Control para bajas (muerte/venta/descarte)
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 5. Tabla de Registro Histórico de Celos
CREATE TABLE cachorras_registro_celo (
    id SERIAL PRIMARY KEY,
    id_cerda VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    edad INT,
    peso NUMERIC(10,2),
    tfi VARCHAR(50),
    tfd VARCHAR(50),
    numero_de_celo INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    lote_origen VARCHAR(100),
    motivo VARCHAR(200),
    fecha_nacimiento DATE,
    fecha_movimiento DATE, -- Fecha del celo ingresada por el operario
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 6. Histórico de Bajas por Muerte
CREATE TABLE cachorras_muertes (
    id SERIAL PRIMARY KEY,
    id_cerda VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    edad INT,
    peso NUMERIC(10,2),
    tfi VARCHAR(50),
    tfd VARCHAR(50),
    numero_de_celo INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    lote_origen VARCHAR(100),
    motivo VARCHAR(255),
    destino VARCHAR(150),
    fecha_nacimiento DATE,
    fecha_movimiento DATE,
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 7. Histórico de Bajas por Descarte
CREATE TABLE cachorras_descartes (
    id SERIAL PRIMARY KEY,
    id_cerda VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    edad INT,
    peso NUMERIC(10,2),
    tfi VARCHAR(50),
    tfd VARCHAR(50),
    numero_de_celo INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    lote_origen VARCHAR(100),
    motivo VARCHAR(255),
    destino VARCHAR(150),
    fecha_nacimiento DATE,
    fecha_movimiento DATE,
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 8. Histórico de Bajas por Venta
CREATE TABLE cachorras_ventas (
    id SERIAL PRIMARY KEY,
    id_cerda VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    edad INT,
    peso NUMERIC(10,2),
    tfi VARCHAR(50),
    tfd VARCHAR(50),
    numero_de_celo INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    lote_origen VARCHAR(100),
    motivo VARCHAR(255),
    destino VARCHAR(150),
    fecha_nacimiento DATE,
    fecha_movimiento DATE,
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 9. Control de Solicitudes de Modificación (Auditoría)
CREATE TABLE cachorras_modificaciones (
    id_solicitud VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operario VARCHAR(100),
    tipo_movimiento VARCHAR(100), -- 'Celo', 'Muerte', 'Descarte', 'Venta'
    id_cerda VARCHAR(50) NOT NULL,
    datos_originales TEXT, -- JSON con los datos del registro a revertir
    estado VARCHAR(50) DEFAULT 'Pendiente', -- 'Pendiente', 'Aprobado', 'Rechazado', 'Error'
    timestamp_resolucion TIMESTAMP NULL,
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- 10. Bitácora de Telemetría (System Logger)
CREATE TABLE cachorras_logger (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nivel VARCHAR(50), -- INFO, WARNING, ERROR
    usuario VARCHAR(100),
    evento TEXT,
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- ====================================================================
-- ÍNDICES PARA VELOCIDAD Y CRON DE SINCRONIZACIÓN
-- ====================================================================
CREATE INDEX idx_lotes_sync ON cachorras_lotes(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_plantel_sync ON cachorras_plantel(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_celo_sync ON cachorras_registro_celo(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_muertes_sync ON cachorras_muertes(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_descartes_sync ON cachorras_descartes(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_ventas_sync ON cachorras_ventas(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_modificaciones_sync ON cachorras_modificaciones(synced_to_sheets) WHERE synced_to_sheets = FALSE;
CREATE INDEX idx_logger_sync ON cachorras_logger(synced_to_sheets) WHERE synced_to_sheets = FALSE;
