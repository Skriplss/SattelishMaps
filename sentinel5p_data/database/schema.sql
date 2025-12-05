-- ============================================================================
-- СХЕМА БАЗЫ ДАННЫХ ДЛЯ SENTINEL-5P АТМОСФЕРНЫХ ДАННЫХ
-- ============================================================================
-- Описание: Структура БД для хранения данных о загрязнении воздуха
-- Параметры: NO₂, O₃, SO₂, AER_AI, CO
-- СУБД: PostgreSQL (Supabase)
-- ============================================================================

-- Включить расширение PostGIS для работы с геоданными
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- ТАБЛИЦА 1: СПУТНИКИ
-- ============================================================================
-- Информация о спутниках, собирающих данные

CREATE TABLE satellites (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    mission_type TEXT DEFAULT 'atmospheric_monitoring',
    launch_date TIMESTAMPTZ,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'decommissioned')),
    description TEXT,
    metadata JSONB, -- Дополнительная информация
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индекс для быстрого поиска активных спутников
CREATE INDEX idx_satellites_status ON satellites(status);

-- Комментарии
COMMENT ON TABLE satellites IS 'Информация о спутниках для мониторинга атмосферы';
COMMENT ON COLUMN satellites.metadata IS 'Дополнительные данные: орбита, инструменты и т.д.';

-- Вставить Sentinel-5P
INSERT INTO satellites (name, mission_type, launch_date, status, description) VALUES
('Sentinel-5P', 'atmospheric_monitoring', '2017-10-13', 'active', 
 'Sentinel-5 Precursor - спутник для мониторинга качества воздуха и состава атмосферы');

-- ============================================================================
-- ТАБЛИЦА 2: СЕССИИ ИЗМЕРЕНИЙ (МЕТАДАННЫЕ ФАЙЛОВ)
-- ============================================================================
-- Информация о загруженных файлах NetCDF

CREATE TABLE measurement_sessions (
    id BIGSERIAL PRIMARY KEY,
    satellite_id BIGINT NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    
    -- Информация о продукте
    product_type TEXT NOT NULL CHECK (product_type IN (
        'L2__NO2___', 'L2__O3____', 'L2__SO2___', 
        'L2__AER_AI', 'L2__CO____'
    )),
    product_level TEXT DEFAULT 'L2',
    
    -- Файл
    filename TEXT NOT NULL UNIQUE,
    file_size_mb DECIMAL(10, 2),
    file_hash TEXT, -- SHA256 для проверки целостности
    
    -- Временные данные
    measurement_start TIMESTAMPTZ NOT NULL,
    measurement_end TIMESTAMPTZ NOT NULL,
    
    -- Географическое покрытие
    bbox_geometry GEOMETRY(POLYGON, 4326), -- Bounding box области
    center_point GEOMETRY(POINT, 4326),
    
    -- Качество данных
    data_quality JSONB, -- Метрики: облачность, валидные пиксели и т.д.
    processing_version TEXT,
    
    -- Статус обработки
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN (
        'pending', 'processing', 'completed', 'failed'
    )),
    error_message TEXT,
    
    -- Временные метки
    downloaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    uploaded_to_db_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_sessions_satellite ON measurement_sessions(satellite_id);
CREATE INDEX idx_sessions_product_type ON measurement_sessions(product_type);
CREATE INDEX idx_sessions_measurement_start ON measurement_sessions(measurement_start DESC);
CREATE INDEX idx_sessions_status ON measurement_sessions(processing_status);
CREATE INDEX idx_sessions_bbox ON measurement_sessions USING GIST(bbox_geometry);

COMMENT ON TABLE measurement_sessions IS 'Метаданные загруженных файлов Sentinel-5P';

-- ============================================================================
-- ТАБЛИЦА 3: NO₂ ИЗМЕРЕНИЯ (ДИОКСИД АЗОТА)
-- ============================================================================
-- Данные о концентрации диоксида азота

