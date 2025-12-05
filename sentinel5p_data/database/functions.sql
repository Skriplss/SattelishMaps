-- ============================================================================
-- ПОЛЕЗНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
-- ============================================================================
-- Запускать ПОСЛЕ создания основной схемы (schema.sql)
-- ============================================================================

-- ============================================================================
-- ФУНКЦИЯ 1: Получить данные в радиусе от точки
-- ============================================================================
-- Пример: найти все измерения NO₂ в радиусе 50км от Киева

CREATE OR REPLACE FUNCTION get_measurements_near_point(
    param_type TEXT,           -- 'NO2', 'O3', 'SO2', 'CO', 'AEROSOL'
    center_lat DECIMAL,        -- Широта центра
    center_lon DECIMAL,        -- Долгота центра
    radius_km DECIMAL,         -- Радиус в километрах
    days_back INTEGER DEFAULT 7 -- Сколько дней назад искать
)
RETURNS TABLE (
    measurement_id BIGINT,
    timestamp TIMESTAMPTZ,
    latitude DECIMAL,
    longitude DECIMAL,
    value DECIMAL,
    qa_value DECIMAL,
    distance_km DECIMAL
) AS $$
BEGIN
    -- Создать точку центра
    DECLARE
        center_point GEOMETRY := ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326);
    BEGIN
        -- В зависимости от типа параметра, выбрать нужную таблицу
        IF param_type = 'NO2' THEN
            RETURN QUERY
            SELECT 
                n.id,
                n.timestamp,
                n.latitude,
                n.longitude,
                n.no2_column,
                n.qa_value,
                ROUND(ST_Distance(n.location::geography, center_point::geography) / 1000, 2) as distance_km
            FROM no2_measurements n
            WHERE n.timestamp > NOW() - INTERVAL '1 day' * days_back
                AND ST_DWithin(n.location::geography, center_point::geography, radius_km * 1000)
                AND n.qa_value > 0.75
            ORDER BY n.timestamp DESC;
            
        ELSIF param_type = 'O3' THEN
            RETURN QUERY
            SELECT 
                o.id,
                o.timestamp,
                o.latitude,
                o.longitude,
                o.o3_column,
                o.qa_value,
                ROUND(ST_Distance(o.location::geography, center_point::geography) / 1000, 2)
            FROM o3_measurements o
            WHERE o.timestamp > NOW() - INTERVAL '1 day' * days_back
                AND ST_DWithin(o.location::geography, center_point::geography, radius_km * 1000)
                AND o.qa_value > 0.75
            ORDER BY o.timestamp DESC;
            
        ELSIF param_type = 'SO2' THEN
            RETURN QUERY
            SELECT 
                s.id,
                s.timestamp,
                s.latitude,
                s.longitude,
                s.so2_column,
                s.qa_value,
                ROUND(ST_Distance(s.location::geography, center_point::geography) / 1000, 2)
            FROM so2_measurements s
            WHERE s.timestamp > NOW() - INTERVAL '1 day' * days_back
                AND ST_DWithin(s.location::geography, center_point::geography, radius_km * 1000)
                AND s.qa_value > 0.75
            ORDER BY s.timestamp DESC;
            
        ELSIF param_type = 'CO' THEN
            RETURN QUERY
            SELECT 
                c.id,
                c.timestamp,
                c.latitude,
                c.longitude,
                c.co_column,
                c.qa_value,
                ROUND(ST_Distance(c.location::geography, center_point::geography) / 1000, 2)
            FROM co_measurements c
            WHERE c.timestamp > NOW() - INTERVAL '1 day' * days_back
                AND ST_DWithin(c.location::geography, center_point::geography, radius_km * 1000)
                AND c.qa_value > 0.75
            ORDER BY c.timestamp DESC;
        END IF;
    END;
END;
$$ LANGUAGE plpgsql;

-- Пример использования:
-- SELECT * FROM get_measurements_near_point('NO2', 50.4501, 30.5234, 50, 7);
-- (Киев, радиус 50км, последние 7 дней)

