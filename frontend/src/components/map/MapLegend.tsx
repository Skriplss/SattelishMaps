import { useEffect, useState } from 'react';

interface MapLegendProps {
    activeLayer: string | null;
}

const layerInfo: Record<string, { name: string; color: string; description: string; range: string }> = {
    ndvi: {
        name: 'NDVI',
        color: 'from-red-500 via-yellow-500 to-green-500',
        description: 'Normalized Difference Vegetation Index',
        range: '-1 to 1'
    },
    ndwi: {
        name: 'NDWI',
        color: 'from-brown-500 via-yellow-500 to-blue-500',
        description: 'Normalized Difference Water Index',
        range: '-1 to 1'
    },
    ndbi: {
        name: 'NDBI',
        color: 'from-green-500 via-yellow-500 to-red-500',
        description: 'Normalized Difference Built-up Index',
        range: '-1 to 1'
    },
    moisture: {
        name: 'Moisture',
        color: 'from-yellow-500 via-green-500 to-blue-500',
        description: 'Soil Moisture Index',
        range: '0 to 1'
    }
};

export function MapLegend({ activeLayer }: MapLegendProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(!!activeLayer);
    }, [activeLayer]);

    if (!activeLayer || !isVisible) return null;

    const info = layerInfo[activeLayer];
    if (!info) return null;

    return (
        <div className="absolute bottom-8 left-20 bg-white dark:bg-slate-800 rounded-lg shadow-xl p-4 z-10 min-w-[200px] border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{info.name}</h4>
                <button
                    onClick={() => setIsVisible(false)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                    ✕
                </button>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-3">{info.description}</p>

            {/* Color gradient */}
            <div className={`h-4 rounded bg-gradient-to-r ${info.color} mb-2`}></div>

            {/* Range labels */}
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>{info.range.split(' to ')[0]}</span>
                <span>{info.range.split(' to ')[1]}</span>
            </div>
        </div>
    );
}