CREATE TABLE no2_measurements (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES measurement_sessions(id) ON DELETE CASCADE,
    
    -- Геолокация
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(11, 7),
    
    -- Временная метка
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Данные NO₂
    no2_column DECIMAL(12, 6), -- Тропосферная колонка NO₂ (µmol/m²)
    no2_column_precision DECIMAL(12, 6), -- Точность измерения
    
    -- Качество
    qa_value DECIMAL(5, 4), -- Quality Assurance (0-1, >0.75 = хорошее)
    cloud_fraction DECIMAL(5, 4), -- Облачность (0-1)
    
    -- Дополнительно
    surface_albedo DECIMAL(5, 4), -- Альбедо поверхности
    solar_zenith_angle DECIMAL(6, 2), -- Угол солнца
    
    -- Метаданные
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX idx_no2_session ON no2_measurements(session_id);
CREATE INDEX idx_no2_location ON no2_measurements USING GIST(location);
CREATE INDEX idx_no2_timestamp ON no2_measurements(timestamp DESC);
CREATE INDEX idx_no2_qa ON no2_measurements(qa_value) WHERE qa_value > 0.75;

COMMENT ON TABLE no2_measurements IS 'Измерения концентрации диоксида азота (NO₂)';
COMMENT ON COLUMN no2_measurements.no2_column IS 'Тропосферная колонка NO₂ в µmol/m²';
COMMENT ON COLUMN no2_measurements.qa_value IS 'Качество данных: >0.75 рекомендуется';

-- ============================================================================
-- ТАБЛИЦА 4: O₃ ИЗМЕРЕНИЯ (ОЗОН)
-- ============================================================================

CREATE TABLE o3_measurements (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES measurement_sessions(id) ON DELETE CASCADE,
    
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(11, 7),
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Данные озона
    o3_column DECIMAL(12, 6), -- Общая колонка озона (DU - Dobson Units)
    o3_column_precision DECIMAL(12, 6),
    
    -- Качество
    qa_value DECIMAL(5, 4),
    cloud_fraction DECIMAL(5, 4),
    
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_o3_session ON o3_measurements(session_id);
CREATE INDEX idx_o3_location ON o3_measurements USING GIST(location);
CREATE INDEX idx_o3_timestamp ON o3_measurements(timestamp DESC);

COMMENT ON TABLE o3_measurements IS 'Измерения концентрации озона (O₃)';

-- ============================================================================
-- ТАБЛИЦА 5: SO₂ ИЗМЕРЕНИЯ (СЕРНИСТЫЙ ГАЗ)
-- ============================================================================

CREATE TABLE so2_measurements (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES measurement_sessions(id) ON DELETE CASCADE,
    
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(11, 7),
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Данные SO₂
    so2_column DECIMAL(12, 6), -- Колонка SO₂ (DU)
    so2_column_precision DECIMAL(12, 6),
    so2_layer_height DECIMAL(8, 2), -- Высота слоя (км)
    
    -- Качество
    qa_value DECIMAL(5, 4),
    cloud_fraction DECIMAL(5, 4),
    
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_so2_session ON so2_measurements(session_id);
CREATE INDEX idx_so2_location ON so2_measurements USING GIST(location);
CREATE INDEX idx_so2_timestamp ON so2_measurements(timestamp DESC);

COMMENT ON TABLE so2_measurements IS 'Измерения концентрации сернистого газа (SO₂)';

-- ============================================================================
-- ТАБЛИЦА 6: АЭРОЗОЛЬНЫЙ ИНДЕКС
-- ============================================================================

CREATE TABLE aerosol_measurements (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES measurement_sessions(id) ON DELETE CASCADE,
    
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(11, 7),
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Аэрозольный индекс
    aerosol_index_340_380 DECIMAL(10, 6), -- AI на 340/380 нм
    aerosol_index_354_388 DECIMAL(10, 6), -- AI на 354/388 нм
    aerosol_optical_depth DECIMAL(10, 6), -- Оптическая толщина
    
    -- Качество
    qa_value DECIMAL(5, 4),
    cloud_fraction DECIMAL(5, 4),
    
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_aerosol_session ON aerosol_measurements(session_id);
CREATE INDEX idx_aerosol_location ON aerosol_measurements USING GIST(location);
CREATE INDEX idx_aerosol_timestamp ON aerosol_measurements(timestamp DESC);

COMMENT ON TABLE aerosol_measurements IS 'Измерения аэрозольного индекса (дым, пыль, PM2.5)';

-- ============================================================================
-- ТАБЛИЦА 7: CO ИЗМЕРЕНИЯ (УГАРНЫЙ ГАЗ)
-- ============================================================================

CREATE TABLE co_measurements (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES measurement_sessions(id) ON DELETE CASCADE,
    
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(11, 7),
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Данные CO
    co_column DECIMAL(12, 6), -- Колонка CO (mol/m²)
    co_column_precision DECIMAL(12, 6),
    
    -- Качество
    qa_value DECIMAL(5, 4),
    cloud_fraction DECIMAL(5, 4),
    
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_co_session ON co_measurements(session_id);
CREATE INDEX idx_co_location ON co_measurements USING GIST(location);
CREATE INDEX idx_co_timestamp ON co_measurements(timestamp DESC);

COMMENT ON TABLE co_measurements IS 'Измерения концентрации угарного газа (CO)';

-- ============================================================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ АНАЛИТИКИ
-- ============================================================================

-- Последние данные по всем параметрам
CREATE VIEW latest_atmospheric_data AS
SELECT 
    'NO2' as parameter,
    location,
    timestamp,
    no2_column as value,    
    qa_value,
    session_id
FROM no2_measurements
WHERE timestamp > NOW() - INTERVAL '7 days'
    AND qa_value > 0.75

UNION ALL

SELECT 
    'O3' as parameter,
    location,
    timestamp,
    o3_column as value,
    qa_value,
    session_id
FROM o3_measurements
WHERE timestamp > NOW() - INTERVAL '7 days'
    AND qa_value > 0.75

UNION ALL

SELECT 
    'SO2' as parameter,
    location,
    timestamp,
    so2_column as value,
    qa_value,
    session_id
FROM so2_measurements
WHERE timestamp > NOW() - INTERVAL '7 days'
    AND qa_value > 0.75

UNION ALL

SELECT 
    'CO' as parameter,
    location,
    timestamp,
    co_column as value,
    qa_value,
    session_id
FROM co_measurements
WHERE timestamp > NOW() - INTERVAL '7 days'
    AND qa_value > 0.75;

COMMENT ON VIEW latest_atmospheric_data IS 'Последние данные за 7 дней по всем параметрам';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Включить RLS для всех таблиц
ALTER TABLE satellites ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurement_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE no2_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE o3_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE so2_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE aerosol_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE co_measurements ENABLE ROW LEVEL SECURITY;

-- Политика: все могут читать данные
CREATE POLICY "Public read access" ON satellites FOR SELECT USING (true);
CREATE POLICY "Public read access" ON measurement_sessions FOR SELECT USING (true);
CREATE POLICY "Public read access" ON no2_measurements FOR SELECT USING (true);
CREATE POLICY "Public read access" ON o3_measurements FOR SELECT USING (true);
CREATE POLICY "Public read access" ON so2_measurements FOR SELECT USING (true);
CREATE POLICY "Public read access" ON aerosol_measurements FOR SELECT USING (true);
CREATE POLICY "Public read access" ON co_measurements FOR SELECT USING (true);

-- Политика: только авторизованные могут вставлять
CREATE POLICY "Authenticated insert" ON measurement_sessions 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert" ON no2_measurements 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert" ON o3_measurements 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert" ON so2_measurements 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert" ON aerosol_measurements 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated insert" ON co_measurements 
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- ============================================================================
-- ГОТОВО!
-- ============================================================================
-- Схема базы данных создана
-- Следующий шаг: запустить этот скрипт в Supabase SQL Editor
