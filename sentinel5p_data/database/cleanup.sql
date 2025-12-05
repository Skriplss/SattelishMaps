-- ============================================================================
-- СКРИПТ ДЛЯ ОЧИСТКИ СТАРОЙ БАЗЫ ДАННЫХ
-- ============================================================================
-- Запусти этот скрипт ПЕРЕД schema.sql если нужно удалить старые таблицы
-- ============================================================================

-- Удалить старые таблицы измерений (если существуют)
DROP TABLE IF EXISTS co_measurements CASCADE;
DROP TABLE IF EXISTS aerosol_measurements CASCADE;
DROP TABLE IF EXISTS so2_measurements CASCADE;
DROP TABLE IF EXISTS o3_measurements CASCADE;
DROP TABLE IF EXISTS no2_measurements CASCADE;

-- Удалить партиции если они были созданы
DROP TABLE IF EXISTS co_measurements_2024_12 CASCADE;
DROP TABLE IF EXISTS co_measurements_2025_01 CASCADE;
DROP TABLE IF EXISTS aerosol_measurements_2024_12 CASCADE;
DROP TABLE IF EXISTS aerosol_measurements_2025_01 CASCADE;
DROP TABLE IF EXISTS so2_measurements_2024_12 CASCADE;
DROP TABLE IF EXISTS so2_measurements_2025_01 CASCADE;
DROP TABLE IF EXISTS o3_measurements_2024_12 CASCADE;
DROP TABLE IF EXISTS o3_measurements_2025_01 CASCADE;
DROP TABLE IF EXISTS no2_measurements_2024_12 CASCADE;
DROP TABLE IF EXISTS no2_measurements_2025_01 CASCADE;
DROP TABLE IF EXISTS no2_measurements_2025_02 CASCADE;

-- Удалить метаданные и спутники
DROP TABLE IF EXISTS measurement_sessions CASCADE;
DROP TABLE IF EXISTS satellites CASCADE;

-- Удалить представления
DROP VIEW IF EXISTS latest_atmospheric_data CASCADE;
DROP VIEW IF EXISTS daily_pollution_summary CASCADE;

-- Удалить функции
DROP FUNCTION IF EXISTS get_measurements_near_point CASCADE;
DROP FUNCTION IF EXISTS get_area_statistics CASCADE;
DROP FUNCTION IF EXISTS detect_pollution_anomalies CASCADE;

-- ============================================================================
-- НЕ УДАЛЯЙ spatial_ref_sys - это системная таблица PostGIS!
-- ============================================================================

-- Готово! Теперь можешь запустить schema.sql
