-- ============================================================================
-- SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - ESQUEMA DDL POSTGRESQL DEFINITIVO
-- Versión: 2.0 Enterprise (Auditada y Sincronizada)
-- Compatibilidad: PostgreSQL 14+, Supabase, AWS RDS, Flyway / Alembic
-- ============================================================================

-- 0. EXTENSIONES Y ROLES DE SEGURIDAD ---------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'edge_user') THEN
        CREATE ROLE edge_user;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_user') THEN
        CREATE ROLE audit_user;
    END IF;
END
$$;

-- 1. CATÁLOGOS MAESTROS Y CONFIGURACIÓN -------------------------------------
CREATE TABLE catalogo_operarios (
    id_operario       BIGSERIAL PRIMARY KEY,
    nombre            VARCHAR(100) NOT NULL,
    pin_hash          VARCHAR(128) NOT NULL,
    rol               VARCHAR(30)  NOT NULL CHECK (rol IN ('OPERARIO_GRANJA','CARNICERO','SUPERVISOR','AUDITOR','CHOFER')),
    sucursal_asignada VARCHAR(30),
    activo            BOOLEAN      DEFAULT TRUE,
    creado_en         TIMESTAMP    DEFAULT now()
);

CREATE TABLE catalogo_articulos (
    codigo_tango                 VARCHAR(20) PRIMARY KEY,
    nombre                       VARCHAR(100) NOT NULL,
    familia                      VARCHAR(30)  NOT NULL CHECK (familia IN ('CORTE_MADRE','CORTE_FINAL','CHACINADO_FRESCO','CHACINADO_SECO','SUBPRODUCTO','INSUMO')),
    unidad                       VARCHAR(5)   NOT NULL DEFAULT 'KG',
    temperatura_conservacion_min NUMERIC(3,1) DEFAULT 0.0,
    temperatura_conservacion_max NUMERIC(3,1) DEFAULT 4.0,
    activo                       BOOLEAN      DEFAULT TRUE,
    creado_en                    TIMESTAMP    DEFAULT now()
);

CREATE TABLE configuracion_subproductos (
    tipo_subproducto      VARCHAR(30) PRIMARY KEY, -- 'TOCINO', 'CUERO', 'HUESO', 'GRASA'
    codigo_articulo_tango VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    lote_fijo_asignado    VARCHAR(30) DEFAULT '00049',
    descripcion           TEXT
);

-- 2. GRANJA: REPRODUCCIÓN, PARTOS Y DESTETES -------------------------------
CREATE TABLE granja_servicios (
    id_servicio         BIGSERIAL PRIMARY KEY,
    id_cerda            VARCHAR(20) NOT NULL,
    categoria_cerda     VARCHAR(20) NOT NULL CHECK (categoria_cerda IN ('CACHORRA_NULIPARA','MULTIPARA')),
    nro_parto_historico SMALLINT    NOT NULL,
    id_macho_dosis      VARCHAR(30) NOT NULL,
    fecha_servicio      DATE        NOT NULL,
    hora_servicio       TIME        NOT NULL,
    nro_dosis           SMALLINT    NOT NULL DEFAULT 1 CHECK (nro_dosis BETWEEN 1 AND 3),
    tipo_servicio       VARCHAR(20) NOT NULL CHECK (tipo_servicio IN ('INSEMINACION_IA','MONTA_NATURAL')),
    operario_id         BIGINT      NOT NULL REFERENCES catalogo_operarios(id_operario),
    creado_en           TIMESTAMP   DEFAULT now()
);

CREATE TABLE granja_diagnostico_prenez (
    id_diagnostico           BIGSERIAL PRIMARY KEY,
    id_servicio_fk           BIGINT      NOT NULL REFERENCES granja_servicios(id_servicio),
    fecha_control            DATE        NOT NULL,
    metodo                   VARCHAR(20) NOT NULL DEFAULT 'ECOGRAFIA' CHECK (metodo IN ('ECOGRAFIA','DOPPLER','RETORNO_CELO')),
    resultado                VARCHAR(15) NOT NULL CHECK (resultado IN ('POSITIVA','NEGATIVA','DUDOSA')),
    dias_abiertos_calculados SMALLINT,
    fecha_probable_parto     DATE,
    creado_en                TIMESTAMP   DEFAULT now()
);

