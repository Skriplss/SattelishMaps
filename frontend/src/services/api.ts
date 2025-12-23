export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TimeseriesPoint {
    date: string;
    mean: number;
    min: number;
    max: number;
}

export const SatelliteAPI = {
    async fetchRegionHistory(regionName: string, indexType: string): Promise<TimeseriesPoint[]> {
        console.log(`📊 Fetching history for ${regionName} (${indexType})...`);

        try {
            const params = new URLSearchParams({
                index_type: indexType,
                limit: '100'
            });

            const response = await fetch(`${API_BASE_URL}/api/statistics/timeseries/${regionName}?${params.toString()}`, {
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
            console.error('❌ Error fetching history:', error);
            return [];
        }
    }
};
