"""
Скрипт для загрузки данных NO₂ (диоксид азота) со спутника Sentinel-5P
Использует библиотеку sentinelsat для доступа к Copernicus Open Access Hub

Требования:
- Регистрация на https://dataspace.copernicus.eu/
- Установленные библиотеки: sentinelsat, pandas, netCDF4
"""

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date, timedelta
import os
import json


class Sentinel5PDownloader:
    """Класс для загрузки данных Sentinel-5P"""
    
    def __init__(self, username, password, download_dir='../raw_data'):
        """
        Инициализация загрузчика
        
        Args:
            username: Логин Copernicus
            password: Пароль Copernicus
            download_dir: Директория для сохранения файлов
        """
        # Подключение к API Copernicus
        self.api = SentinelAPI(username, password, 'https://apihub.copernicus.eu/apihub')
        self.download_dir = download_dir
        
        # Создать директорию если не существует
        os.makedirs(download_dir, exist_ok=True)
        
    def search_no2_data(self, 
                        start_date, 
                        end_date, 
                        area_coords=None,
                        max_results=10):
        """
        Поиск данных NO₂
        
        Args:
            start_date: Начальная дата (datetime.date или строка 'YYYY-MM-DD')
            end_date: Конечная дата (datetime.date или строка 'YYYY-MM-DD')
            area_coords: Кортеж координат (lon_min, lat_min, lon_max, lat_max) или None для всего мира
            max_results: Максимальное количество результатов
            
        Returns:
            dict: Словарь с найденными продуктами
        """
        # Конвертировать строки в даты если нужно
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        # Определить область поиска
        if area_coords:
            # Формат: (lon_min, lat_min, lon_max, lat_max)
            footprint = f"POLYGON(({area_coords[0]} {area_coords[1]}, " \
                       f"{area_coords[2]} {area_coords[1]}, " \
                       f"{area_coords[2]} {area_coords[3]}, " \
                       f"{area_coords[0]} {area_coords[3]}, " \
                       f"{area_coords[0]} {area_coords[1]}))"
        else:
            footprint = None
            
        # Параметры поиска
        search_params = {
            'platformname': 'Sentinel-5 Precursor',
            'producttype': 'L2__NO2___',  # Продукт Level 2 NO₂
            'date': (start_date, end_date),
        }
        
        if footprint:
            search_params['area'] = footprint
            
        # Выполнить поиск
        print(f"🔍 Поиск данных NO₂ за период {start_date} - {end_date}...")
        products = self.api.query(**search_params)
        
        print(f"✅ Найдено {len(products)} продуктов")
        
        # Ограничить количество результатов
        if len(products) > max_results:
            print(f"⚠️ Ограничение до {max_results} результатов")
            products = dict(list(products.items())[:max_results])
            
        return products
    
    def download_products(self, products):
        """
        Загрузить продукты
        
        Args:
            products: Словарь продуктов из search_no2_data()
            
        Returns:
            dict: Информация о загруженных файлах
        """
        print(f"\n📥 Начало загрузки {len(products)} файлов...")
        
        try:
            result = self.api.download_all(products, directory_path=self.download_dir)
            print(f"✅ Загрузка завершена!")
            return result
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}")
            return None
    
    def get_product_info(self, products):
        """
        Получить информацию о продуктах в читаемом формате
        
        Args:
            products: Словарь продуктов
            
        Returns:
            list: Список с информацией о каждом продукте
        """
        info_list = []
        
        for product_id, product_info in products.items():
            info = {
                'id': product_id,
                'filename': product_info['filename'],
                'date': product_info['beginposition'].strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(product_info['size'] / (1024 * 1024), 2),
                'cloud_cover': product_info.get('cloudcoverpercentage', 'N/A'),
            }
            info_list.append(info)
            
        return info_list


def main():
    """Пример использования"""
    
    # ⚠️ ВАЖНО: Замени на свои учетные данные!
    # Регистрация: https://dataspace.copernicus.eu/
    USERNAME = 'your_username'
    PASSWORD = 'your_password'
    
    # Проверка учетных данных
    if USERNAME == 'your_username' or PASSWORD == 'your_password':
        print("❌ ОШИБКА: Укажите свои учетные данные Copernicus!")
        print("📝 Зарегистрируйся на: https://dataspace.copernicus.eu/")
        return
    
    # Создать загрузчик
    downloader = Sentinel5PDownloader(USERNAME, PASSWORD)
    
    # Пример 1: Поиск данных за последнюю неделю для Украины
    print("=" * 60)
    print("🇺🇦 Пример: Данные NO₂ для Украины за последнюю неделю")
    print("=" * 60)
    
    # Координаты Украины (приблизительно)
    ukraine_coords = (22.0, 44.0, 40.0, 52.5)  # (lon_min, lat_min, lon_max, lat_max)
    
    # Даты
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    # Поиск
    products = downloader.search_no2_data(
        start_date=start_date,
        end_date=end_date,
        area_coords=ukraine_coords,
        max_results=5  # Ограничим для примера
    )
    
    # Показать информацию о найденных продуктах
    if products:
        print("\n📊 Информация о найденных файлах:")
        info = downloader.get_product_info(products)
        
        for i, item in enumerate(info, 1):
            print(f"\n{i}. {item['filename']}")
            print(f"   Дата: {item['date']}")
            print(f"   Размер: {item['size_mb']} MB")
        
        # Спросить пользователя о загрузке
        user_input = input("\n💾 Загрузить эти файлы? (y/n): ")
        
        if user_input.lower() == 'y':
            downloader.download_products(products)
        else:
            print("❌ Загрузка отменена")
    else:
        print("⚠️ Продукты не найдены. Попробуй другой период или область")
    
    # Пример 2: Поиск для определенного города
    print("\n" + "=" * 60)
    print("🏙️ Пример: Данные NO₂ для Киева")
    print("=" * 60)
    
    # Координаты области вокруг Киева (50км радиус)
    kyiv_coords = (30.2, 50.2, 30.8, 50.7)
    
    products_kyiv = downloader.search_no2_data(
        start_date=start_date,
        end_date=end_date,
        area_coords=kyiv_coords,
        max_results=3
    )
    
    if products_kyiv:
        info = downloader.get_product_info(products_kyiv)
        print(f"\n✅ Найдено {len(info)} файлов для Киева")


if __name__ == "__main__":
    main()