CREATE TABLE granja_partos (
    id_parto                BIGSERIAL PRIMARY KEY,
    id_servicio_fk          BIGINT      NOT NULL REFERENCES granja_servicios(id_servicio),
    id_cerda                VARCHAR(20) NOT NULL,
    fecha_parto             DATE        NOT NULL,
    sala_maternidad         VARCHAR(20) NOT NULL,
    jaula                   VARCHAR(10) NOT NULL,
    nacidos_vivos           SMALLINT    NOT NULL,
    nacidos_muertos         SMALLINT    NOT NULL DEFAULT 0,
    momias                  SMALLINT    NOT NULL DEFAULT 0,
    lechones_adoptados      SMALLINT    NOT NULL DEFAULT 0,
    lechones_donados        SMALLINT    NOT NULL DEFAULT 0,
    total_camada_efectiva   SMALLINT    GENERATED ALWAYS AS (nacidos_vivos + lechones_adoptados - lechones_donados) STORED,
    peso_camada_nacida_kg   NUMERIC(6,2) NOT NULL,
    duracion_parto_horas    NUMERIC(3,1),
    atencion_parto_operario BIGINT      REFERENCES catalogo_operarios(id_operario),
    creado_en               TIMESTAMP   DEFAULT now()
);

CREATE TABLE granja_destetes (
    id_destete              BIGSERIAL PRIMARY KEY,
    id_parto_fk             BIGINT      NOT NULL REFERENCES granja_partos(id_parto),
    lote_destete_creado     VARCHAR(30) UNIQUE NOT NULL,
    fecha_destete           DATE        NOT NULL,
    dias_lactancia          SMALLINT    NOT NULL,
    lechones_destetados     SMALLINT    NOT NULL,
    bajas_en_lactancia      SMALLINT    NOT NULL DEFAULT 0,
    peso_total_destete_kg   NUMERIC(7,2) NOT NULL,
    peso_promedio_lechon_kg NUMERIC(5,2) GENERATED ALWAYS AS (peso_total_destete_kg / NULLIF(lechones_destetados, 0)) STORED,
    destino_cerda           VARCHAR(25) NOT NULL CHECK (destino_cerda IN ('RE_SERVICIO','GESTACION_CONFIRMADA','ENFERMERIA','DESCARTE_REFUGO')),
    creado_en               TIMESTAMP   DEFAULT now()
);

-- 3. GRANJA: RECRÍA, ENGORDE Y BALANCEADOS (MODELO M:N) ---------------------
CREATE TABLE granja_lotes_engorde (
    id_lote_engorde       VARCHAR(30) PRIMARY KEY,
    galpon_pista          VARCHAR(20) NOT NULL,
    fecha_inicio          DATE        NOT NULL,
    cabezas_ingresadas    INTEGER     NOT NULL,
    peso_inicial_total_kg NUMERIC(8,2) NOT NULL,
    fecha_cierre          DATE,
    cabezas_finales       INTEGER,
    peso_final_total_kg   NUMERIC(8,2),
    bajas_mortandad       INTEGER     DEFAULT 0,
    estado                VARCHAR(15) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO','DESPACHADO','CERRADO')),
    creado_en             TIMESTAMP   DEFAULT now()
);

CREATE TABLE granja_lote_engorde_composicion (
    id_composicion         BIGSERIAL PRIMARY KEY,
    id_lote_engorde_fk     VARCHAR(30) NOT NULL REFERENCES granja_lotes_engorde(id_lote_engorde),
    lote_destete_origen_fk VARCHAR(30) NOT NULL REFERENCES granja_destetes(lote_destete_creado),
    cabezas_aportadas      INTEGER     NOT NULL,
    kilos_aportados        NUMERIC(7,2) NOT NULL,
    creado_en              TIMESTAMP   DEFAULT now()
);

CREATE TABLE granja_consumo_balanceado (
    id_entrega_alimento       BIGSERIAL PRIMARY KEY,
    id_lote_engorde_fk        VARCHAR(30) NOT NULL REFERENCES granja_lotes_engorde(id_lote_engorde),
    fecha_suministro          DATE        NOT NULL,
    tipo_formula              VARCHAR(30) NOT NULL,
    lote_balanceado_proveedor VARCHAR(30) NOT NULL,
    kilos_alimento_kg         NUMERIC(8,2) NOT NULL,
    creado_en                 TIMESTAMP   DEFAULT now()
);

