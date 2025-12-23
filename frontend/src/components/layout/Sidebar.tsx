import { useState, useEffect } from 'react';
import { Menu, Globe, Layers, Droplets, CloudRain, Square, Sun, Moon, Info, Languages, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
    onLayerSelect: (layer: string | null) => void;
    activeLayer: string | null;
}

export function Sidebar({ onLayerSelect, activeLayer }: SidebarProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [theme, setTheme] = useState<'light' | 'dark'>(() => {
        const saved = localStorage.getItem('theme');
        return (saved === 'dark' || saved === 'light') ? saved : 'light';
    });
    const [showInfo, setShowInfo] = useState(false);

    // Initialize theme on mount
    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, []);

    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', newTheme);
    };

    const toggleLanguage = () => {
        alert('Language switching will be implemented in next iteration');
    };

    const toggleInfo = () => {
        setShowInfo(!showInfo);
    };

    const layers = [
        { id: 'ndvi', label: 'NDVI', icon: Layers, color: 'text-green-500' },
        { id: 'ndwi', label: 'NDWI', icon: Droplets, color: 'text-blue-500' },
        { id: 'ndbi', label: 'NDBI', icon: Square, color: 'text-orange-500' },
        { id: 'moisture', label: 'Moisture', icon: CloudRain, color: 'text-cyan-500' },
    ];

    return (
        <>
            <aside
                className={cn(
                    "fixed left-0 top-0 h-screen bg-sidebar border-r border-slate-200 dark:border-slate-800 z-50 transition-all duration-300 flex flex-col p-4 shadow-xl",
                    isOpen ? "w-72" : "w-20"
                )}
            >
                {/* Menu Toggle */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-3 p-3 w-full rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors mb-6 text-slate-700 dark:text-slate-200"
                >
                    <Menu className="w-6 h-6 min-w-[24px]" />
                    <span className={cn("font-semibold overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                        Filters
                    </span>
                </button>

                {/* Layers Section */}
                <div className="flex-1 overflow-y-auto overflow-x-hidden space-y-2">
                    {isOpen && <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-2">Satellite Layers</h3>}

                    {layers.map((layer) => (
                        <button
                            key={layer.id}
                            onClick={() => onLayerSelect(activeLayer === layer.id ? null : layer.id)}
                            className={cn(
                                "flex items-center gap-3 p-3 w-full rounded-xl transition-all border border-transparent",
                                activeLayer === layer.id
                                    ? "bg-blue-50 dark:bg-slate-800 border-blue-200 dark:border-slate-700 text-blue-600 dark:text-blue-400"
                                    : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                            )}
                            title={layer.label}
                        >
                            <layer.icon className={cn("w-6 h-6 min-w-[24px]", layer.color)} />
                            <span className={cn("font-medium overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                                {layer.label}
                            </span>
                            {activeLayer === layer.id && isOpen && <ChevronRight className="ml-auto w-4 h-4 opacity-50" />}
                        </button>
                    ))}

                    {/* Separator */}
                    <hr className="my-4 border-slate-200 dark:border-slate-700" />

                    {/* Placeholder for Area Selection (Only if layer active) */}
                    {activeLayer && (
                        <button
                            className="flex items-center gap-3 p-3 w-full rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 mb-2"
                            title="Select Area"
                        >
                            <Globe className="w-6 h-6 min-w-[24px] text-purple-500" />
                            <span className={cn("font-medium overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                                Select Area
                            </span>
                        </button>
                    )}
                </div>

                {/* Bottom Actions */}
                <div className="mt-auto space-y-2 pt-4 border-t border-slate-200 dark:border-slate-700">

                    {/* Language */}
                    <button onClick={toggleLanguage} className="flex items-center gap-3 p-3 w-full rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300">
                        <Languages className="w-6 h-6 min-w-[24px]" />
                        <span className={cn("font-medium overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                            Language (SK)
                        </span>
                    </button>

                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className="flex items-center gap-3 p-3 w-full rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                    >
                        {theme === 'light' ? <Moon className="w-6 h-6 min-w-[24px]" /> : <Sun className="w-6 h-6 min-w-[24px]" />}
                        <span className={cn("font-medium overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                        </span>
                    </button>

                    {/* Info */}
                    <button onClick={toggleInfo} className="flex items-center gap-3 p-3 w-full rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300">
                        <Info className="w-6 h-6 min-w-[24px]" />
                        <span className={cn("font-medium overflow-hidden whitespace-nowrap transition-all", !isOpen && "w-0 opacity-0")}>
                            About
                        </span>
                    </button>
                </div>
            </aside>

            {/* Info Modal */}
            {showInfo && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onClick={toggleInfo}>
                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h3 className="text-xl font-bold mb-4 text-slate-900 dark:text-slate-100">About SattelishMaps</h3>
                        <p className="text-slate-600 dark:text-slate-300 mb-4">
                            Satellite imagery analysis platform for Slovakia. Visualize NDVI, NDWI, NDBI, and Moisture indices using Sentinel-2 data.
                        </p>
                        <button
                            onClick={toggleInfo}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
