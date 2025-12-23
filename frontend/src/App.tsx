import { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { Sidebar } from './components/layout/Sidebar';

import { MapContainer } from './components/map/MapContainer';

function App() {
  const [activeLayer, setActiveLayer] = useState<string | null>(null);

  return (
    <Layout>
      <Sidebar
        activeLayer={activeLayer}
        onLayerSelect={setActiveLayer}
      />

      {/* Main Content Area */}
      <main className="flex-1 relative flex flex-col bg-slate-200 dark:bg-slate-900">
        <MapContainer activeLayer={activeLayer} />
      </main>
    </Layout>
  );
}

export default App;
