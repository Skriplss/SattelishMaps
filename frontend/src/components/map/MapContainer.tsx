import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapContainerProps {
    activeLayer: string | null;
}

export function MapContainer({ activeLayer }: MapContainerProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    // Hardcoded date for MVP verification, will be moved to state later
    const selectedDate = '2024-12-05';
    const API_BASE_URL = 'http://localhost:8000';

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

        map.current.on('load', () => {
            setIsLoaded(true);
            console.log('Map loaded');
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
            console.log(`Adding layer: ${activeLayer} for date ${selectedDate}`);
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

    }, [activeLayer, isLoaded]);

    return <div ref={mapContainer} className="w-full h-full relative" />;
}