-- 4. FRIGORÍFICO Y FAENA ----------------------------------------------------
CREATE TABLE faena_tropas (
    id_tropa_faena          VARCHAR(30) PRIMARY KEY,
    id_lote_engorde_fk      VARCHAR(30) NOT NULL REFERENCES granja_lotes_engorde(id_lote_engorde),
    dte_senasa              VARCHAR(30) NOT NULL UNIQUE,
    fecha_faena             DATE        NOT NULL,
    hora_inicio_faena       TIME        NOT NULL,
    cabezas_recibidas       INTEGER     NOT NULL,
    cabezas_faenadas        INTEGER     NOT NULL,
    peso_despacho_granja_kg NUMERIC(8,2) NOT NULL,
    peso_vivo_bascula_kg    NUMERIC(8,2) NOT NULL,
    decomisos_cabezas_total INTEGER     DEFAULT 0,
    merma_transporte_pie_kg NUMERIC(7,2) GENERATED ALWAYS AS (peso_despacho_granja_kg - peso_vivo_bascula_kg) STORED,
    horas_descanso_corral   NUMERIC(3,1) NOT NULL,
    creado_en               TIMESTAMP   DEFAULT now()
);

CREATE TABLE faena_medias_reses (
    id_media_res                  BIGSERIAL PRIMARY KEY,
    id_tropa_fk                   VARCHAR(30) NOT NULL REFERENCES faena_tropas(id_tropa_faena),
    lado                          VARCHAR(3)  NOT NULL CHECK (lado IN ('IZQ','DER')),
    peso_gancho_caliente_kg       NUMERIC(6,2) NOT NULL,
    peso_gancho_frio_kg           NUMERIC(6,2),
    espesor_grasa_dorsal_mm       NUMERIC(4,1) NOT NULL,
    porcentaje_magro_estimado     NUMERIC(4,1) NOT NULL,
    ph_45min                      NUMERIC(3,2),
    ph_24h                        NUMERIC(3,2),
    temperatura_camara_c          NUMERIC(3,1) NOT NULL,
    lote_media_res                VARCHAR(30) NOT NULL,
    aprobacion_veterinaria_senasa BOOLEAN     DEFAULT TRUE,
    idempotency_key               VARCHAR(64) UNIQUE,
    creado_en                     TIMESTAMP   DEFAULT now()
);

-- 5. FÁBRICA DE CHACINADOS Y EMBUTIDOS --------------------------------------
CREATE TABLE catalogo_recetas_chacinados (
    id_receta                BIGSERIAL PRIMARY KEY,
    codigo_articulo_tango    VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    nombre_receta            VARCHAR(100) NOT NULL,
    tipo_proceso             VARCHAR(20) NOT NULL CHECK (tipo_proceso IN ('FRESCO','SECO_CURADO','COCIDO')),
    temperatura_mezclado_max NUMERIC(3,1) DEFAULT 4.0,
    rendimiento_teorico_pct  NUMERIC(5,2) NOT NULL,
    activo                   BOOLEAN      DEFAULT TRUE
);

CREATE TABLE chacinados_bachadas (
    id_bachada                 VARCHAR(30) PRIMARY KEY,
    id_receta_fk               BIGINT       NOT NULL REFERENCES catalogo_recetas_chacinados(id_receta),
    fecha_elaboracion          TIMESTAMP    NOT NULL,
    operario_responsable       BIGINT       NOT NULL REFERENCES catalogo_operarios(id_operario),
    temperatura_mezclado_real  NUMERIC(3,1) NOT NULL,
    kilos_masa_formulada       NUMERIC(8,2) NOT NULL,
    kilos_obtenidos_terminados NUMERIC(8,2) NOT NULL,
    unidades_ristras           INTEGER      NOT NULL,
    merma_secado_curado_kg     NUMERIC(7,2) DEFAULT 0.0,
    idempotency_key            VARCHAR(64)  UNIQUE,
    creado_en                  TIMESTAMP    DEFAULT now()
);

CREATE TABLE chacinados_ingredientes_consumidos (
    id_ingrediente_item    BIGSERIAL PRIMARY KEY,
    id_bachada_fk          VARCHAR(30) NOT NULL REFERENCES chacinados_bachadas(id_bachada),
    tipo_ingrediente       VARCHAR(30) NOT NULL CHECK (tipo_ingrediente IN ('MAGRO_CERDO','TOCINO_GRASA','CUERO','SANGRE','TRIPA','SAL_CURA_ADITIVO','ESPECIAS')),
    lote_origen_mp         VARCHAR(30) NOT NULL,
    lote_proveedor_aditivo VARCHAR(30),
    fecha_vencimiento_insumo DATE,
    kilos_utilizados_kg    NUMERIC(7,2) NOT NULL,
    creado_en              TIMESTAMP    DEFAULT now()
);

