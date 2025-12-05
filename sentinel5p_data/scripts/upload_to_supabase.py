"""
Скрипт для загрузки обработанных данных Sentinel-5P в Supabase
Поддерживает все параметры: NO₂, O₃, SO₂, AER_AI, CO
"""

from supabase import create_client, Client
import netCDF4 as nc
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
import json


class SupabaseUploader:
    """Загрузчик данных в Supabase"""
    
    def __init__(self, supabase_url, supabase_key):
        """
        Инициализация
        
        Args:
            supabase_url: URL проекта Supabase
            supabase_key: Anon ключ Supabase
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Маппинг типов продуктов к таблицам
        self.product_to_table = {
            'L2__NO2___': 'no2_measurements',
            'L2__O3____': 'o3_measurements',
            'L2__SO2___': 'so2_measurements',
            'L2__AER_AI': 'aerosol_measurements',
            'L2__CO____': 'co_measurements'
        }
        
        # Маппинг переменных в NetCDF файлах
        self.variable_mappings = {
            'L2__NO2___': {
                'main_var': 'nitrogendioxide_tropospheric_column',
                'precision_var': 'nitrogendioxide_tropospheric_column_precision',
                'column_name': 'no2_column',
                'precision_name': 'no2_column_precision'
            },
            'L2__O3____': {
                'main_var': 'ozone_total_vertical_column',
                'precision_var': 'ozone_total_vertical_column_precision',
                'column_name': 'o3_column',
                'precision_name': 'o3_column_precision'
            },
            'L2__SO2___': {
                'main_var': 'sulfurdioxide_total_vertical_column',
                'precision_var': 'sulfurdioxide_total_vertical_column_precision',
                'column_name': 'so2_column',
                'precision_name': 'so2_column_precision'
            },
            'L2__AER_AI': {
                'main_var': 'aerosol_index_340_380',
                'column_name': 'aerosol_index_340_380'
            },
            'L2__CO____': {
                'main_var': 'carbonmonoxide_total_column',
                'precision_var': 'carbonmonoxide_total_column_precision',
                'column_name': 'co_column',
                'precision_name': 'co_column_precision'
            }
        }
    
    def get_satellite_id(self, satellite_name='Sentinel-5P'):
        """Получить ID спутника из БД"""
        response = self.supabase.table('satellites')\
            .select('id')\
            .eq('name', satellite_name)\
            .execute()
        
        if response.data:
            return response.data[0]['id']
        else:
            raise ValueError(f"Спутник {satellite_name} не найден в БД")
    
    def calculate_file_hash(self, file_path):
        """Рассчитать SHA256 хеш файла"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def create_measurement_session(self, netcdf_file_path, product_type):
        """
        Создать запись о сессии измерений
        
        Args:
            netcdf_file_path: Путь к NetCDF файлу
            product_type: Тип продукта (L2__NO2___ и т.д.)
            
        Returns:
            int: ID созданной сессии
        """
        file_path = Path(netcdf_file_path)
        
        # Открыть файл для чтения метаданных
        dataset = nc.Dataset(file_path, 'r')
        
        try:
            # Получить метаданные
            product_group = dataset.groups.get('PRODUCT', dataset)
            
            # Время измерений
            time_var = product_group.variables.get('time')
            if time_var:
                time_data = time_var[:]
                # Конвертировать в datetime (обычно это секунды с 2010-01-01)
                base_time = datetime(2010, 1, 1)
                measurement_start = base_time + timedelta(seconds=float(time_data.min()))
                measurement_end = base_time + timedelta(seconds=float(time_data.max()))
            else:
                measurement_start = datetime.now()
                measurement_end = datetime.now()
            
            # Размер файла
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Хеш файла
            file_hash = self.calculate_file_hash(file_path)
            
            # Данные для вставки
            session_data = {
                'satellite_id': self.get_satellite_id(),
                'product_type': product_type,
                'filename': file_path.name,
                'file_size_mb': round(file_size_mb, 2),
                'file_hash': file_hash,
                'measurement_start': measurement_start.isoformat(),
                'measurement_end': measurement_end.isoformat(),
                'processing_status': 'processing'
            }
            
            # Вставить в БД
            response = self.supabase.table('measurement_sessions')\
                .insert(session_data)\
                .execute()
            
            session_id = response.data[0]['id']
            print(f"✅ Создана сессия #{session_id} для {file_path.name}")
            
            return session_id
            
        finally:
            dataset.close()
    
    def upload_measurements(self, netcdf_file_path, product_type, session_id, sample_rate=10):
        """
        Загрузить измерения из NetCDF файла в Supabase
        
        Args:
            netcdf_file_path: Путь к файлу
            product_type: Тип продукта
            session_id: ID сессии
            sample_rate: Брать каждую N-ю точку (для экономии места)
        """
        table_name = self.product_to_table[product_type]
        var_mapping = self.variable_mappings[product_type]
        
        print(f"📂 Обработка {Path(netcdf_file_path).name}...")
        
        dataset = nc.Dataset(netcdf_file_path, 'r')
        
        try:
            product_group = dataset.groups.get('PRODUCT', dataset)
            
            # Извлечь координаты
            lat = product_group.variables['latitude'][:]
            lon = product_group.variables['longitude'][:]
            
            # Извлечь основную переменную
            main_var_name = var_mapping['main_var']
            main_data = product_group.variables[main_var_name][:]
            
            # Извлечь precision если есть
            precision_data = None
            if 'precision_var' in var_mapping:
                precision_var_name = var_mapping['precision_var']
                if precision_var_name in product_group.variables:
                    precision_data = product_group.variables[precision_var_name][:]
            
            # QA value
            qa_data = product_group.variables.get('qa_value', None)
            if qa_data is not None:
                qa_data = qa_data[:]
            
            # Cloud fraction
            cloud_data = product_group.variables.get('cloud_fraction', None)
            if cloud_data is not None:
                cloud_data = cloud_data[:]
            
            # Время
            time_var = product_group.variables.get('time')
            if time_var:
                time_data = time_var[:]
            
            # Подготовить данные для вставки
            measurements = []
            
            # Размерность данных
            if len(main_data.shape) == 3:
                # (time, scanline, ground_pixel)
                for t in range(0, main_data.shape[0], sample_rate):
                    for i in range(0, main_data.shape[1], sample_rate):
                        for j in range(0, main_data.shape[2], sample_rate):
                            # Проверить валидность
                            if np.ma.is_masked(main_data[t, i, j]):
                                continue
                            
                            value = float(main_data[t, i, j])
                            latitude = float(lat[t, i, j])
                            longitude = float(lon[t, i, j])
                            
                            # Пропустить невалидные координаты
                            if abs(latitude) > 90 or abs(longitude) > 180:
                                continue
                            
                            # Базовая запись
                            measurement = {
                                'session_id': session_id,
                                'latitude': latitude,
                                'longitude': longitude,
                                'timestamp': datetime.now().isoformat(),  # Упрощенно
                                var_mapping['column_name']: value
                            }
                            
                            # Добавить precision если есть
                            if precision_data is not None and 'precision_name' in var_mapping:
                                if not np.ma.is_masked(precision_data[t, i, j]):
                                    measurement[var_mapping['precision_name']] = float(precision_data[t, i, j])
                            
                            # Добавить QA
                            if qa_data is not None:
                                if not np.ma.is_masked(qa_data[t, i, j]):
                                    measurement['qa_value'] = float(qa_data[t, i, j])
                            
                            # Добавить cloud fraction
                            if cloud_data is not None:
                                if not np.ma.is_masked(cloud_data[t, i, j]):
                                    measurement['cloud_fraction'] = float(cloud_data[t, i, j])
                            
                            measurements.append(measurement)
                            
                            # Batch insert каждые 1000 записей
                            if len(measurements) >= 1000:
                                self._batch_insert(table_name, measurements)
                                measurements = []
            
            # Вставить оставшиеся
            if measurements:
                self._batch_insert(table_name, measurements)
            
            # Обновить статус сессии
            self.supabase.table('measurement_sessions')\
                .update({'processing_status': 'completed', 'processed_at': datetime.now().isoformat()})\
                .eq('id', session_id)\
                .execute()
            
            print(f"✅ Загрузка завершена")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            # Обновить статус на failed
            self.supabase.table('measurement_sessions')\
                .update({'processing_status': 'failed', 'error_message': str(e)})\
                .eq('id', session_id)\
                .execute()
            raise
        finally:
            dataset.close()
    
    def _batch_insert(self, table_name, data):
        """Вставить данные батчем"""
        try:
            self.supabase.table(table_name).insert(data).execute()
            print(f"  ✓ Вставлено {len(data)} записей в {table_name}")
        except Exception as e:
            print(f"  ✗ Ошибка вставки: {e}")
    
    def process_directory(self, directory_path, product_type, sample_rate=10):
        """
        Обработать все NetCDF файлы в директории
        
        Args:
            directory_path: Путь к директории с файлами
            product_type: Тип продукта
            sample_rate: Частота сэмплирования
        """
        directory = Path(directory_path)
        nc_files = list(directory.glob('*.nc'))
        
        if not nc_files:
            print(f"⚠️ NetCDF файлы не найдены в {directory}")
            return
        
        print(f"📁 Найдено {len(nc_files)} файлов в {directory}")
        
        for i, nc_file in enumerate(nc_files, 1):
            print(f"\n[{i}/{len(nc_files)}] Обработка {nc_file.name}")
            
            try:
                # Создать сессию
                session_id = self.create_measurement_session(nc_file, product_type)
                
                # Загрузить измерения
                self.upload_measurements(nc_file, product_type, session_id, sample_rate)
                
            except Exception as e:
                print(f"❌ Ошибка при обработке {nc_file.name}: {e}")
                continue


def main():
    """Пример использования"""
    
    # ⚠️ ВАЖНО: Укажи свои данные Supabase
    SUPABASE_URL = 'https://your-project.supabase.co'
    SUPABASE_KEY = 'your-anon-key'
    
    if 'your-project' in SUPABASE_URL:
        print("❌ ОШИБКА: Укажи свои данные Supabase!")
        print("📝 Найди их в Project Settings → API")
        return
    
    # Создать uploader
    uploader = SupabaseUploader(SUPABASE_URL, SUPABASE_KEY)
    
    # Обработать данные NO₂
    print("=" * 60)
    print("📊 ЗАГРУЗКА ДАННЫХ NO₂ В SUPABASE")
    print("=" * 60)
    
    uploader.process_directory(
        directory_path='../raw_data/no2',
        product_type='L2__NO2___',
        sample_rate=50  # Каждая 50-я точка (для экономии места)
    )
    
    # Можно обработать и другие параметры
    # uploader.process_directory('../raw_data/o3', 'L2__O3____', sample_rate=50)
    # uploader.process_directory('../raw_data/co', 'L2__CO____', sample_rate=50)


if __name__ == "__main__":
    main()
