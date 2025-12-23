import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="flex flex-col h-screen w-full bg-slate-900 text-white overflow-hidden">
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center p-10 bg-slate-800 rounded-2xl shadow-xl border border-slate-700">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-4">
            Sattelish Maps
          </h1>
          <p className="text-slate-400 mb-8">Modern Frontend initialized with Vite + React + Tailwind</p>

          <button
            onClick={() => setCount(c => c + 1)}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-all active:scale-95"
          >
            Count is {count}
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
