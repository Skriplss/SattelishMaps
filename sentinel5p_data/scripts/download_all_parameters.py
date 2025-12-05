"""
Универсальный загрузчик данных Sentinel-5P для всех параметров
Поддерживает: NO₂, O₃, SO₂, AER_AI, CO
"""

from sentinelsat import SentinelAPI
from datetime import date, timedelta
import os
import json
from pathlib import Path


# Типы продуктов Sentinel-5P
PRODUCT_TYPES = {
    'NO2': 'L2__NO2___',   # Диоксид азота
    'O3': 'L2__O3____',    # Озон
    'SO2': 'L2__SO2___',   # Сернистый газ
    'AER_AI': 'L2__AER_AI', # Аэрозольный индекс
    'CO': 'L2__CO____'     # Угарный газ
}


class Sentinel5PMultiDownloader:
    """Загрузчик для всех параметров Sentinel-5P"""
    
    def __init__(self, username, password, base_download_dir='../raw_data'):
        """
        Инициализация
        
        Args:
            username: Логин Copernicus
            password: Пароль Copernicus
            base_download_dir: Базовая директория для загрузки
        """
        self.api = SentinelAPI(username, password, 'https://apihub.copernicus.eu/apihub')
        self.base_download_dir = Path(base_download_dir)
        
        # Создать поддиректории для каждого параметра
        for param in PRODUCT_TYPES.keys():
            param_dir = self.base_download_dir / param.lower()
            param_dir.mkdir(parents=True, exist_ok=True)
    
    def search_products(self, 
                       parameter,
                       start_date, 
                       end_date, 
                       area_coords=None,
                       max_results=10):
        """
        Поиск продуктов для конкретного параметра
        
        Args:
            parameter: 'NO2', 'O3', 'SO2', 'AER_AI', 'CO'
            start_date: Начальная дата
            end_date: Конечная дата
            area_coords: (lon_min, lat_min, lon_max, lat_max) или None
            max_results: Максимальное количество результатов
            
        Returns:
            dict: Найденные продукты
        """
        if parameter not in PRODUCT_TYPES:
            raise ValueError(f"Неизвестный параметр: {parameter}. Доступны: {list(PRODUCT_TYPES.keys())}")
        
        product_type = PRODUCT_TYPES[parameter]
        
        # Конвертировать даты
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        # Область поиска
        if area_coords:
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
            'producttype': product_type,
            'date': (start_date, end_date),
        }
        
        if footprint:
            search_params['area'] = footprint
        
        print(f"\n🔍 Поиск {parameter} за период {start_date} - {end_date}...")
        products = self.api.query(**search_params)
        
        print(f"✅ Найдено {len(products)} продуктов {parameter}")
        
        # Ограничить результаты
        if len(products) > max_results:
            print(f"⚠️ Ограничение до {max_results} результатов")
            products = dict(list(products.items())[:max_results])
        
        return products
    
    def download_products(self, products, parameter):
        """
        Загрузить продукты в соответствующую папку
        
        Args:
            products: Словарь продуктов
            parameter: Тип параметра для определения папки
        """
        download_dir = self.base_download_dir / parameter.lower()
        
        print(f"\n📥 Загрузка {len(products)} файлов {parameter} в {download_dir}...")
        
        try:
            result = self.api.download_all(products, directory_path=str(download_dir))
            print(f"✅ Загрузка {parameter} завершена!")
            return result
        except Exception as e:
            print(f"❌ Ошибка при загрузке {parameter}: {e}")
            return None
    
    def download_all_parameters(self,
                                start_date,
                                end_date,
                                area_coords=None,
                                parameters=None,
                                max_results_per_param=5):
        """
        Загрузить данные для всех параметров
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            area_coords: Координаты области
            parameters: Список параметров или None для всех
            max_results_per_param: Макс. результатов на параметр
        """
        if parameters is None:
            parameters = list(PRODUCT_TYPES.keys())
        
        results = {}
        
        for param in parameters:
            print("\n" + "=" * 60)
            print(f"📊 Параметр: {param}")
            print("=" * 60)
            
            try:
                # Поиск
                products = self.search_products(
                    parameter=param,
                    start_date=start_date,
                    end_date=end_date,
                    area_coords=area_coords,
                    max_results=max_results_per_param
                )
                
                if products:
                    # Загрузка
                    result = self.download_products(products, param)
                    results[param] = {
                        'products_found': len(products),
                        'download_result': result
                    }
                else:
                    print(f"⚠️ Продукты {param} не найдены")
                    results[param] = {
                        'products_found': 0,
                        'download_result': None
                    }
                    
            except Exception as e:
                print(f"❌ Ошибка для {param}: {e}")
                results[param] = {
                    'error': str(e)
                }
        
        return results
    
    def get_product_info(self, products):
        """Получить информацию о продуктах"""
        info_list = []
        
        for product_id, product_info in products.items():
            info = {
                'id': product_id,
                'filename': product_info['filename'],
                'date': product_info['beginposition'].strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(product_info['size'] / (1024 * 1024), 2),
            }
            info_list.append(info)
        
        return info_list


def main():
    """Пример использования"""
    
    # ⚠️ ВАЖНО: Укажи свои учетные данные!
    USERNAME = 'your_username'
    PASSWORD = 'your_password'
    
    if USERNAME == 'your_username' or PASSWORD == 'your_password':
        print("❌ ОШИБКА: Укажи свои учетные данные Copernicus!")
        print("📝 Зарегистрируйся на: https://dataspace.copernicus.eu/")
        return
    
    # Создать загрузчик
    downloader = Sentinel5PMultiDownloader(USERNAME, PASSWORD)
    
    # Параметры поиска
    end_date = date.today()
    start_date = end_date - timedelta(days=3)  # Последние 3 дня
    
    # Координаты Украины
    ukraine_coords = (22.0, 44.0, 40.0, 52.5)
    
    print("=" * 60)
    print("🛰️ ЗАГРУЗКА ДАННЫХ SENTINEL-5P")
    print("=" * 60)
    print(f"📅 Период: {start_date} - {end_date}")
    print(f"📍 Область: Украина")
    print(f"📊 Параметры: NO₂, O₃, SO₂, AER_AI, CO")
    print("=" * 60)
    
    # Вариант 1: Загрузить все параметры
    results = downloader.download_all_parameters(
        start_date=start_date,
        end_date=end_date,
        area_coords=ukraine_coords,
        max_results_per_param=2  # По 2 файла на параметр для теста
    )
    
    # Показать итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ЗАГРУЗКИ")
    print("=" * 60)
    
    for param, result in results.items():
        if 'error' in result:
            print(f"❌ {param}: Ошибка - {result['error']}")
        else:
            print(f"✅ {param}: Найдено {result['products_found']} файлов")
    
    # Вариант 2: Загрузить только конкретные параметры
    print("\n" + "=" * 60)
    print("🎯 ЗАГРУЗКА ТОЛЬКО NO₂ И CO")
    print("=" * 60)
    
    results_selective = downloader.download_all_parameters(
        start_date=start_date,
        end_date=end_date,
        area_coords=ukraine_coords,
        parameters=['NO2', 'CO'],  # Только эти параметры
        max_results_per_param=3
    )


if __name__ == "__main__":
    main()
