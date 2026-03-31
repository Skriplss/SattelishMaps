export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TimeseriesPoint {
    date: string;
    mean: number;
    min: number;
    max: number;
}

export interface RegionStatistics {
    id: string;
    region_name: string;
    date: string;
    index_type: string;
    mean: number;
    min: number;
    max: number;
    std: number;
    sample_count: number;
}

export const SatelliteAPI = {
    async fetchRegionHistory(regionName: string, indexType: string): Promise<TimeseriesPoint[]> {
        try {
            const params = new URLSearchParams({
                index_type: indexType,
                limit: '100'
            });

            const response = await fetch(`${API_BASE_URL}/api/statistics/timeseries/${encodeURIComponent(regionName)}?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data || [];
        } catch (error) {
            console.error('Error fetching history:', error);
            return [];
        }
    },

    async fetchAvailableDates(indexType?: string, regionName?: string): Promise<string[]> {
        try {
            const params = new URLSearchParams();
            if (indexType) params.append('index_type', indexType);
            if (regionName) params.append('region_name', regionName);

            const response = await fetch(`${API_BASE_URL}/api/statistics/region/dates?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data?.dates || [];
        } catch (error) {
            console.error('Error fetching available dates:', error);
            return [];
        }
    }
};


export interface AreaStatistics {
    mean: number | null;
    min: number | null;
    max: number | null;
    std: number | null;
    pixel_count: number;
}

export const TileAPI = {
    async fetchAreaStatistics(
        minLat: number,
        maxLat: number,
        minLon: number,
        maxLon: number,
        date: string,
        indexType: string
    ): Promise<AreaStatistics | null> {
        try {
            const params = new URLSearchParams({
                min_lat: minLat.toString(),
                max_lat: maxLat.toString(),
                min_lon: minLon.toString(),
                max_lon: maxLon.toString(),
                date: date,
                index_type: indexType
            });

            const response = await fetch(`${API_BASE_URL}/api/tiles/area/stats?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data || null;
        } catch (error) {
            console.error('Error fetching area statistics:', error);
            return null;
        }
    }
};
