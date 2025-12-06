
import os
import sys
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from glob import glob
import asyncio

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging
from services.supabase_service import supabase_service
from services.ndvi_calculator import ndvi_calculator
from services.ndwi_calculator import ndwi_calculator

logger = logging.getLogger(__name__)

class SafeProductImporter:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        
    def find_safe_products(self):
        """Find .SAFE directories in the data directory"""
        return glob(os.path.join(self.data_dir, "*.SAFE"))
        
    def parse_metadata(self, safe_path: str):
        """Parse MTD_MSIL2A.xml (or MSIL1C) file"""
        # Try finding metadata file
        mtd_files = glob(os.path.join(safe_path, "MTD_*.xml"))
        if not mtd_files:
            raise FileNotFoundError(f"No metadata file found in {safe_path}")
            
        mtd_path = mtd_files[0]
        tree = ET.parse(mtd_path)
        root = tree.getroot()
        
        # Namespacing is annoying in XML, so we'll use a helper or strip it
        # Helper to find without namespace
        def find_xml(element, tag_name):
            # Iterate all elements to find matching tag name regardless of namespace
            for child in element.iter():
                if child.tag.endswith(tag_name):
                    return child
            return None
            
        # General Info
        general_info = find_xml(root, "General_Info")
        if not general_info:
             # Try level 1C structure if 2A fails or just try searching from root
             general_info = root
             
        product_info = find_xml(general_info, "Product_Info")
        
        # Extract basic fields
        product_id = os.path.basename(safe_path).replace('.SAFE', '')
        
        timestamp_elem = find_xml(product_info, "PRODUCT_START_TIME")
        timestamp = timestamp_elem.text if timestamp_elem is not None else datetime.now().isoformat()
        
        level_elem = find_xml(product_info, "PROCESSING_LEVEL")
        processing_level = level_elem.text if level_elem is not None else "Unknown"
        
        # Cloud coverage
        cloud_coverage = 0.0
        quality_indicators = find_xml(root, "Quality_Indicators_Info")
        if quality_indicators:
            cloud_pct = find_xml(quality_indicators, "Cloud_Coverage_Assessment")
            if cloud_pct is not None:
                cloud_coverage = float(cloud_pct.text)
        
        # Parse timestamp
        # Fix for some timestamp formats
        if timestamp.endswith('Z'):
            timestamp = timestamp.replace('Z', '+00:00')
        try:
            acq_date = datetime.fromisoformat(timestamp)
        except:
            acq_date = datetime.now()
        
        # Footprint (Geometric_Info)
        # Parse EXT_POS_LIST for accurate bounds
        bounds_wkt = None
        center_point_wkt = None
        
        try:
            geometric_info = find_xml(root, "Geometric_Info")
            if geometric_info:
                footprint = find_xml(geometric_info, "Product_Footprint")
                if footprint:
                    global_footprint = find_xml(footprint, "Global_Footprint")
                    if global_footprint:
                        pos_list = find_xml(global_footprint, "EXT_POS_LIST")
                        if pos_list is not None and pos_list.text:
                            # Sentinel-2 format: Lat1 Lon1 Lat2 Lon2 ...
                            coords = pos_list.text.strip().split()
                            if len(coords) >= 4:
                                poly_coords = []
                                lats = []
                                lons = []
                                
                                # Iterate by 2 (lat, lon)
                                for i in range(0, len(coords), 2):
                                    lat = float(coords[i])
                                    lon = float(coords[i+1])
                                    lats.append(lat)
                                    lons.append(lon)
                                    poly_coords.append(f"{lon} {lat}")
                                
                                # Close the polygon if not closed
                                if poly_coords[0] != poly_coords[-1]:
                                    poly_coords.append(poly_coords[0])
                                
                                bounds_wkt = f"POLYGON(({', '.join(poly_coords)}))"
                                
                                # Calculate simple center
                                avg_lat = sum(lats) / len(lats)
                                avg_lon = sum(lons) / len(lons)
                                center_point_wkt = f"POINT({avg_lon} {avg_lat})"
        except Exception as e:
            logger.warning(f"Failed to extract footprint: {e}")

        # Fallback if parsing failed
        if not center_point_wkt:
             center_point_wkt = "POINT(0 0)"
        
        return {
            'product_id': product_id,
            'title': product_id,
            'acquisition_date': acq_date,
            'processing_date': datetime.now(),
            'cloud_coverage': cloud_coverage,
            'thumbnail_url': '',
            'download_url': '',
            'metadata': {
                'processinglevel': processing_level,
                'format': 'SAFE'
            },
            'center_point': center_point_wkt,
            'bounds': bounds_wkt
        }

    def find_band_file(self, safe_path: str, band_name: str) -> str:
        """Find specific band file (jp2) in GRANULE/*/IMG_DATA/R10m/"""
        # Pattern for L2A: GRANULE/*/IMG_DATA/R10m/*_B04_10m.jp2
        # Use recursive glob
        patterns = [
            f"**/*_{band_name}_10m.jp2", # L2A 10m
            f"**/*_{band_name}.jp2"      # Fallback
        ]
        
        for pattern in patterns:
            matches = glob(os.path.join(safe_path, pattern), recursive=True)
            if matches:
                return matches[0]
        return None

    def import_product(self, safe_path: str):
        try:
            logger.info(f"Importing {safe_path}...")
            product_data = self.parse_metadata(safe_path)
            
            # Prepare for Supabase
            db_data = {
                'product_id': product_data['product_id'],
                'title': product_data['title'],
                'acquisition_date': product_data['acquisition_date'].isoformat(),
                'processing_date': product_data['processing_date'].isoformat(),
                'cloud_coverage': product_data['cloud_coverage'],
                'thumbnail_url': product_data['thumbnail_url'],
                'download_url': product_data['download_url'],
                'metadata': product_data['metadata'],
                'center_point': product_data['center_point'],
                'bounds': product_data['bounds']
            }
            
            # Insert satellite image
            logger.info(f"Saving metadata for {product_data['product_id']}")
            result = supabase_service.insert_satellite_image(db_data)
            image_id = result['id']
            
            # Find Bands
            logger.info("Looking for spectral bands (B03, B04, B08)...")
            b03_path = self.find_band_file(safe_path, "B03") # Green
            b04_path = self.find_band_file(safe_path, "B04") # Red
            b08_path = self.find_band_file(safe_path, "B08") # NIR
            
            # Calculate NDVI
            if b04_path and b08_path:
                logger.info(f"✅ Found bands for NDVI: {os.path.basename(b04_path)}, {os.path.basename(b08_path)}")
                logger.info("Calculating REAL NDVI from bands (this may take a moment)...")
                try:
                    ndvi_data = ndvi_calculator.calculate_ndvi_from_bands(
                        nir_band_path=b08_path,
                        red_band_path=b04_path,
                        image_id=image_id
                    )
                    supabase_service.insert_ndvi_data(ndvi_data)
                    logger.info("✅ NDVI calculation complete")
                except Exception as e:
                    logger.error(f"Failed to calculate NDVI from bands: {e}")
            else:
                logger.warning("Bands for NDVI not found, falling back to metadata estimation")
                ndvi_data = ndvi_calculator.calculate_ndvi_from_metadata(
                    image_id=image_id,
                    product_id=product_data['product_id'],
                    cloud_coverage=product_data['cloud_coverage'],
                    center_point=product_data['center_point']
                )
                supabase_service.insert_ndvi_data(ndvi_data)
            
            # Calculate NDWI
            if b03_path and b08_path:
                logger.info(f"✅ Found bands for NDWI: {os.path.basename(b03_path)}, {os.path.basename(b08_path)}")
                logger.info("Calculating REAL NDWI from bands...")
                try:
                    ndwi_data = ndwi_calculator.calculate_ndwi_from_bands(
                        green_band_path=b03_path,
                        nir_band_path=b08_path,
                        image_id=image_id
                    )
                    supabase_service.insert_ndwi_data(ndwi_data)
                    logger.info("✅ NDWI calculation complete")
                except Exception as e:
                    logger.error(f"Failed to calculate NDWI from bands: {e}")
            else:
                logger.warning("Bands for NDWI not found, falling back to metadata estimation")
                ndwi_data = ndwi_calculator.calculate_ndwi_from_metadata(
                    image_id=image_id,
                    product_id=product_data['product_id'],
                    cloud_coverage=product_data['cloud_coverage'],
                    center_point=product_data['center_point']
                )
                supabase_service.insert_ndwi_data(ndwi_data)
            
            logger.info(f"✅ Successfully imported {product_data['product_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import {safe_path}: {e}")
            return False

def main():
    setup_logging()
    
    # Directory mapping
    # Inside docker: /app/downloads
    # Local: ./downloads
    DATA_DIR = "/app/downloads"
    
    importer = SafeProductImporter(DATA_DIR)
    products = importer.find_safe_products()
    
    if not products:
        print(f"No .SAFE directories found in {DATA_DIR}")
        print("Please unzip Sentinel-2 data into the downloads folder.")
        return
        
    print(f"Found {len(products)} products. Starting import...")
    
    success_count = 0
    for product_path in products:
        if importer.import_product(product_path):
            success_count += 1
            
    print(f"\nImport complted: {success_count}/{len(products)} successful.")

if __name__ == "__main__":
    main()
