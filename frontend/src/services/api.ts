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
    async fetchRegions(): Promise<string[]> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/statistics/regions`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data?.regions || [];
        } catch (error) {
            console.error('Error fetching regions:', error);
            return [];
        }
    },

    async fetchRegionHistory(
        regionName: string,
        indexType: string,
        dateFrom?: string,
        dateTo?: string
    ): Promise<TimeseriesPoint[]> {
        try {
            const params = new URLSearchParams({
                index_type: indexType,
                limit: '100'
            });
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);

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
    }
};


export interface AreaStatistics {
    mean: number | null;
    min: number | null;
    max: number | null;
    std: number | null;
    median: number | null;
    pixel_count: number;
}

export interface AreaTimeseriesPoint {
    date: string;
    mean: number;
    min: number;
    max: number;
    pixel_count: number;
}

export interface HistogramBucket {
    range_min: number;
    range_max: number;
    count: number;
}

export interface AreaChange {
    date_a: string;
    date_b: string;
    mean_a: number | null;
    mean_b: number | null;
    mean_diff: number | null;
    improved_count: number;
    declined_count: number;
    stable_count: number;
    pixel_count: number;
}

export interface AreaBounds {
    minLat: number;
    maxLat: number;
    minLon: number;
    maxLon: number;
}

function areaParams(area: AreaBounds): URLSearchParams {
    return new URLSearchParams({
        min_lat: area.minLat.toString(),
        max_lat: area.maxLat.toString(),
        min_lon: area.minLon.toString(),
        max_lon: area.maxLon.toString()
    });
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
    },

    async fetchAreaTimeseries(
        area: AreaBounds,
        indexType: string,
        dateFrom: string,
        dateTo: string
    ): Promise<AreaTimeseriesPoint[]> {
        try {
            const params = areaParams(area);
            params.append('index_type', indexType);
            params.append('date_from', dateFrom);
            params.append('date_to', dateTo);

            const response = await fetch(`${API_BASE_URL}/api/tiles/area/timeseries?${params.toString()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data || [];
        } catch (error) {
            console.error('Error fetching area timeseries:', error);
            return [];
        }
    },

    async fetchAreaHistogram(
        area: AreaBounds,
        indexType: string,
        date: string,
        bins: number = 20
    ): Promise<HistogramBucket[]> {
        try {
            const params = areaParams(area);
            params.append('index_type', indexType);
            params.append('date', date);
            params.append('bins', bins.toString());

            const response = await fetch(`${API_BASE_URL}/api/tiles/area/histogram?${params.toString()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data || [];
        } catch (error) {
            console.error('Error fetching area histogram:', error);
            return [];
        }
    },

    async fetchPixels(
        area: AreaBounds,
        date: string,
        resolution: number = 100
    ): Promise<{ success: boolean; pixels_stored: number } | null> {
        try {
            const params = areaParams(area);
            params.append('date', date);
            params.append('resolution', resolution.toString());

            const response = await fetch(`${API_BASE_URL}/api/tiles/fetch-pixels?${params.toString()}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            return json.data || null;
        } catch (error) {
            console.error('Error fetching pixels:', error);
            return null;
        }
    },

    async fetchAreaChange(
        area: AreaBounds,
        indexType: string,
        dateA: string,
        dateB: string
    ): Promise<AreaChange | null> {
        try {
            const params = areaParams(area);
            params.append('index_type', indexType);
            params.append('date_a', dateA);
            params.append('date_b', dateB);

            const response = await fetch(`${API_BASE_URL}/api/tiles/area/change?${params.toString()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const json = await response.json();
            const data = json.data;
            return data && data.pixel_count > 0 ? data : null;
        } catch (error) {
            console.error('Error fetching area change:', error);
            return null;
        }
    }
};
