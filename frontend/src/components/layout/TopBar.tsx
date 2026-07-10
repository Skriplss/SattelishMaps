import { Calendar, Search, MapPin, Loader2, SquareDashed } from 'lucide-react';
import { useState, useEffect, useRef, type ChangeEvent } from 'react';
import { useTranslation } from '@/hooks/useTranslation';
import { COVERAGE } from '@/config';

interface GeocodeResult {
    name: string;
    center: [number, number];
    bbox?: [number, number, number, number];
}

interface TopBarProps {
    selectedDate: string;
    onDateChange: (date: string) => void;
    onLocationSelect: (center: [number, number]) => void;
    onAreaFromSearch: (bbox: [number, number, number, number], center: [number, number]) => void;
}

export function TopBar({ selectedDate, onDateChange, onLocationSelect, onAreaFromSearch }: TopBarProps) {
    const { t, language } = useTranslation();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<GeocodeResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const searchRef = useRef<HTMLDivElement>(null);

    const handleDateChange = (e: ChangeEvent<HTMLInputElement>) => {
        onDateChange(e.target.value);
    };

    // Debounced geocoding via MapTiler, restricted to Slovakia
    useEffect(() => {
        if (query.trim().length < 2) {
            setResults([]);
            return;
        }

        const apiKey = import.meta.env.VITE_MAPTILER_KEY;
        if (!apiKey) return;

        const timer = setTimeout(async () => {
            setIsSearching(true);
            try {
                const bbox = `${COVERAGE.minLon},${COVERAGE.minLat},${COVERAGE.maxLon},${COVERAGE.maxLat}`;
                const url = `https://api.maptiler.com/geocoding/${encodeURIComponent(query.trim())}.json` +
                    `?key=${apiKey}&country=sk&bbox=${bbox}&limit=5&language=${language}`;
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                setResults(
                    (data.features || []).map((f: { place_name: string; center: [number, number]; bbox?: [number, number, number, number] }) => ({
                        name: f.place_name,
                        center: f.center,
                        bbox: f.bbox
                    }))
                );
                setShowResults(true);
            } catch (error) {
                console.error('Geocoding error:', error);
                setResults([]);
            } finally {
                setIsSearching(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query, language]);

    // Close dropdown on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
                setShowResults(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const selectResult = (result: GeocodeResult) => {
        onLocationSelect(result.center);
        setQuery(result.name);
        setShowResults(false);
    };

    return (
        <div className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 z-10 shadow-sm">

            {/* Left: Location search (Slovakia only) */}
            <div className="flex items-center gap-4 flex-1">
                <div className="relative w-64 hidden md:block" ref={searchRef}>
                    {isSearching
                        ? <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
                        : <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />}
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => results.length > 0 && setShowResults(true)}
                        placeholder={t('searchLocation')}
                        className="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all dark:text-slate-200"
                    />
                    {showResults && (
                        <div className="absolute top-full mt-1 w-full bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50">
                            {results.length === 0 ? (
                                <div className="px-3 py-2 text-sm text-slate-400">{t('searchNoResults')}</div>
                            ) : results.map((result, i) => (
                                <div
                                    key={i}
                                    className="flex items-center hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                                >
                                    <button
                                        onClick={() => selectResult(result)}
                                        className="flex items-center gap-2 flex-1 min-w-0 px-3 py-2 text-left text-sm text-slate-700 dark:text-slate-200"
                                    >
                                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                        <span className="truncate">{result.name}</span>
                                    </button>
                                    {result.bbox && (
                                        <button
                                            onClick={() => {
                                                onAreaFromSearch(result.bbox!, result.center);
                                                setQuery(result.name);
                                                setShowResults(false);
                                            }}
                                            title={t('selectAsArea')}
                                            className="p-2 mr-1 rounded-md text-purple-500 hover:bg-purple-100 dark:hover:bg-slate-600 shrink-0"
                                        >
                                            <SquareDashed className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Middle: Date Picker */}
            <div className="flex items-center gap-3">
                <div className="flex items-center bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-1.5 focus-within:ring-2 focus-within:ring-blue-500 transition-all">
                    <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400 mr-2" />
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={handleDateChange}
                        className="bg-transparent border-none text-sm font-medium text-blue-700 dark:text-blue-300 focus:outline-none"
                    />
                </div>
            </div>

            {/* Right: balance flex so the date picker stays centered */}
            <div className="flex-1" />

        </div>
    );
}
