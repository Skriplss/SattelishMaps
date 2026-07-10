import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useTranslation } from '@/hooks/useTranslation';
import {
    MAP_MAX_BOUNDS,
    MAP_CENTER,
    MAP_DEFAULT_ZOOM,
    MAP_MIN_ZOOM,
    clampAreaToCoverage,
    areaSizeKm
} from '@/config';

type Area = { minLat: number; maxLat: number; minLon: number; maxLon: number };

interface MapContainerProps {
    activeLayer: string | null;
    selectedDate: string;
    selectedArea: Area | null;
    drawMode: boolean;
    flyTo: { center: [number, number] } | null;
    onAreaSelect: (area: Area | null) => void;
}

function styleUrl(apiKey: string, dark: boolean): string {
    return `https://api.maptiler.com/maps/${dark ? 'dataviz-dark' : 'dataviz'}/style.json?key=${apiKey}`;
}

function areaToFeature(area: Area) {
    return {
        type: 'Feature' as const,
        geometry: {
            type: 'Polygon' as const,
            coordinates: [[
                [area.minLon, area.minLat],
                [area.maxLon, area.minLat],
                [area.maxLon, area.maxLat],
                [area.minLon, area.maxLat],
                [area.minLon, area.minLat]
            ]]
        },
        properties: {}
    };
}