-- 6. LOGÍSTICA DE DESPACHO TÉRMICO -----------------------------------------
CREATE TABLE logistica_despachos_remitos (
    id_remito_tango            VARCHAR(20) PRIMARY KEY,
    sucursal_destino           VARCHAR(30) NOT NULL,
    fecha_salida               TIMESTAMP   NOT NULL,
    fecha_llegada_real         TIMESTAMP,
    chofer_id                  BIGINT      NOT NULL REFERENCES catalogo_operarios(id_operario),
    patente_vehiculo           VARCHAR(15) NOT NULL,
    temperatura_caja_salida_c  NUMERIC(3,1) NOT NULL,
    temperatura_caja_llegada_c NUMERIC(3,1),
    precinto_seguridad_nro     VARCHAR(30) NOT NULL,
    estado                     VARCHAR(25) DEFAULT 'EN_TRANSITO' CHECK (estado IN ('EN_TRANSITO','RECIBIDO_CONFORME','RECIBIDO_CON_OBSERVACION','RECHAZADO')),
    creado_en                  TIMESTAMP   DEFAULT now()
);

CREATE TABLE logistica_remito_items (
    id_item_remito                 BIGSERIAL PRIMARY KEY,
    id_remito_fk                   VARCHAR(20) NOT NULL REFERENCES logistica_despachos_remitos(id_remito_tango),
    codigo_tango                   VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    lote_origen                    VARCHAR(30) NOT NULL,
    piezas_unidades                INTEGER     NOT NULL DEFAULT 1,
    kilos_despachados_kg           NUMERIC(8,2) NOT NULL,
    kilos_recibidos_kg             NUMERIC(8,2),
    diferencia_merma_transporte_kg NUMERIC(6,2) GENERATED ALWAYS AS (kilos_despachados_kg - kilos_recibidos_kg) STORED,
    creado_en                      TIMESTAMP   DEFAULT now()
);

-- 7. LOCAL COMERCIAL: DESPIECE SPI EN MOSTRADOR ----------------------------
CREATE TABLE spi_despiece_sesiones (
    id_sesion_despiece        BIGSERIAL PRIMARY KEY,
    sucursal                  VARCHAR(30) NOT NULL,
    fecha_hora                TIMESTAMP   NOT NULL DEFAULT now(),
    operario_id               BIGINT      NOT NULL REFERENCES catalogo_operarios(id_operario),
    lote_madre                VARCHAR(30) NOT NULL,
    codigo_madre              VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    corte_madre_nombre        VARCHAR(50) NOT NULL,
    peso_madre_ingreso_kg     NUMERIC(7,2) NOT NULL,
    peso_total_resultantes_kg NUMERIC(7,2) DEFAULT 0.0,
    peso_merma_despiece_kg    NUMERIC(6,2) DEFAULT 0.0,
    rendimiento_sesion_pct    NUMERIC(5,2),
    duracion_minutos          SMALLINT,
    estado                    VARCHAR(15) DEFAULT 'CERRADA' CHECK (estado IN ('EN_PROCESO','CERRADA','ANULADA')),
    idempotency_key           VARCHAR(64) UNIQUE,
    creado_en                 TIMESTAMP   DEFAULT now(),
    eliminado_en              TIMESTAMP
);

CREATE TABLE spi_despiece_resultantes (
    id_resultante         BIGSERIAL PRIMARY KEY,
    id_sesion_fk          BIGINT      NOT NULL REFERENCES spi_despiece_sesiones(id_sesion_despiece),
    tipo_registro         VARCHAR(15) NOT NULL CHECK (tipo_registro IN ('DESTINO','DECOMISO')),
    codigo_resultante     VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    producto_resultante   VARCHAR(50) NOT NULL,
    peso_kg               NUMERIC(6,2) NOT NULL,
    lote_resultante       VARCHAR(35) NOT NULL,
    motivo_decomiso       TEXT,
    codigo_etiqueta_barra VARCHAR(50),
    idempotency_key       VARCHAR(64) UNIQUE,
    creado_en             TIMESTAMP   DEFAULT now(),
    eliminado_en          TIMESTAMP
);

-- 8. LOCAL COMERCIAL: VENTA POS Y SNAPSHOT DIARIO DE STOCK -----------------
CREATE TABLE tango_ventas_pos (
    id_ticket_linea        BIGSERIAL PRIMARY KEY,
    sucursal               VARCHAR(30) NOT NULL,
    nro_ticket_factura     VARCHAR(30) NOT NULL,
    fecha_hora             TIMESTAMP   NOT NULL,
    codigo_articulo        VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    descripcion            VARCHAR(100) NOT NULL,
    lote_vendido_escaneado VARCHAR(35),
    kilos_vendidos         NUMERIC(7,2) NOT NULL,
    precio_unitario        NUMERIC(10,2) NOT NULL,
    total_facturado        NUMERIC(12,2) NOT NULL,
    creado_en              TIMESTAMP   DEFAULT now()
);

