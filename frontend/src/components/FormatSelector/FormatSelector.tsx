import type { ExportFormat, FormatOption } from '../../types'
import { clsx } from 'clsx'

const FORMATS: FormatOption[] = [
  {
    id: 'gpkg',
    label: 'GeoPackage',
    description: 'Standard OGC, compatibile QGIS/ArcGIS',
    icon: '🟩',
    ext: '.gpkg',
  },
  {
    id: 'geojson',
    label: 'GeoJSON',
    description: 'Standard web-GIS, testo human-readable',
    icon: '🔵',
    ext: '.geojson',
  },
  {
    id: 'fgdb',
    label: 'File Geodatabase',
    description: 'Formato nativo Esri ArcGIS',
    icon: '🟧',
    ext: '.gdb',
  },
  {
    id: 'duckdb',
    label: 'DuckDB / GeoParquet',
    description: 'Analisi OLAP ad alte prestazioni',
    icon: '🦆',
    ext: '.duckdb',
  },
]

interface FormatSelectorProps {
  value: ExportFormat
  onChange: (fmt: ExportFormat) => void
}

export default function FormatSelector({ value, onChange }: FormatSelectorProps) {
  return (
    <div>
      <p className="text-xs font-semibold tracking-widest text-ink-light uppercase mb-2">
        Formato output
      </p>
      <div className="grid grid-cols-2 gap-2">
        {FORMATS.map((fmt) => (
          <button
            key={fmt.id}
            type="button"
            onClick={() => onChange(fmt.id)}
            className={clsx(
              'flex flex-col items-start p-3 rounded-lg border text-left transition-all',
              value === fmt.id
                ? 'border-brand-400 bg-brand-50 ring-1 ring-brand-400'
                : 'border-surface-border bg-white hover:bg-surface-subtle hover:border-brand-200',
            )}
          >
            <span className="text-base">{fmt.icon}</span>
            <span className="text-sm font-semibold text-ink mt-1">{fmt.label}</span>
            <span className="text-xs text-ink-light mt-0.5 leading-tight">{fmt.description}</span>
            <code className="text-xs text-ink-light font-mono mt-1">{fmt.ext}</code>
          </button>
        ))}
      </div>
    </div>
  )
}