-- ============================================================================
-- ФУНКЦИЯ 2: Статистика по области (bounding box)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_area_statistics(
    param_type TEXT,
    min_lat DECIMAL,
    min_lon DECIMAL,
    max_lat DECIMAL,
    max_lon DECIMAL,
    start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '7 days',
    end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    avg_value DECIMAL,
    min_value DECIMAL,
    max_value DECIMAL,
    median_value DECIMAL,
    std_dev DECIMAL,
    measurement_count BIGINT
) AS $$
BEGIN
    IF param_type = 'NO2' THEN
        RETURN QUERY
        SELECT 
            ROUND(AVG(no2_column)::DECIMAL, 4),
            ROUND(MIN(no2_column)::DECIMAL, 4),
            ROUND(MAX(no2_column)::DECIMAL, 4),
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY no2_column)::DECIMAL, 4),
            ROUND(STDDEV(no2_column)::DECIMAL, 4),
            COUNT(*)
        FROM no2_measurements
        WHERE latitude BETWEEN min_lat AND max_lat
            AND longitude BETWEEN min_lon AND max_lon
            AND timestamp BETWEEN start_date AND end_date
            AND qa_value > 0.75;
            
    ELSIF param_type = 'O3' THEN
        RETURN QUERY
        SELECT 
            ROUND(AVG(o3_column)::DECIMAL, 4),
            ROUND(MIN(o3_column)::DECIMAL, 4),
            ROUND(MAX(o3_column)::DECIMAL, 4),
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY o3_column)::DECIMAL, 4),
            ROUND(STDDEV(o3_column)::DECIMAL, 4),
            COUNT(*)
        FROM o3_measurements
        WHERE latitude BETWEEN min_lat AND max_lat
            AND longitude BETWEEN min_lon AND max_lon
            AND timestamp BETWEEN start_date AND end_date
            AND qa_value > 0.75;
            
    ELSIF param_type = 'SO2' THEN
        RETURN QUERY
        SELECT 
            ROUND(AVG(so2_column)::DECIMAL, 4),
            ROUND(MIN(so2_column)::DECIMAL, 4),
            ROUND(MAX(so2_column)::DECIMAL, 4),
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY so2_column)::DECIMAL, 4),
            ROUND(STDDEV(so2_column)::DECIMAL, 4),
            COUNT(*)
        FROM so2_measurements
        WHERE latitude BETWEEN min_lat AND max_lat
            AND longitude BETWEEN min_lon AND max_lon
            AND timestamp BETWEEN start_date AND end_date
            AND qa_value > 0.75;
            
    ELSIF param_type = 'CO' THEN
        RETURN QUERY
        SELECT 
            ROUND(AVG(co_column)::DECIMAL, 4),
            ROUND(MIN(co_column)::DECIMAL, 4),
            ROUND(MAX(co_column)::DECIMAL, 4),
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY co_column)::DECIMAL, 4),
            ROUND(STDDEV(co_column)::DECIMAL, 4),
            COUNT(*)
        FROM co_measurements
        WHERE latitude BETWEEN min_lat AND max_lat
            AND longitude BETWEEN min_lon AND max_lon
            AND timestamp BETWEEN start_date AND end_date
            AND qa_value > 0.75;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Пример использования:
-- SELECT * FROM get_area_statistics('NO2', 50.0, 30.0, 51.0, 31.0);
-- (Статистика NO₂ для области Киева)

-- ============================================================================
-- ФУНКЦИЯ 3: Определение аномалий (превышение порогов)
-- ============================================================================

CREATE OR REPLACE FUNCTION detect_pollution_anomalies(
    param_type TEXT,
    threshold_multiplier DECIMAL DEFAULT 2.0, -- Во сколько раз выше среднего
    days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    measurement_id BIGINT,
    timestamp TIMESTAMPTZ,
    latitude DECIMAL,
    longitude DECIMAL,
    value DECIMAL,
    avg_value DECIMAL,
    deviation_percent DECIMAL
) AS $$
DECLARE
    avg_val DECIMAL;
