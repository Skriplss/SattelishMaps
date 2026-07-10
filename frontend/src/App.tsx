import { useState, useCallback } from 'react';
import { Layout } from './components/layout/Layout';
import { Sidebar } from './components/layout/Sidebar';

import { MapContainer } from './components/map/MapContainer';
import { StatsPanel } from './components/stats/StatsPanel';

import { MapLegend } from './components/map/MapLegend';

import { TopBar } from './components/layout/TopBar';
import { clampAreaToCoverage } from './config';

type Area = { minLat: number; maxLat: number; minLon: number; maxLon: number };

function App() {
  const [activeLayer, setActiveLayer] = useState<string | null>(null);
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('2024-12-05');
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [drawMode, setDrawMode] = useState(false);
  const [flyTo, setFlyTo] = useState<{ center: [number, number] } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleAreaSelect = useCallback((area: Area | null) => {
    setSelectedArea(area);
    setDrawMode(false);
    if (area) {
      setIsStatsOpen(true);
    }
  }, []);

  const handleLocationSelect = useCallback((center: [number, number]) => {
    setFlyTo({ center });
  }, []);

  // Search result → analysis area (precise city/village bounds from geocoder)
  const handleAreaFromSearch = useCallback((bbox: [number, number, number, number], center: [number, number]) => {
    const clamped = clampAreaToCoverage({
      minLon: bbox[0], minLat: bbox[1], maxLon: bbox[2], maxLat: bbox[3]
    });
    if (clamped) {
      setSelectedArea(clamped);
      setIsStatsOpen(true);
    }
    setFlyTo({ center });
  }, []);

  return (
    <Layout>
      <Sidebar
        activeLayer={activeLayer}
        onLayerSelect={(layer) => {
          setActiveLayer(layer);
          if (layer) setIsStatsOpen(true);
        }}
        isOpen={sidebarOpen}
        onToggleOpen={() => setSidebarOpen(prev => !prev)}
        drawMode={drawMode}
        onToggleDrawMode={() => setDrawMode(prev => !prev)}
        hasSelection={selectedArea !== null}
        onClearSelection={() => setSelectedArea(null)}
      />

      <StatsPanel
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
        activeLayer={activeLayer}
        selectedArea={selectedArea}
        selectedDate={selectedDate}
      />

      {/* Main Content Area */}
      <main className="flex-1 relative flex flex-col bg-slate-200 dark:bg-slate-900 pl-20 w-full">
        <TopBar
          selectedDate={selectedDate}
          onDateChange={setSelectedDate}
          onLocationSelect={handleLocationSelect}
          onAreaFromSearch={handleAreaFromSearch}
        />
        <div className="flex-1 relative w-full">
          <MapContainer
            activeLayer={activeLayer}
            selectedDate={selectedDate}
            selectedArea={selectedArea}
            drawMode={drawMode}
            flyTo={flyTo}
            onAreaSelect={handleAreaSelect}
          />
          <MapLegend activeLayer={activeLayer} sidebarOpen={sidebarOpen} />
        </div>
      </main>
    </Layout>
  );
}

export default App;
