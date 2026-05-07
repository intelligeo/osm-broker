import { useState, useCallback } from 'react'
import Navbar from './components/Layout/Navbar'
import MapView from './components/Map/MapView'
import AOIPanel from './components/AOIPanel/AOIPanel'
import { useJob } from './hooks/useJob'
import { useAuth } from './hooks/useAuth'
import type { AOIFeature, ExportFormat } from './types'

export default function App() {
  const [aoi, setAoi] = useState<AOIFeature | null>(null)
  const [areaKm2, setAreaKm2] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { job, error, submit, reset } = useJob()
  const { user, isLoading, authEnabled, signIn, signOut } = useAuth()

  const handleAOIChange = useCallback((feature: AOIFeature | null, km2: number) => {
    setAoi(feature)
    setAreaKm2(km2)
  }, [])

  const handleSubmit = useCallback(
    (format: ExportFormat, symbology: boolean) => {
      if (!aoi) return
      submit({ aoi, format, symbology })
    },
    [aoi, submit],
  )

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        user={user}
        isLoading={isLoading}
        authEnabled={authEnabled}
        onSignIn={signIn}
        onSignOut={signOut}
      />
      <div className="flex flex-1 overflow-hidden relative">
        {/* Overlay sfondo mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/30 z-20 sm:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
        )}

        {/* Sidebar — sempre visibile su desktop, overlay su mobile */}
        <div
          className={[
            'absolute sm:relative z-30 sm:z-auto h-full transition-transform duration-300',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full sm:translate-x-0',
          ].join(' ')}
        >
          <AOIPanel
            aoi={aoi}
            areaKm2={areaKm2}
            job={job}
            error={error}
            onSubmit={handleSubmit}
            onReset={reset}
            onClose={() => setSidebarOpen(false)}
          />
        </div>

        {/* Mappa */}
        <main className="flex-1 relative min-w-0">
          <MapView onAOIChange={handleAOIChange} />
          {!aoi && areaKm2 === 0 && (
            <div className="absolute bottom-12 left-1/2 -translate-x-1/2 pointer-events-none">
              <div className="panel-glass px-4 py-2 text-sm text-ink-muted flex items-center gap-2 shadow-panel">
                <span>▱</span>
                <span>Clicca sul pulsante poligono per disegnare l&apos;area di interesse</span>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
