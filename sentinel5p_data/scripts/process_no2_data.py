"""
Скрипт для обработки и анализа данных NO₂ из файлов Sentinel-5P
Читает NetCDF файлы и извлекает данные о концентрации диоксида азота

Требования:
- netCDF4
- numpy
- matplotlib
- pandas
"""

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from datetime import datetime


class NO2DataProcessor:
    """Класс для обработки данных NO₂"""
    
    def __init__(self, netcdf_file_path):
        """
        Инициализация процессора
        
        Args:
            netcdf_file_path: Путь к NetCDF файлу со спутниковыми данными
        """
        self.file_path = netcdf_file_path
        self.dataset = None
        self.data = {}
        
    def load_data(self):
        """Загрузить данные из NetCDF файла"""
        print(f"📂 Открытие файла: {Path(self.file_path).name}")
        
        try:
            self.dataset = nc.Dataset(self.file_path, 'r')
            print("✅ Файл успешно открыт")
            return True
        except Exception as e:
            print(f"❌ Ошибка при открытии файла: {e}")
            return False
    
    def explore_structure(self):
        """Показать структуру файла (переменные, размерности)"""
        if not self.dataset:
            print("❌ Файл не загружен. Вызови load_data() сначала")
            return
        
        print("\n" + "=" * 60)
        print("📊 СТРУКТУРА ФАЙЛА")
        print("=" * 60)
        
        # Размерности
        print("\n🔢 Размерности:")
        for dim_name, dim in self.dataset.dimensions.items():
            print(f"  - {dim_name}: {len(dim)}")
        
        # Переменные
        print("\n📈 Переменные:")
        for var_name in self.dataset.variables.keys():
            var = self.dataset.variables[var_name]
            print(f"  - {var_name}")
            print(f"    Размерность: {var.dimensions}")
            print(f"    Форма: {var.shape}")
            if hasattr(var, 'units'):
                print(f"    Единицы: {var.units}")
    
    def extract_no2_data(self):
        """
        Извлечь данные NO₂ из файла
        
        Returns:
            dict: Словарь с данными NO₂ и метаданными
        """
        if not self.dataset:
            print("❌ Файл не загружен")
            return None
        
        print("\n🔬 Извлечение данных NO₂...")
        
        try:
            # Основная переменная NO₂ (тропосферная колонка)
            # Название может отличаться в зависимости от версии продукта
            no2_var_names = [
                'nitrogendioxide_tropospheric_column',
                'NO2',
                'tropospheric_NO2_column_number_density'
            ]
            
            no2_data = None
            no2_var_name = None
            
            # Найти правильное название переменной
            for var_name in no2_var_names:
                if var_name in self.dataset.groups.get('PRODUCT', self.dataset).variables:
                    product_group = self.dataset.groups['PRODUCT']
                    no2_data = product_group.variables[var_name][:]
                    no2_var_name = var_name
                    break
            
            if no2_data is None:
                print("⚠️ Переменная NO₂ не найдена. Доступные переменные:")
                print(list(self.dataset.variables.keys()))
                return None
            
            # Извлечь координаты
            product_group = self.dataset.groups.get('PRODUCT', self.dataset)
            
            # Широта и долгота
            lat = product_group.variables['latitude'][:]
            lon = product_group.variables['longitude'][:]
            
            # Время
            time_var = product_group.variables.get('time', None)
            if time_var:
                time_data = time_var[:]
            else:
                time_data = None
            
            # Преобразовать данные NO₂ (обычно в mol/m²)
            # Удалить невалидные значения (fill values)
            no2_data_masked = np.ma.masked_invalid(no2_data)
            
            # Преобразовать в µmol/m² (более понятные единицы)
            no2_umol = no2_data_masked * 1e6
            
            self.data = {
                'no2': no2_umol,
                'latitude': lat,
                'longitude': lon,
                'time': time_data,
                'variable_name': no2_var_name,
                'units': 'µmol/m²',
                'shape': no2_data.shape
            }
            
            print(f"✅ Данные извлечены")
            print(f"   Форма данных: {self.data['shape']}")
            print(f"   Диапазон широты: {lat.min():.2f} - {lat.max():.2f}")
            print(f"   Диапазон долготы: {lon.min():.2f} - {lon.max():.2f}")
            print(f"   Диапазон NO₂: {no2_umol.min():.2f} - {no2_umol.max():.2f} {self.data['units']}")
            
            return self.data
            
        except Exception as e:
            print(f"❌ Ошибка при извлечении данных: {e}")
            return None
    
    def calculate_statistics(self):
        """Рассчитать статистику по данным NO₂"""
        if not self.data:
            print("❌ Данные не извлечены. Вызови extract_no2_data() сначала")
            return None
        
        no2 = self.data['no2']
        
        stats = {
            'mean': float(np.mean(no2)),
            'median': float(np.median(no2)),
            'std': float(np.std(no2)),
            'min': float(np.min(no2)),
            'max': float(np.max(no2)),
            'percentile_25': float(np.percentile(no2, 25)),
            'percentile_75': float(np.percentile(no2, 75)),
            'units': self.data['units']
        }
        
        print("\n📊 СТАТИСТИКА NO₂:")
        print(f"  Среднее: {stats['mean']:.2f} {stats['units']}")
        print(f"  Медиана: {stats['median']:.2f} {stats['units']}")
        print(f"  Стд. отклонение: {stats['std']:.2f} {stats['units']}")
        print(f"  Минимум: {stats['min']:.2f} {stats['units']}")
        print(f"  Максимум: {stats['max']:.2f} {stats['units']}")
        
        return stats
    
    def visualize_no2_map(self, output_path='../processed_data/no2_map.png'):
        """
        Создать визуализацию карты NO₂
        
        Args:
            output_path: Путь для сохранения изображения
        """
        if not self.data:
            print("❌ Данные не извлечены")
            return
        
        print(f"\n🗺️ Создание карты NO₂...")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Создать карту
        no2 = self.data['no2']
        lat = self.data['latitude']
        lon = self.data['longitude']
        
        # Если данные многомерные, взять первый срез
        if len(no2.shape) > 2:
            no2 = no2[0]
            lat = lat[0]
            lon = lon[0]
        
        # Построить карту
        im = ax.pcolormesh(lon, lat, no2, cmap='RdYlBu_r', shading='auto')
        
        # Настроить оси
        ax.set_xlabel('Долгота', fontsize=12)
        ax.set_ylabel('Широта', fontsize=12)
        ax.set_title('Концентрация NO₂ (Диоксид азота) - Sentinel-5P', fontsize=14, fontweight='bold')
        
        # Добавить цветовую шкалу
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(f'NO₂ [{self.data["units"]}]', fontsize=12)
        
        # Добавить сетку
        ax.grid(True, alpha=0.3)
        
        # Сохранить
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Карта сохранена: {output_path}")
        
        plt.close()
    
    def export_to_json(self, output_path='../processed_data/no2_data.json'):
        """
        Экспортировать обработанные данные в JSON
        
        Args:
            output_path: Путь для сохранения JSON файла
        """
        if not self.data:
            print("❌ Данные не извлечены")
            return
        
        print(f"\n💾 Экспорт данных в JSON...")
        
        # Подготовить данные для JSON
        export_data = {
            'metadata': {
                'source_file': str(Path(self.file_path).name),
                'processing_date': datetime.now().isoformat(),
                'units': self.data['units'],
                'shape': self.data['shape']
            },
            'statistics': self.calculate_statistics()
        }
        
        # Сохранить JSON
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Данные экспортированы: {output_path}")
    
    def close(self):
        """Закрыть файл"""
        if self.dataset:
            self.dataset.close()
            print("✅ Файл закрыт")


