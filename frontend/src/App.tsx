import { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { Sidebar } from './components/layout/Sidebar';

import { MapContainer } from './components/map/MapContainer';
import { StatsPanel } from './components/stats/StatsPanel';

import { TopBar } from './components/layout/TopBar';

function App() {
  const [activeLayer, setActiveLayer] = useState<string | null>(null);
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('2024-12-05');

  return (
    <Layout>
      <Sidebar
        activeLayer={activeLayer}
        onLayerSelect={(layer) => {
          setActiveLayer(layer);
          if (layer) setIsStatsOpen(true);
        }}
      />

      <StatsPanel
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
        activeLayer={activeLayer}
      />

      {/* Main Content Area */}
      <main className="flex-1 relative flex flex-col bg-slate-200 dark:bg-slate-900">
        <TopBar
          selectedDate={selectedDate}
          onDateChange={setSelectedDate}
        />
        <div className="flex-1 relative">
          <MapContainer
            activeLayer={activeLayer}
            selectedDate={selectedDate}
          />
        </div>
      </main>
    </Layout>
  );
}

export default App;
