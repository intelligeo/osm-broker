import { MapPin, Github, Menu } from 'lucide-react'

interface NavbarProps {
  onToggleSidebar: () => void
}

export default function Navbar({ onToggleSidebar }: NavbarProps) {
  return (
    <header className="h-16 bg-white border-b border-surface-border flex items-center px-4 sm:px-6 gap-3 shadow-card z-10 relative">
      {/* Hamburger — solo mobile */}
      <button
        type="button"
        onClick={onToggleSidebar}
        aria-label="Apri/chiudi pannello di configurazione"
        className="sm:hidden p-2 rounded-lg text-ink-light hover:text-ink hover:bg-surface-subtle transition-colors"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Logo */}
      <div className="flex items-center gap-2 select-none">
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center shadow-sm">
          <MapPin className="w-4 h-4 text-white" strokeWidth={2.5} />
        </div>
        <span className="font-semibold text-ink text-lg tracking-tight">
          OSM <span className="text-brand-500">Broker</span>
        </span>
      </div>

      <div className="ml-1 h-5 w-px bg-surface-border hidden sm:block" />

      {/* Tagline */}
      <p className="text-ink-muted text-sm hidden sm:block">
        Search · Clip · Export OpenStreetMap data with GIS symbology
      </p>

      <div className="ml-auto flex items-center gap-3">
        <span className="hidden md:inline-flex items-center gap-1.5 text-xs font-medium text-ink-light bg-surface-subtle border border-surface-border rounded-full px-3 py-1">
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block animate-pulse" />
          Live OSM data
        </span>

        {import.meta.env.VITE_AUTH_ENABLED === 'true' && (
          <button className="text-sm font-medium text-brand-600 hover:text-brand-700 transition-colors">
            Sign in
          </button>
        )}

        <a
          href="https://github.com/geometalab/osm-broker"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Source code on GitHub"
          className="text-ink-light hover:text-ink transition-colors"
        >
          <Github className="w-5 h-5" />
        </a>
      </div>
    </header>
  )
}
