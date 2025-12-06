# Frontend Architecture

Vanilla JavaScript frontend з MapLibre GL для візуалізації супутникових даних.

## Технології

- **MapLibre GL JS 3.x** - Інтерактивні карти
- **Vanilla JavaScript (ES6+)** - Без фреймворків
- **CSS3** - Сучасна стилізація

## Структура

```
frontend/
├── index.html          # Головна сторінка
├── js/
│   ├── main.js        # Точка входу
│   ├── map.js         # MapLibre компонент
│   ├── api.js         # API інтеграція
│   ├── filters.js     # Фільтри
│   ├── colormap.js    # Кольорові карти
│   └── utils.js       # Утиліти
├── css/
│   ├── styles.css     # Головні стилі
│   ├── map.css        # Стилі карти
│   └── filters.css    # Стилі фільтрів
└── assets/
    └── icons/         # Іконки
```

## Компоненти

### Map Component ([map.js](map-component.md))
- Ініціалізація MapLibre GL
- Управління шарами
- Події карти

### API Integration ([api.js](api-integration.md))
- HTTP запити до backend
- Обробка відповідей
- Error handling

### Filters System ([filters.js](filters.md))
- Фільтри за датою
- Фільтри за хмарністю
- Фільтри за індексами

### Color Mapping ([colormap.js](colormap.md))
- Кольорові схеми для NDVI, NDWI, NDBI
- Легенда

## Детальна документація

- [Структура](structure.md)
- [Компонент карти](map-component.md)
- [API інтеграція](api-integration.md)
- [Фільтри](filters.md)
- [Colormap](colormap.md)
- [Стилізація](styling.md)
