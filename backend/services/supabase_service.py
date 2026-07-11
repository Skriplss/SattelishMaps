"""
Supabase service — single entry point for all database operations.

Schema: database/schemas/init.sql
"""
from supabase import create_client, Client
from config.settings import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Production-ready Supabase service"""

    def __init__(self):
        try:
            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    def upsert_region_statistics(self, rows: List[Dict]) -> int:
        """
        Upsert region statistics rows (long format: one row per
        region_name + date + index_type).
        """
        if not rows:
            return 0
        try:
            self.client.table('region_statistics').upsert(
                rows,
                on_conflict='region_name,date,index_type'
            ).execute()

            logger.info(f"Upserted {len(rows)} region statistics rows")
            return len(rows)

        except Exception as e:
            logger.error(f"Error upserting region statistics: {str(e)}")
            raise

    def get_region_statistics_geojson(
        self,
        date: str,
        index_type: str,
        region_name: Optional[str] = None
    ) -> Dict:
        """
        Get region statistics as GeoJSON FeatureCollection.

        Single RPC call — geometry conversion happens in SQL.
        """
        try:
            response = self.client.rpc(
                'get_region_stats_geojson',
                {
                    'p_date': date,
                    'p_index_type': index_type,
                    'p_region_name': region_name
                }
            ).execute()

            features = [
                {
                    "type": "Feature",
                    "geometry": row['geometry'],
                    "properties": {
                        "id": row['id'],
                        "region_name": row['region_name'],
                        "date": row['date'],
                        "index_type": row['index_type'],
                        "mean": row['mean'],
                        "min": row['min'],
                        "max": row['max'],
                        "std": row['std'],
                        "sample_count": row['sample_count']
                    }
                }
                for row in (response.data or [])
            ]

            return {"type": "FeatureCollection", "features": features}

        except Exception as e:
            logger.error(f"Error getting region statistics as GeoJSON: {str(e)}")
            raise

    def get_region_names(self) -> List[str]:
        """Get distinct region names present in region_statistics"""
        try:
            response = self.client.table('region_statistics')\
                .select('region_name')\
                .execute()

            return sorted(set(row['region_name'] for row in response.data if row.get('region_name')))

        except Exception as e:
            logger.error(f"Error fetching region names: {str(e)}")
            raise

    def get_available_dates(
        self,
        index_type: Optional[str] = None,
        region_name: Optional[str] = None
    ) -> List[str]:
        """Get list of available dates in region_statistics"""
        try:
            query = self.client.table('region_statistics').select('date')

            if index_type:
                query = query.eq('index_type', index_type)
            if region_name:
                query = query.eq('region_name', region_name)

            response = query.execute()

            return sorted(set(row['date'] for row in response.data if 'date' in row))

        except Exception as e:
            logger.error(f"Error fetching available dates: {str(e)}")
            raise

    def get_region_statistics_timeseries(
        self,
        region_name: str,
        index_type: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get timeseries data for region and index"""
        try:
            query = self.client.table('region_statistics')\
                .select('*')\
                .eq('region_name', region_name)\
                .eq('index_type', index_type)\
                .order('date', desc=False)

            if date_from:
                query = query.gte('date', date_from)
            if date_to:
                query = query.lte('date', date_to)

            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Error fetching region timeseries: {str(e)}")
            raise


# Singleton instance
supabase_service = SupabaseService()
