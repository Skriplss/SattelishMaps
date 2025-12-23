import { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { Sidebar } from './components/layout/Sidebar';

function App() {
  const [activeLayer, setActiveLayer] = useState<string | null>(null);

  // Placeholder for real map stats
  const [count, setCount] = useState(0);

  return (
    <Layout>
      <Sidebar
        activeLayer={activeLayer}
        onLayerSelect={setActiveLayer}
      />

      {/* Main Content Area (Map Placeholder) */}
      <main className="flex-1 relative flex flex-col">
        {/* Top Bar / Date Controls will go here */}

        <div className="flex-1 bg-slate-200 dark:bg-slate-900 flex items-center justify-center relative">

          {/* Temporary Placeholder */}
          <div className="text-center p-10 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 max-w-md mx-6">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              Map Container
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Active Layer: <span className="font-bold text-blue-500">{activeLayer || 'None'}</span>
            </p>

            <button
              onClick={() => setCount(c => c + 1)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Interactions: {count}
            </button>
          </div>

        </div>
      </main>
    </Layout>
  );
}

export default App;