export function MapContainer({ activeLayer, selectedDate, selectedArea, drawMode, flyTo, onAreaSelect }: MapContainerProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [isDrawing, setIsDrawing] = useState(false);
    const [drawSize, setDrawSize] = useState<{ w: number; h: number } | null>(null);
    const drawStart = useRef<[number, number] | null>(null);
    const drawModeRef = useRef(drawMode);
    // Overlay state the style-reload handler needs (refs avoid stale closures)
    const overlayState = useRef({ activeLayer, selectedDate, selectedArea });
    const { t } = useTranslation();

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    drawModeRef.current = drawMode;
    overlayState.current = { activeLayer, selectedDate, selectedArea };

    /** (Re)create the drawn-area source/layers and the satellite raster layer.
     *  Idempotent — safe to call after every style load. */
    const syncOverlays = () => {
        const m = map.current;
        if (!m) return;
        const { activeLayer, selectedDate, selectedArea } = overlayState.current;

        if (!m.getSource('drawn-area')) {
            m.addSource('drawn-area', {
                type: 'geojson',
                data: {
                    type: 'FeatureCollection',
                    features: selectedArea ? [areaToFeature(selectedArea)] : []
                }
            });
            m.addLayer({
                id: 'drawn-area-fill',
                type: 'fill',
                source: 'drawn-area',
                paint: { 'fill-color': '#3b82f6', 'fill-opacity': 0.2 }
            });
            m.addLayer({
                id: 'drawn-area-outline',
                type: 'line',
                source: 'drawn-area',
                paint: { 'line-color': '#3b82f6', 'line-width': 2 }
            });
        }

        const layerId = 'satellite-layer';
        if (m.getLayer(layerId)) m.removeLayer(layerId);
        if (m.getSource(layerId)) m.removeSource(layerId);

        if (activeLayer) {
            const tileUrl = `${API_BASE_URL}/api/wms/tile/{z}/{x}/{y}.png?date=${selectedDate}&index_type=${activeLayer.toUpperCase()}`;

            m.addSource(layerId, {
                type: 'raster',
                tiles: [tileUrl],
                tileSize: 256,
                attribution: 'Sentinel-2 Data'
            });

            // Insert below labels, above the drawn area's siblings
            const labelLayer = m.getStyle().layers?.find(l => l.type === 'symbol');
            m.addLayer({
                id: layerId,
                type: 'raster',
                source: layerId,
                paint: {
                    'raster-opacity': 0.8,
                    'raster-fade-duration': 300
                }
            }, labelLayer?.id);
        }
    };

    // Map init
    useEffect(() => {
        if (map.current || !mapContainer.current) return;

        const apiKey = import.meta.env.VITE_MAPTILER_KEY;
        if (!apiKey) {
            console.error("Missing VITE_MAPTILER_KEY");
            return;
        }

        const isDark = document.documentElement.classList.contains('dark');

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: styleUrl(apiKey, isDark),
            center: MAP_CENTER,
            zoom: MAP_DEFAULT_ZOOM,
            minZoom: MAP_MIN_ZOOM,
            maxBounds: MAP_MAX_BOUNDS,
            attributionControl: false
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
        map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

        map.current.on('load', () => {
            setIsLoaded(true);
            syncOverlays();
        });

        // Follow the app theme: swap the basemap style and restore overlays
        const observer = new MutationObserver(() => {
            const m = map.current;
            if (!m) return;
            const dark = document.documentElement.classList.contains('dark');
            const url = styleUrl(apiKey, dark);
            if ((m.getStyle() as { sprite?: string })?.sprite?.includes(dark ? 'dataviz-dark' : 'dataviz/')) return;
            m.setStyle(url);
            m.once('style.load', () => syncOverlays());
        });
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

        return () => {
            observer.disconnect();
            map.current?.remove();
            map.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Satellite layer follows activeLayer/date
    useEffect(() => {
        if (!map.current || !isLoaded) return;
        syncOverlays();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeLayer, isLoaded, selectedDate, API_BASE_URL]);

    // Reflect external selection changes (including clearing)
    useEffect(() => {
        if (!map.current || !isLoaded) return;
        const source = map.current.getSource('drawn-area') as maplibregl.GeoJSONSource | undefined;
        source?.setData({
            type: 'FeatureCollection',
            features: selectedArea ? [areaToFeature(selectedArea)] : []
        });
    }, [selectedArea, isLoaded]);

    // Fly to a searched location
    useEffect(() => {
        if (!map.current || !flyTo) return;
        map.current.flyTo({ center: flyTo.center, zoom: 12 });
    }, [flyTo]);

    // Crosshair cursor while draw mode is armed
    useEffect(() => {
        const canvas = map.current?.getCanvas();
        if (!canvas) return;
        canvas.style.cursor = drawMode ? 'crosshair' : '';
    }, [drawMode, isLoaded]);

    // Area selection: Shift+drag, or plain drag when draw mode is armed
    useEffect(() => {
        if (!map.current || !isLoaded) return;

        const canvas = map.current.getCanvas();

        const handleMouseDown = (e: MouseEvent) => {
            if (!e.shiftKey && !drawModeRef.current) return;

            e.preventDefault();

            const rect = canvas.getBoundingClientRect();
            const point = map.current!.unproject([e.clientX - rect.left, e.clientY - rect.top]);
            drawStart.current = [point.lng, point.lat];
            setIsDrawing(true);

            canvas.style.cursor = 'crosshair';
            map.current!.dragPan.disable();
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing || !drawStart.current) return;

            const rect = canvas.getBoundingClientRect();
            const point = map.current!.unproject([e.clientX - rect.left, e.clientY - rect.top]);
            const start = drawStart.current;
            const end = [point.lng, point.lat];

            const rect2 = {
                minLon: Math.min(start[0], end[0]),
                maxLon: Math.max(start[0], end[0]),
                minLat: Math.min(start[1], end[1]),
                maxLat: Math.max(start[1], end[1])
            };

            const source = map.current?.getSource('drawn-area') as maplibregl.GeoJSONSource;
            source?.setData({
                type: 'FeatureCollection',
                features: [areaToFeature(rect2)]
            });
            setDrawSize(areaSizeKm(rect2));
        };

        const handleMouseUp = (e: MouseEvent) => {
            if (!isDrawing || !drawStart.current) return;

            const rect = canvas.getBoundingClientRect();
            const point = map.current!.unproject([e.clientX - rect.left, e.clientY - rect.top]);
            const start = drawStart.current;
            const end = [point.lng, point.lat];

            const raw = {
                minLon: Math.min(start[0], end[0]),
                maxLon: Math.max(start[0], end[0]),
                minLat: Math.min(start[1], end[1]),
                maxLat: Math.max(start[1], end[1])
            };

            // Keep the selection inside the coverage area (Slovakia)
            const clamped = clampAreaToCoverage(raw);
            onAreaSelect(clamped);

            setIsDrawing(false);
            setDrawSize(null);
            drawStart.current = null;
            canvas.style.cursor = drawModeRef.current ? 'crosshair' : '';
            map.current!.dragPan.enable();
        };

        canvas.addEventListener('mousedown', handleMouseDown);
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseup', handleMouseUp);

        return () => {
            canvas.removeEventListener('mousedown', handleMouseDown);
            canvas.removeEventListener('mousemove', handleMouseMove);
            canvas.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isLoaded, isDrawing, onAreaSelect]);

    return (
        <div className="relative w-full h-full">
            <div ref={mapContainer} className="w-full h-full" />
            {/* Drawing hint — live size while drawing, instructions otherwise */}
            {activeLayer && (isDrawing || !selectedArea) && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white dark:bg-slate-800 px-4 py-2 rounded-lg shadow-lg text-sm text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 pointer-events-none">
                    {isDrawing && drawSize ? (
                        <span className="font-mono font-medium">
                            {drawSize.w.toFixed(1)} × {drawSize.h.toFixed(1)} km
                        </span>
                    ) : drawMode ? t('drawModeHint') : (
                        <>
                            <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded border border-slate-300 dark:border-slate-600 font-mono text-xs mr-1">Shift</kbd>
                            {t('drawHint')}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