BEGIN
    -- Рассчитать среднее значение за период
    IF param_type = 'NO2' THEN
        SELECT AVG(no2_column) INTO avg_val 
        FROM no2_measurements 
        WHERE timestamp > NOW() - INTERVAL '1 day' * days_back
            AND qa_value > 0.75;
            
        RETURN QUERY
        SELECT 
            n.id,
            n.timestamp,
            n.latitude,
            n.longitude,
            n.no2_column,
            avg_val,
            ROUND(((n.no2_column - avg_val) / avg_val * 100)::DECIMAL, 2)
        FROM no2_measurements n
        WHERE n.timestamp > NOW() - INTERVAL '1 day' * days_back
            AND n.qa_value > 0.75
            AND n.no2_column > avg_val * threshold_multiplier
        ORDER BY n.no2_column DESC;
        
    ELSIF param_type = 'CO' THEN
        SELECT AVG(co_column) INTO avg_val 
        FROM co_measurements 
        WHERE timestamp > NOW() - INTERVAL '1 day' * days_back
            AND qa_value > 0.75;
            
        RETURN QUERY
        SELECT 
            c.id,
            c.timestamp,
            c.latitude,
            c.longitude,
            c.co_column,
            avg_val,
            ROUND(((c.co_column - avg_val) / avg_val * 100)::DECIMAL, 2)
        FROM co_measurements c
        WHERE c.timestamp > NOW() - INTERVAL '1 day' * days_back
            AND c.qa_value > 0.75
            AND c.co_column > avg_val * threshold_multiplier
        ORDER BY c.co_column DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Пример использования:
-- SELECT * FROM detect_pollution_anomalies('NO2', 2.0, 7);
-- (Найти точки где NO₂ в 2 раза выше среднего за последние 7 дней)

-- ============================================================================
-- ПРЕДСТАВЛЕНИЕ: Агрегированные данные по дням
-- ============================================================================

CREATE OR REPLACE VIEW daily_pollution_summary AS
SELECT 
    DATE(timestamp) as measurement_date,
    'NO2' as parameter,
    COUNT(*) as measurement_count,
    ROUND(AVG(no2_column)::DECIMAL, 4) as avg_value,
    ROUND(MIN(no2_column)::DECIMAL, 4) as min_value,
    ROUND(MAX(no2_column)::DECIMAL, 4) as max_value
FROM no2_measurements
WHERE qa_value > 0.75
GROUP BY DATE(timestamp)

UNION ALL

SELECT 
    DATE(timestamp),
    'O3',
    COUNT(*),
    ROUND(AVG(o3_column)::DECIMAL, 4),
    ROUND(MIN(o3_column)::DECIMAL, 4),
    ROUND(MAX(o3_column)::DECIMAL, 4)
FROM o3_measurements
WHERE qa_value > 0.75
GROUP BY DATE(timestamp)

UNION ALL

SELECT 
    DATE(timestamp),
    'SO2',
    COUNT(*),
    ROUND(AVG(so2_column)::DECIMAL, 4),
    ROUND(MIN(so2_column)::DECIMAL, 4),
    ROUND(MAX(so2_column)::DECIMAL, 4)
FROM so2_measurements
WHERE qa_value > 0.75
GROUP BY DATE(timestamp)

UNION ALL

SELECT 
    DATE(timestamp),
    'CO',
    COUNT(*),
    ROUND(AVG(co_column)::DECIMAL, 4),
    ROUND(MIN(co_column)::DECIMAL, 4),
    ROUND(MAX(co_column)::DECIMAL, 4)
FROM co_measurements
WHERE qa_value > 0.75
GROUP BY DATE(timestamp)

ORDER BY measurement_date DESC, parameter;

COMMENT ON VIEW daily_pollution_summary IS 'Ежедневная сводка по всем параметрам загрязнения';

-- ============================================================================
-- ГОТОВО!
-- ============================================================================
-- Функции созданы и готовы к использованию
