// App-wide geographic configuration.
// The app serves Slovakia only — the map is locked to these bounds and
// the backend rejects requests outside its COVERAGE_BBOX (keep in sync).

export const COVERAGE = {
    // Data coverage bbox (matches backend COVERAGE_BBOX)
    minLon: 16.8,
    minLat: 47.7,
    maxLon: 22.6,
    maxLat: 49.7,
};

// Map viewport limits — coverage plus a small margin so the country
// isn't glued to the viewport edges
export const MAP_MAX_BOUNDS: [[number, number], [number, number]] = [
    [15.9, 47.3],
    [23.5, 50.1],
];

export const MAP_CENTER: [number, number] = [19.699, 48.669];
export const MAP_DEFAULT_ZOOM = 7;
export const MAP_MIN_ZOOM = 6;

/** Approximate area dimensions in km (lat: ~111 km/°, lon scaled by cos(lat)) */
export function areaSizeKm(area: {
    minLat: number; maxLat: number; minLon: number; maxLon: number;
}): { w: number; h: number } {
    const midLat = (area.minLat + area.maxLat) / 2;
    return {
        w: (area.maxLon - area.minLon) * 111 * Math.cos((midLat * Math.PI) / 180),
        h: (area.maxLat - area.minLat) * 111
    };
}

/** Clamp an area selection to the coverage bbox. Returns null if fully outside. */
export function clampAreaToCoverage(area: {
    minLat: number; maxLat: number; minLon: number; maxLon: number;
}): typeof area | null {
    const clamped = {
        minLon: Math.max(area.minLon, COVERAGE.minLon),
        maxLon: Math.min(area.maxLon, COVERAGE.maxLon),
        minLat: Math.max(area.minLat, COVERAGE.minLat),
        maxLat: Math.min(area.maxLat, COVERAGE.maxLat),
    };
    if (clamped.minLon >= clamped.maxLon || clamped.minLat >= clamped.maxLat) {
        return null;
    }
    return clamped;
}
