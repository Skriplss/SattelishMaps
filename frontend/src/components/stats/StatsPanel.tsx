import { useRef } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { X, FileText, Image } from 'lucide-react';
import { cn } from '@/lib/utils';
import { type Chart } from 'chart.js';

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
}

export function StatsPanel({ isOpen, onClose, activeLayer }: StatsPanelProps) {
    const chartRef = useRef<Chart<'line'>>(null);

    // Mock Data (Ported from legacy stats.js generateData)
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const data = {
        labels,
        datasets: [
            {
                label: `${activeLayer?.toUpperCase() || 'NDVI'} Trend`,
                data: labels.map(() => 0.3 + Math.random() * 0.5),
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
                "fixed top-0 right-0 h-screen w-96 bg-sidebar border-l border-slate-200 dark:border-slate-800 shadow-2xl transition-transform duration-300 z-40 flex flex-col pointer-events-auto",
                isOpen ? "translate-x-0" : "translate-x-full"
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100">Area Analysis</h3>
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
                        <label className="text-xs text-slate-500 mb-1 block">From</label>
                        <input type="date" className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm" />
                    </div>
                    <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">To</label>
                        <input type="date" className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-sm" />
                    </div>
                </div>

                {/* Chart */}
                <div className="h-64 bg-slate-50 dark:bg-slate-900 rounded-xl p-2 border border-slate-200 dark:border-slate-700">
                    <Line ref={chartRef} options={options} data={data} />
                </div>

                {/* AI Analysis Box */}
                <div className="space-y-2">
                    <h4 className="font-semibold text-sm text-purple-500 flex items-center gap-2">
                        ✨ AI Analysis
                    </h4>
                    <div className="p-4 bg-purple-50 dark:bg-slate-800/50 border border-purple-100 dark:border-slate-700 rounded-xl text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                        Analysis for <strong>{activeLayerLabel}</strong> shows stable vegetation growth in the selected region. Moisture levels are optimal for this season.
                    </div>
                </div>

                {/* Export Actions */}
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Export</h4>
                    <div className="grid grid-cols-2 gap-3">
                        <button className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                            <Image className="w-4 h-4" />
                            Save Chart
                        </button>
                        <button className="flex items-center justify-center gap-2 p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                            <FileText className="w-4 h-4" />
                            Save Report
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
