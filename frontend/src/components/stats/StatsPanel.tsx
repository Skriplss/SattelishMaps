import { useRef, useEffect, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    type Chart
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { X, FileText, Image } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SatelliteAPI, TileAPI } from '@/services/api';
import { useTranslation } from '@/hooks/useTranslation';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface StatsPanelProps {
    isOpen: boolean;
    onClose: () => void;
    activeLayer: string | null;
    selectedArea: { minLat: number; maxLat: number; minLon: number; maxLon: number } | null;
    selectedDate: string;
}

export function StatsPanel({ isOpen, onClose, activeLayer, selectedArea, selectedDate }: StatsPanelProps) {
    const chartRef = useRef<Chart<'line'>>(null);
    const [chartData, setChartData] = useState<{ labels: string[], data: number[] }>({ labels: [], data: [] });
    const [isLoading, setIsLoading] = useState(false);
    const [aiAnalysis, setAiAnalysis] = useState<string>('');
    const { t } = useTranslation();

    // Default region for MVP
    const regionName = "Default Region";

    useEffect(() => {
        async function loadData() {
            if (!isOpen || !activeLayer) return;

            setIsLoading(true);
            
            // If area is selected, fetch pixel-level statistics
            if (selectedArea) {
                try {
                    const areaStats = await TileAPI.fetchAreaStatistics(
                        selectedArea.minLat,
                        selectedArea.maxLat,
                        selectedArea.minLon,
                        selectedArea.maxLon,
                        selectedDate,
                        activeLayer
                    );
                    
                    if (areaStats && areaStats.mean !== null) {
                        // Create simple chart with current value
                        setChartData({
                            labels: [selectedDate],
                            data: [areaStats.mean]
                        });
                        
                        // Generate AI analysis based on area stats
                        generateAIAnalysis(activeLayer, areaStats);
                    } else {
                        setChartData({ labels: [], data: [] });
                        setAiAnalysis('No pixel data available for the selected area. Try selecting a different area or date.');
                    }
                } catch (error) {
                    console.error('Error fetching area stats:', error);
                    setChartData({ labels: [], data: [] });
                    setAiAnalysis('Error loading data for selected area.');
                }
            } else {
                // Fetch historical data for region
                const history = await SatelliteAPI.fetchRegionHistory(regionName, activeLayer);

                if (history && history.length > 0) {
                    const sorted = history.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

                    setChartData({
                        labels: sorted.map(h => new Date(h.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
                        data: sorted.map(h => h.mean)
                    });
                    
                    // Generate AI analysis
                    const avgValue = sorted.reduce((sum, h) => sum + h.mean, 0) / sorted.length;
                    const trend = sorted.length > 1 ? 
                        (sorted[sorted.length - 1].mean > sorted[0].mean ? 'increasing' : 'decreasing') : 'stable';
                    
                    generateAIAnalysisFromHistory(activeLayer, avgValue, trend);
                } else {
                    setChartData({ labels: [], data: [] });
                    setAiAnalysis('No data available for the selected area and time period.');
                }
            }
            
            setIsLoading(false);
        }

        loadData();
    }, [isOpen, activeLayer, selectedArea, selectedDate]);
    
    const generateAIAnalysis = (layer: string, stats: any) => {
        const value = stats.mean;
        let analysis = '';
        
        if (layer === 'ndvi') {
            if (value > 0.6) {
                analysis = `Excellent vegetation health detected in selected area. Average NDVI of ${value.toFixed(3)} indicates dense, healthy vegetation covering ${stats.pixel_count} pixels.`;
            } else if (value > 0.4) {
                analysis = `Good vegetation coverage in selected area. Average NDVI of ${value.toFixed(3)} shows moderate to healthy vegetation across ${stats.pixel_count} pixels.`;
            } else if (value > 0.2) {
                analysis = `Moderate vegetation detected. Average NDVI of ${value.toFixed(3)} indicates sparse to moderate vegetation in the selected area (${stats.pixel_count} pixels).`;
            } else {
                analysis = `Limited vegetation in selected area. Average NDVI of ${value.toFixed(3)} indicates sparse vegetation or bare soil across ${stats.pixel_count} pixels.`;
            }
        } else if (layer === 'ndwi') {
            if (value > 0.3) {
                analysis = `High water content detected. Average NDWI of ${value.toFixed(3)} indicates significant water presence in ${stats.pixel_count} pixels.`;
            } else if (value > 0) {
                analysis = `Moderate moisture levels. Average NDWI of ${value.toFixed(3)} shows balanced water content across ${stats.pixel_count} pixels.`;
            } else {
                analysis = `Low water content. Average NDWI of ${value.toFixed(3)} indicates dry conditions in the selected area (${stats.pixel_count} pixels).`;
            }
        } else {
            analysis = `Analysis for ${layer.toUpperCase()}: Average value ${value.toFixed(3)} across ${stats.pixel_count} pixels.`;
        }
        
        setAiAnalysis(analysis);
    };
    
    const generateAIAnalysisFromHistory = (layer: string, avgValue: number, trend: string) => {
        let analysis = '';
        
        if (layer === 'ndvi') {
            if (avgValue > 0.6) {
                analysis = `Excellent vegetation health detected. Average NDVI of ${avgValue.toFixed(2)} indicates dense, healthy vegetation. Trend is ${trend}.`;
            } else if (avgValue > 0.4) {
                analysis = `Good vegetation coverage. Average NDVI of ${avgValue.toFixed(2)} shows moderate to healthy vegetation. Trend is ${trend}.`;
            } else {
                analysis = `Limited vegetation detected. Average NDVI of ${avgValue.toFixed(2)} indicates sparse vegetation or bare soil. Trend is ${trend}.`;
            }
        } else if (layer === 'ndwi') {
            if (avgValue > 0.3) {
                analysis = `High water content detected. Average NDWI of ${avgValue.toFixed(2)} indicates significant water presence. Trend is ${trend}.`;
            } else if (avgValue > 0) {
                analysis = `Moderate moisture levels. Average NDWI of ${avgValue.toFixed(2)} shows balanced water content. Trend is ${trend}.`;
            } else {
                analysis = `Low water content. Average NDWI of ${avgValue.toFixed(2)} indicates dry conditions. Trend is ${trend}.`;
            }
        } else {
            analysis = `Analysis for ${layer.toUpperCase()}: Average value ${avgValue.toFixed(2)}, trend is ${trend}.`;
        }
        
        setAiAnalysis(analysis);
    };

    const data = {
        labels: chartData.labels,
        datasets: [
            {
                label: `${activeLayer?.toUpperCase() || 'NDVI'} Trend - ${regionName}`,
                data: chartData.data,
                borderColor: '#41A636',
                backgroundColor: 'rgba(65, 166, 54, 0.5)',
                tension: 0.4,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: 'Regional Analysis',
            },
        },
        scales: {
            y: {
                min: 0,
                max: 1
            }
        }
    };

    const activeLayerLabel = activeLayer?.toUpperCase() || 'NDVI';

    return (
        <div
            className={cn(
                "fixed top-0 right-0 h-screen w-96 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl transition-transform duration-300 z-40 flex flex-col pointer-events-auto",
                isOpen ? "translate-x-0" : "translate-x-full"
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100">{t('areaAnalysis')}</h3>
                <button
                    onClick={onClose}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors text-slate-500"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">

                {/* Controls */}
                <div className="flex gap-2">
                    <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">{t('from')}</label>
                        <input type="date" className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm" />
                    </div>
                    <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">{t('to')}</label>
                        <input type="date" className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm" />
                    </div>
                </div>

                {/* Chart */}
                <div className="h-64 bg-slate-50 dark:bg-slate-900 rounded-xl p-2 border border-slate-200 dark:border-slate-700 relative">
                    {isLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-sm z-10">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        </div>
                    )}
                    <Line ref={chartRef} options={options} data={data} />
                </div>

                {/* AI Analysis Box */}
                <div className="space-y-2">
                    <h4 className="font-semibold text-sm text-purple-500 flex items-center gap-2">
                        ✨ {t('aiAnalysis')}
                    </h4>
                    <div className="p-4 bg-purple-50 dark:bg-slate-800/50 border border-purple-100 dark:border-slate-700 rounded-xl text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                        {isLoading ? (
                            <div className="flex items-center gap-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
                                <span>Analyzing data...</span>
                            </div>
                        ) : (
                            aiAnalysis || `Analysis for ${activeLayerLabel} shows stable conditions in the selected region.`
                        )}
                    </div>
                </div>

                {/* Export Actions */}
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{t('export')}</h4>
                    <div className="grid grid-cols-2 gap-3">
                        <button className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                            <Image className="w-4 h-4" />
                            {t('saveChart')}
                        </button>
                        <button className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                            <FileText className="w-4 h-4" />
                            {t('saveReport')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
