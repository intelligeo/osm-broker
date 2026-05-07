import { MapPin, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-surface-muted flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        {/* Logo mark */}
        <div className="w-16 h-16 rounded-2xl bg-brand-500 flex items-center justify-center mx-auto mb-6 shadow-sm">
          <MapPin className="w-8 h-8 text-white" strokeWidth={2.5} />
        </div>

        <p className="text-7xl font-bold text-brand-500 mb-3">404</p>
        <h1 className="text-2xl font-semibold text-ink mb-3">Pagina non trovata</h1>
        <p className="text-ink-muted text-sm mb-8">
          L&apos;URL richiesto non esiste in questa applicazione.
        </p>

        <Link
          to="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Torna alla mappa
        </Link>
      </div>
    </div>
  )
}