CREATE TABLE auditoria_stock_cierres_diarios (
    id_cierre                  BIGSERIAL PRIMARY KEY,
    sucursal                   VARCHAR(30) NOT NULL,
    fecha_cierre               DATE        NOT NULL,
    codigo_articulo            VARCHAR(20) NOT NULL REFERENCES catalogo_articulos(codigo_tango),
    stock_inicial_kg           NUMERIC(8,2) NOT NULL,
    ingresos_rei_remitos_kg    NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    ventas_rem_pos_kg          NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    entradas_despiece_spi_kg   NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    salidas_corte_madre_spi_kg NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    decomisos_local_kg         NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    stock_teorico_calculado_kg NUMERIC(8,2) NOT NULL,
    stock_fisico_real_kg       NUMERIC(8,2) NOT NULL,
    diferencia_kg              NUMERIC(7,2) NOT NULL,
    estado_auditoria           VARCHAR(20) NOT NULL CHECK (estado_auditoria IN ('NORMAL','FALTANTE_LEVE','FALTANTE_GRAVE','SOBRANTE')),
    auditor_responsable        BIGINT      NOT NULL REFERENCES catalogo_operarios(id_operario),
    observaciones              TEXT,
    creado_en                  TIMESTAMP   DEFAULT now(),
    CONSTRAINT uq_sucursal_fecha_articulo UNIQUE (sucursal, fecha_cierre, codigo_articulo)
);

-- 9. EVENT LOG INMUTABLE DE TRAZABILIDAD CENTRAL ---------------------------
CREATE TABLE evento_lote (
    id_evento       BIGSERIAL PRIMARY KEY,
    lote            VARCHAR(35) NOT NULL,
    tipo_evento     VARCHAR(25) NOT NULL CHECK (tipo_evento IN ('CREACION','PESAJE','TRANSITO','RECEPCION','TRANSFORMACION','VENTA','DECOMISO','ALERTA_TEMPERATURA')),
    ubicacion       VARCHAR(50) NOT NULL,
    id_operario_fk  BIGINT      NOT NULL REFERENCES catalogo_operarios(id_operario),
    payload_json    JSONB,
    idempotency_key VARCHAR(64) UNIQUE,
    fecha_hora      TIMESTAMP   NOT NULL DEFAULT now()
);

-- 10. ÍNDICES DE RENDIMIENTO Y TRAZABILIDAD ---------------------------------
CREATE INDEX idx_evento_lote_lote ON evento_lote(lote);
CREATE INDEX idx_evento_lote_fecha ON evento_lote(fecha_hora);
CREATE INDEX idx_granja_servicios_cerda ON granja_servicios(id_cerda);
CREATE INDEX idx_granja_partos_cerda ON granja_partos(id_cerda);
CREATE INDEX idx_granja_destetes_lote ON granja_destetes(lote_destete_creado);
CREATE INDEX idx_granja_composicion_engorde ON granja_lote_engorde_composicion(id_lote_engorde_fk);
CREATE INDEX idx_faena_tropas_fecha ON faena_tropas(fecha_faena);
CREATE INDEX idx_faena_medias_reses_tropa ON faena_medias_reses(id_tropa_fk);
CREATE INDEX idx_faena_medias_reses_lote ON faena_medias_reses(lote_media_res);
CREATE INDEX idx_chacinados_bachadas_receta ON chacinados_bachadas(id_receta_fk);
CREATE INDEX idx_spi_sesiones_sucursal_fecha ON spi_despiece_sesiones(sucursal, fecha_hora);
CREATE INDEX idx_spi_resultantes_sesion ON spi_despiece_resultantes(id_sesion_fk);
CREATE INDEX idx_tango_ventas_pos_articulo ON tango_ventas_pos(codigo_articulo);
CREATE INDEX idx_auditoria_stock_sucursal_fecha ON auditoria_stock_cierres_diarios(sucursal, fecha_cierre);

-- 11. PERMISOS DE ROLES -----------------------------------------------------
-- Rol AppSheet / Móvil (app_user): Lectura y escritura operacional
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM app_user; -- Previene borrados accidentales desde la app

-- Rol Terminales Edge Python (edge_user): Inserciones operacionales con idempotencia
GRANT SELECT, INSERT ON faena_medias_reses, chacinados_bachadas, chacinados_ingredientes_consumidos, spi_despiece_sesiones, spi_despiece_resultantes, evento_lote TO edge_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO edge_user;

-- Rol Auditoría (audit_user): Solo lectura y carga de cierres/eventos
GRANT SELECT ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT INSERT ON auditoria_stock_cierres_diarios, evento_lote TO audit_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO audit_user;
