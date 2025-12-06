# API Documentation

REST API для доступу до супутникових даних та статистики.

## Base URL

```
http://localhost:8000/api
```

## Автентифікація

API наразі не вимагає автентифікації для read-only операцій.

## Endpoints

### Satellite Data
- [GET /satellite/images](satellite.md#get-images) - Список супутникових знімків
- [GET /satellite/image/{id}](satellite.md#get-image) - Деталі знімка

### Statistics
- [GET /statistics/region](statistics.md#get-region-stats) - Статистика для регіону
- [GET /statistics/timeseries](statistics.md#get-timeseries) - Часовий ряд

### Indices
- [GET /indices/ndvi](indices.md#get-ndvi) - NDVI дані
- [GET /indices/ndwi](indices.md#get-ndwi) - NDWI дані
- [GET /indices/ndbi](indices.md#get-ndbi) - NDBI дані
- [GET /indices/moisture](indices.md#get-moisture) - Moisture дані

### Scheduler
- [GET /scheduler/status](satellite.md#scheduler-status) - Статус scheduler

## Quick Examples

### Отримати статистику

```bash
curl "http://localhost:8000/api/statistics/region?region_name=Trnava&date_from=2024-01-01&date_to=2024-12-31"
```

### Отримати NDVI

```bash
curl "http://localhost:8000/api/indices/ndvi?region_name=Trnava&limit=10"
```

## Response Format

Всі відповіді у JSON форматі:

```json
{
  "data": [...],
  "count": 10,
  "message": "Success"
}
```

## Error Handling

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Rate Limiting

Наразі немає rate limiting для локального використання.

## Детальна документація

- [Satellite Endpoints](satellite.md)
- [Statistics Endpoints](statistics.md)
- [Indices Endpoints](indices.md)
- [Examples](examples.md)
