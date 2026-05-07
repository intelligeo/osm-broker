import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[OSM Broker] Uncaught error:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="min-h-screen bg-surface-muted flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-panel border border-surface-border p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7 text-red-500" />
          </div>
          <h1 className="text-xl font-semibold text-ink mb-2">Qualcosa è andato storto</h1>
          <p className="text-sm text-ink-muted mb-1">
            Si è verificato un errore imprevisto nell&apos;applicazione.
          </p>
          {this.state.error && (
            <pre className="mt-3 text-xs text-left text-red-700 bg-red-50 border border-red-100 rounded-lg p-3 overflow-x-auto">
              {this.state.error.message}
            </pre>
          )}
          <button
            type="button"
            onClick={this.handleReset}
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Ricarica l&apos;applicazione
          </button>
        </div>
      </div>
    )
  }
}
