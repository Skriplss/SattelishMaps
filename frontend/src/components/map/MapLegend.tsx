import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { useTranslation } from '@/hooks/useTranslation';

interface MapLegendProps {
    activeLayer: string | null;
    sidebarOpen: boolean;
}

// Color stops mirror the backend palettes (pixel_tile_renderer.py /
// Sentinel Hub evalscripts) so the legend matches what the map shows.
const layerInfo: Record<string, { name: string; gradient: string; range: [string, string] }> = {
    ndvi: {
        name: 'NDVI',
        gradient: 'linear-gradient(to right, #804D1A, #CCB366, #E6E699, #99CC4D, #4DB333, #1A801A)',
        range: ['-1', '1']
    },
    ndwi: {
        name: 'NDWI',
        gradient: 'linear-gradient(to right, #804D1A, #CCB380, #80CCE6, #4D80E6, #0000CC, #000080)',
        range: ['-1', '1']
    },
    ndbi: {
        name: 'NDBI',
        gradient: 'linear-gradient(to right, #0000CC, #1A801A, #CCB380, #994D1A, #80331A, #800000)',
        range: ['-1', '1']
    },
    moisture: {
        name: 'Moisture',
        gradient: 'linear-gradient(to right, #800000, #CC3333, #E68080, #FFFF00, #99E699, #00FFFF, #000080)',
        range: ['-1', '1']
    }
};

export function MapLegend({ activeLayer, sidebarOpen }: MapLegendProps) {
    const [isVisible, setIsVisible] = useState(false);
    const { t } = useTranslation();

    useEffect(() => {
        setIsVisible(!!activeLayer);
    }, [activeLayer]);

    if (!activeLayer || !isVisible) return null;

    const info = layerInfo[activeLayer];
    if (!info) return null;

    return (
        <div className={cn(
            "absolute bottom-8 bg-white dark:bg-slate-800 rounded-lg shadow-xl p-4 z-10 min-w-[200px] border border-slate-200 dark:border-slate-700 transition-all duration-300",
            // Container starts after the collapsed sidebar (pl-20 = 5rem);
            // expanded sidebar is w-72 (18rem) → 13rem further + 1rem gap
            sidebarOpen ? "left-[14rem]" : "left-4"
        )}>
            <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{info.name}</h4>
                <button
                    onClick={() => setIsVisible(false)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                    ✕
                </button>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-3">{t(`legendDesc.${activeLayer}`)}</p>

            {/* Color gradient — matches the actual tile palette */}
            <div className="h-4 rounded mb-2" style={{ background: info.gradient }}></div>

            {/* Range labels */}
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>{info.range[0]}</span>
                <span>{info.range[1]}</span>
            </div>
        </div>
    );
}
