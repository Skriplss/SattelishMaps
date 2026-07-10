import { useRef, useEffect, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    type Chart
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { X, FileText, Image, DownloadCloud, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { areaSizeKm } from '@/config';
import {
    SatelliteAPI,
    TileAPI,
    type AreaStatistics,
    type HistogramBucket,
    type AreaChange
} from '@/services/api';
import { useTranslation } from '@/hooks/useTranslation';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
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

function isoDaysBefore(dateStr: string, days: number): string {
    const d = new Date(dateStr);
    d.setDate(d.getDate() - days);
    return d.toISOString().split('T')[0];
}

export function StatsPanel({ isOpen, onClose, activeLayer, selectedArea, selectedDate }: StatsPanelProps) {
    const chartRef = useRef<Chart<'line'>>(null);
    const [chartData, setChartData] = useState<{ labels: string[], data: number[] }>({ labels: [], data: [] });
    const [areaStats, setAreaStats] = useState<AreaStatistics | null>(null);
    const [histogram, setHistogram] = useState<HistogramBucket[]>([]);
    const [areaChange, setAreaChange] = useState<AreaChange | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [aiAnalysis, setAiAnalysis] = useState<string>('');
    const [dateFrom, setDateFrom] = useState(() => isoDaysBefore(selectedDate, 90));
    const [dateTo, setDateTo] = useState(selectedDate);
    const [regions, setRegions] = useState<string[]>([]);
    const [regionName, setRegionName] = useState<string>('');
    const [isFetchingPixels, setIsFetchingPixels] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const { t } = useTranslation();

    // Load available regions once the panel opens
    useEffect(() => {
        if (!isOpen || regions.length > 0) return;
        SatelliteAPI.fetchRegions().then(list => {
            setRegions(list);
            if (list.length > 0 && !regionName) setRegionName(list[0]);
        });
    }, [isOpen, regions.length, regionName]);

    // Keep the range's end pinned to the map date until the user edits it
    useEffect(() => {
        setDateTo(selectedDate);
        setDateFrom(prev => (prev < selectedDate ? prev : isoDaysBefore(selectedDate, 90)));
    }, [selectedDate]);

    useEffect(() => {
        async function loadData() {
            if (!isOpen || !activeLayer) return;

            setIsLoading(true);

            // If area is selected, fetch pixel-level statistics
            if (selectedArea) {
                try {
                    const [stats, timeseries, hist, change] = await Promise.all([
                        TileAPI.fetchAreaStatistics(
                            selectedArea.minLat,
                            selectedArea.maxLat,
                            selectedArea.minLon,
                            selectedArea.maxLon,
                            selectedDate,
                            activeLayer
                        ),
                        TileAPI.fetchAreaTimeseries(selectedArea, activeLayer, dateFrom, dateTo),
                        TileAPI.fetchAreaHistogram(selectedArea, activeLayer, selectedDate),
                        TileAPI.fetchAreaChange(selectedArea, activeLayer, dateFrom, dateTo)
                    ]);

                    setAreaStats(stats);
                    setHistogram(hist);
                    setAreaChange(change);

                    if (timeseries.length > 0) {
                        setChartData({
                            labels: timeseries.map(p => new Date(p.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
                            data: timeseries.map(p => p.mean)
                        });
                    } else if (stats && stats.mean !== null) {
                        setChartData({ labels: [selectedDate], data: [stats.mean] });
                    } else {
                        setChartData({ labels: [], data: [] });
                    }

                    if (stats && stats.mean !== null) {
                        generateAIAnalysis(activeLayer, stats);
                    } else {
                        setAiAnalysis('No pixel data available for the selected area. Try selecting a different area or date.');
                    }
                } catch (error) {
                    console.error('Error fetching area stats:', error);
                    setChartData({ labels: [], data: [] });
                    setAreaStats(null);
                    setHistogram([]);
                    setAreaChange(null);
                    setAiAnalysis('Error loading data for selected area.');
                }
            } else {
                setAreaStats(null);
                setHistogram([]);
                setAreaChange(null);

                if (!regionName) {
                    setChartData({ labels: [], data: [] });
                    setAiAnalysis('No regions with statistics yet. Load data via the scheduler or scripts.');
                    setIsLoading(false);
                    return;
                }

                // Fetch historical data for region
                const history = await SatelliteAPI.fetchRegionHistory(regionName, activeLayer, dateFrom, dateTo);

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
    }, [isOpen, activeLayer, selectedArea, selectedDate, dateFrom, dateTo, regionName, refreshKey]);

    // Pull raw pixel data from Sentinel Hub for the selected area, then reload
    const loadPixelData = async () => {
        if (!selectedArea || isFetchingPixels) return;
        setIsFetchingPixels(true);
        try {
            await TileAPI.fetchPixels(selectedArea, selectedDate);
            setRefreshKey(k => k + 1);
        } finally {
            setIsFetchingPixels(false);
        }
    };

    const generateAIAnalysis = (layer: string, stats: AreaStatistics) => {
        const value = stats.mean as number;
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

        if (stats.median !== null && stats.std !== null && stats.std > 0.15) {
            analysis += ` Note: high variability (σ=${stats.std.toFixed(3)}, median ${stats.median.toFixed(3)}) suggests the area is not homogeneous.`;
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
                label: `${activeLayer?.toUpperCase() || 'NDVI'} ${selectedArea ? `(${t('selectedAreaLabel')})` : regionName ? `— ${regionName}` : ''}`,
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
                text: selectedArea ? t('areaTrendTitle') : t('regionalAnalysisTitle'),
            },
        },
        // NDWI/NDBI/Moisture routinely go negative — let the axis adapt
        scales: {
            y: {
                suggestedMin: -0.2,
                suggestedMax: 1
            }
        }
    };

    const histogramData = {
        labels: histogram.map(b => b.range_min.toFixed(1)),
        datasets: [
            {
                label: 'Pixels',
                data: histogram.map(b => b.count),
                backgroundColor: 'rgba(65, 166, 54, 0.6)',
            },
        ],
    };

    const histogramOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: true, text: `${activeLayer?.toUpperCase()} ${t('distribution')}` },
            tooltip: {
                callbacks: {
                    title: (items: { dataIndex: number }[]) => {
                        const b = histogram[items[0].dataIndex];
                        return b ? `${b.range_min.toFixed(2)} … ${b.range_max.toFixed(2)}` : '';
                    }
                }
            }
        },
        scales: {
            x: { ticks: { maxRotation: 0, autoSkip: true } }
        }
    };

    const activeLayerLabel = activeLayer?.toUpperCase() || 'NDVI';

    const downloadChart = () => {
        const base64 = chartRef.current?.toBase64Image();
        if (!base64) return;
        const a = document.createElement('a');
        a.href = base64;
        a.download = `${activeLayerLabel}_${dateFrom}_${dateTo}.png`;
        a.click();
    };

    const downloadReport = () => {
        const fmt = (v: number | null | undefined) => (v === null || v === undefined ? '—' : v.toFixed(3));
        const changePct = (count: number) =>
            areaChange && areaChange.pixel_count > 0
                ? `${((count / areaChange.pixel_count) * 100).toFixed(1)}%`
                : '—';

        const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>${activeLayerLabel} Report</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; color: #1e293b; }
h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 1.5rem; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; font-size: 0.9rem; }
.muted { color: #64748b; font-size: 0.85rem; }
</style></head><body>
<h1>SattelishMaps — ${activeLayerLabel} Report</h1>
<p class="muted">Generated: ${new Date().toISOString().split('T')[0]} · Period: ${dateFrom} → ${dateTo}</p>
${selectedArea ? `<p class="muted">Area: [${selectedArea.minLon.toFixed(4)}, ${selectedArea.minLat.toFixed(4)}] → [${selectedArea.maxLon.toFixed(4)}, ${selectedArea.maxLat.toFixed(4)}]</p>` : `<p class="muted">Region: ${regionName}</p>`}
${areaStats && areaStats.mean !== null ? `
<h2>Statistics (${selectedDate})</h2>
<table>
<tr><th>Mean</th><th>Median</th><th>Min</th><th>Max</th><th>σ</th><th>Pixels</th></tr>
<tr><td>${fmt(areaStats.mean)}</td><td>${fmt(areaStats.median)}</td><td>${fmt(areaStats.min)}</td><td>${fmt(areaStats.max)}</td><td>${fmt(areaStats.std)}</td><td>${areaStats.pixel_count}</td></tr>
</table>` : ''}
${areaChange ? `
<h2>Change: ${areaChange.date_a} → ${areaChange.date_b}</h2>
<table>
<tr><th>Mean before</th><th>Mean after</th><th>Δ</th><th>Improved</th><th>Declined</th><th>Stable</th></tr>
<tr><td>${fmt(areaChange.mean_a)}</td><td>${fmt(areaChange.mean_b)}</td><td>${fmt(areaChange.mean_diff)}</td>
<td>${changePct(areaChange.improved_count)}</td><td>${changePct(areaChange.declined_count)}</td><td>${changePct(areaChange.stable_count)}</td></tr>
</table>` : ''}
<h2>Analysis</h2>
<p>${aiAnalysis || 'No analysis available.'}</p>
${chartRef.current ? `<h2>Chart</h2><img src="${chartRef.current.toBase64Image()}" style="max-width:100%" alt="chart" />` : ''}
</body></html>`;

        const blob = new Blob([html], { type: 'text/html' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${activeLayerLabel}_report_${selectedDate}.html`;
        a.click();
        URL.revokeObjectURL(a.href);
    };

    const statCells: Array<{ label: string; value: number | null }> = areaStats ? [
        { label: t('mean'), value: areaStats.mean },
        { label: t('median'), value: areaStats.median },
        { label: t('min'), value: areaStats.min },
        { label: t('max'), value: areaStats.max },
        { label: 'σ', value: areaStats.std },
        { label: t('pixels'), value: areaStats.pixel_count },
    ] : [];

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

                {/* Region selector (only in region mode) */}
                {!selectedArea && regions.length > 0 && (
                    <div>
                        <label className="text-xs text-slate-500 mb-1 block">{t('region')}</label>
                        <select
                            value={regionName}
                            onChange={(e) => setRegionName(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm text-slate-700 dark:text-slate-200"
                        >
                            {regions.map(r => (
                                <option key={r} value={r}>{r}</option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Controls */}
                <div className="flex gap-2">
                    <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">{t('from')}</label>
                        <input
                            type="date"
                            value={dateFrom}
                            max={dateTo}
                            onChange={(e) => setDateFrom(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm"
                        />
                    </div>
                    <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">{t('to')}</label>
                        <input
                            type="date"
                            value={dateTo}
                            min={dateFrom}
                            onChange={(e) => setDateTo(e.target.value)}
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm"
                        />
                    </div>
                </div>

                {/* Selected area dimensions */}
                {selectedArea && (
                    <div className="text-xs text-slate-400 -mt-3">
                        {(() => { const s = areaSizeKm(selectedArea); return `${s.w.toFixed(1)} × ${s.h.toFixed(1)} km`; })()}
                    </div>
                )}

                {/* No pixel data for this area yet — offer to load it */}
                {selectedArea && !isLoading && (!areaStats || areaStats.mean === null) && (
                    <button
                        onClick={loadPixelData}
                        disabled={isFetchingPixels}
                        className="flex items-center justify-center gap-2 w-full p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-xl text-sm font-medium transition-colors"
                    >
                        {isFetchingPixels
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loadingPixelData')}</>
                            : <><DownloadCloud className="w-4 h-4" /> {t('loadPixelData')}</>}
                    </button>
                )}

                {/* Area statistics grid */}
                {areaStats && areaStats.mean !== null && (
                    <div className="grid grid-cols-3 gap-2">
                        {statCells.map(cell => (
                            <div key={cell.label} className="p-2 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-center">
                                <div className="text-[10px] uppercase tracking-wider text-slate-400">{cell.label}</div>
                                <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                                    {cell.value === null
                                        ? '—'
                                        : Number.isInteger(cell.value) ? cell.value : cell.value.toFixed(3)}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Change detection card */}
                {areaChange && areaChange.mean_diff !== null && (
                    <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            {t('change')}: {areaChange.date_a} → {areaChange.date_b}
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-sm text-slate-500">{areaChange.mean_a?.toFixed(3)}</span>
                            <span className="text-slate-400">→</span>
                            <span className="text-sm text-slate-500">{areaChange.mean_b?.toFixed(3)}</span>
                            <span className={cn(
                                "text-sm font-bold",
                                areaChange.mean_diff > 0 ? "text-green-600" : areaChange.mean_diff < 0 ? "text-red-500" : "text-slate-500"
                            )}>
                                {areaChange.mean_diff > 0 ? '+' : ''}{areaChange.mean_diff.toFixed(3)}
                            </span>
                        </div>
                        <div className="flex gap-3 text-xs">
                            <span className="text-green-600">▲ {t('improved')}: {((areaChange.improved_count / areaChange.pixel_count) * 100).toFixed(0)}%</span>
                            <span className="text-red-500">▼ {t('declined')}: {((areaChange.declined_count / areaChange.pixel_count) * 100).toFixed(0)}%</span>
                            <span className="text-slate-500">— {t('stable')}: {((areaChange.stable_count / areaChange.pixel_count) * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                )}

                {/* Chart */}
                <div className="h-64 bg-slate-50 dark:bg-slate-900 rounded-xl p-2 border border-slate-200 dark:border-slate-700 relative">
                    {isLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-sm z-10">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        </div>
                    )}
                    <Line ref={chartRef} options={options} data={data} />
                </div>

                {/* Histogram — only for selected areas with pixel data */}
                {selectedArea && histogram.length > 0 && (
                    <div className="h-48 bg-slate-50 dark:bg-slate-900 rounded-xl p-2 border border-slate-200 dark:border-slate-700">
                        <Bar options={histogramOptions} data={histogramData} />
                    </div>
                )}

                {/* AI Analysis Box */}
                <div className="space-y-2">
                    <h4 className="font-semibold text-sm text-purple-500 flex items-center gap-2">
                        ✨ {t('aiAnalysis')}
                    </h4>
                    <div className="p-4 bg-purple-50 dark:bg-slate-800/50 border border-purple-100 dark:border-slate-700 rounded-xl text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                        {isLoading ? (
                            <div className="flex items-center gap-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
                                <span>{t('analyzing')}</span>
                            </div>
                        ) : (
                            aiAnalysis || `${activeLayerLabel}: ${t('noAnalysisYet')}`
                        )}
                    </div>
                </div>

                {/* Export Actions */}
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{t('export')}</h4>
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={downloadChart}
                            className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            <Image className="w-4 h-4" />
                            {t('saveChart')}
                        </button>
                        <button
                            onClick={downloadReport}
                            className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            <FileText className="w-4 h-4" />
                            {t('saveReport')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
