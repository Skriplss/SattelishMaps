import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapContainerProps {
    activeLayer: string | null;
    selectedDate: string;
    onAreaSelect: (area: { minLat: number; maxLat: number; minLon: number; maxLon: number } | null) => void;
}

export function MapContainer({ activeLayer, selectedDate, onAreaSelect }: MapContainerProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [isDrawing, setIsDrawing] = useState(false);
    const drawStart = useRef<[number, number] | null>(null);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    useEffect(() => {
        if (map.current || !mapContainer.current) return;

        const apiKey = import.meta.env.VITE_MAPTILER_KEY;
        if (!apiKey) {
            console.error("Missing VITE_MAPTILER_KEY");
            return;
        }

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${apiKey}`,
            center: [19.699, 48.669], // Slovakia center
            zoom: 8,
            attributionControl: false
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
        map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

        // Add drawing controls for area selection
        map.current.on('load', () => {
            setIsLoaded(true);
            
            // Add source for drawn features
            if (map.current) {
                map.current.addSource('drawn-area', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: []
                    }
                });

                // Add fill layer
                map.current.addLayer({
                    id: 'drawn-area-fill',
                    type: 'fill',
                    source: 'drawn-area',
                    paint: {
                        'fill-color': '#3b82f6',
                        'fill-opacity': 0.2
                    }
                });

                // Add outline layer
                map.current.addLayer({
                    id: 'drawn-area-outline',
                    type: 'line',
                    source: 'drawn-area',
                    paint: {
                        'line-color': '#3b82f6',
                        'line-width': 2
                    }
                });
            }
        });

        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, []);

    // Handle Layer Switching
    useEffect(() => {
        if (!map.current || !isLoaded) return;

        const layerId = 'satellite-layer';

        // Remove existing layer if valid
        if (map.current.getLayer(layerId)) {
            map.current.removeLayer(layerId);
        }
        if (map.current.getSource(layerId)) {
            map.current.removeSource(layerId);
        }

        if (activeLayer) {
            const tileUrl = `${API_BASE_URL}/api/wms/tile/{z}/{x}/{y}.png?date=${selectedDate}&index_type=${activeLayer.toUpperCase()}`;

            try {
                map.current.addSource(layerId, {
                    type: 'raster',
                    tiles: [tileUrl],
                    tileSize: 256,
                    attribution: 'Sentinel-2 Data'
                });

                // Find where to insert the layer (below labels)
                let beforeLayerId = undefined;
                const layers = map.current.getStyle().layers;
                const labelLayer = layers?.find(l => l.type === 'symbol');
                if (labelLayer) beforeLayerId = labelLayer.id;

                map.current.addLayer({
                    id: layerId,
                    type: 'raster',
                    source: layerId,
                    paint: {
                        'raster-opacity': 0.8,
                        'raster-fade-duration': 300
                    }
                }, beforeLayerId);

            } catch (error) {
                console.error('Error adding layer:', error);
            }
        }

    }, [activeLayer, isLoaded, selectedDate, API_BASE_URL]);

    // Enable area selection with Shift+Click and drag
    useEffect(() => {
        if (!map.current || !isLoaded) return;

        const canvas = map.current.getCanvas();

        const handleMouseDown = (e: MouseEvent) => {
            // Only start drawing if Shift key is pressed
            if (!e.shiftKey) return;
            
            e.preventDefault();
            
            const point = map.current!.unproject([e.clientX, e.clientY]);
            drawStart.current = [point.lng, point.lat];
            setIsDrawing(true);
            
            // Change cursor
            canvas.style.cursor = 'crosshair';
            
            // Disable map dragging while drawing
            map.current!.dragPan.disable();
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDrawing || !drawStart.current) return;

            const point = map.current!.unproject([e.clientX, e.clientY]);
            const start = drawStart.current;
            const end = [point.lng, point.lat];

            // Create rectangle
            const polygon = {
                type: 'Feature' as const,
                geometry: {
                    type: 'Polygon' as const,
                    coordinates: [[
                        [start[0], start[1]],
                        [end[0], start[1]],
                        [end[0], end[1]],
                        [start[0], end[1]],
                        [start[0], start[1]]
                    ]]
                },
                properties: {}
            };

            // Update the drawn area source
            const source = map.current?.getSource('drawn-area') as maplibregl.GeoJSONSource;
            if (source) {
                source.setData({
                    type: 'FeatureCollection',
                    features: [polygon]
                });
            }
        };

        const handleMouseUp = (e: MouseEvent) => {
            if (isDrawing && drawStart.current) {
                const point = map.current!.unproject([e.clientX, e.clientY]);
                const start = drawStart.current;
                const end = [point.lng, point.lat];
                
                // Calculate bounds
                const minLon = Math.min(start[0], end[0]);
                const maxLon = Math.max(start[0], end[0]);
                const minLat = Math.min(start[1], end[1]);
                const maxLat = Math.max(start[1], end[1]);
                
                // Notify parent component
                onAreaSelect({ minLat, maxLat, minLon, maxLon });
                
                setIsDrawing(false);
                drawStart.current = null;
                
                // Reset cursor
                canvas.style.cursor = '';
                
                // Re-enable map dragging
                map.current!.dragPan.enable();
            }
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
            {/* Drawing hint */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white dark:bg-slate-800 px-4 py-2 rounded-lg shadow-lg text-sm text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 pointer-events-none">
                Hold <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded border border-slate-300 dark:border-slate-600 font-mono text-xs">Shift</kbd> and drag to select area
            </div>
        </div>
    );
}