def process_all_files_in_directory(directory_path='../raw_data'):
    """
    Обработать все NetCDF файлы в директории
    
    Args:
        directory_path: Путь к директории с файлами
    """
    directory = Path(directory_path)
    
    # Найти все NetCDF файлы
    nc_files = list(directory.glob('*.nc'))
    
    if not nc_files:
        print(f"⚠️ NetCDF файлы не найдены в {directory}")
        return
    
    print(f"📁 Найдено {len(nc_files)} файлов для обработки\n")
    
    for i, nc_file in enumerate(nc_files, 1):
        print(f"\n{'=' * 60}")
        print(f"Обработка файла {i}/{len(nc_files)}")
        print(f"{'=' * 60}")
        
        processor = NO2DataProcessor(nc_file)
        
        if processor.load_data():
            processor.explore_structure()
            processor.extract_no2_data()
            processor.calculate_statistics()
            
            # Создать уникальные имена для выходных файлов
            base_name = nc_file.stem
            processor.visualize_no2_map(f'../processed_data/{base_name}_map.png')
            processor.export_to_json(f'../processed_data/{base_name}_data.json')
            
            processor.close()


def main():
    """Пример использования"""
    
    print("🛰️ ОБРАБОТЧИК ДАННЫХ NO₂ SENTINEL-5P")
    print("=" * 60)
    
    # Проверить наличие файлов
    raw_data_dir = Path('../raw_data')
    
    if not raw_data_dir.exists():
        print(f"❌ Директория {raw_data_dir} не существует")
        print("   Создай её и помести туда NetCDF файлы (.nc)")
        return
    
    # Обработать все файлы
    process_all_files_in_directory(raw_data_dir)
    
    print("\n" + "=" * 60)
    print("🎉 Обработка завершена!")
    print("=" * 60)


if __name__ == "__main__":
    main()
