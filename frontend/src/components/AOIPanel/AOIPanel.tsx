import { useState } from 'react'
import { Layers, Package, AlertTriangle, CheckCircle2, Loader2, Download, RefreshCw, X } from 'lucide-react'
import FormatSelector from '../FormatSelector/FormatSelector'
import type { ExportFormat, AOIFeature, Job } from '../../types'
import { downloadUrl } from '../../services/api'
import { clsx } from 'clsx'
import * as turf from '@turf/turf'

/** Area massima accettata in km² */
const MAX_KM2 = 500

interface AOIPanelProps {
  aoi: AOIFeature | null
  areaKm2: number
  job: Job | null
  error: string | null
  onSubmit: (fmt: ExportFormat, symbology: boolean) => void
  onReset: () => void
  onClose: () => void
}

export default function AOIPanel({ aoi, areaKm2, job, error, onSubmit, onReset, onClose }: AOIPanelProps) {
  const [format, setFormat] = useState<ExportFormat>('gpkg')
  const [symbology, setSymbology] = useState(true)

  const areaOver = areaKm2 > MAX_KM2
  const busy = job?.status === 'pending' || job?.status === 'processing'
  const canExport = !!aoi && !areaOver && !busy

  return (
    <aside className="w-80 shrink-0 flex flex-col h-full overflow-y-auto bg-surface-muted border-r border-surface-border">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b border-surface-border bg-white">
        <div className="flex items-start justify-between gap-2">
          <h2 className="font-semibold text-ink flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-500" />
            Export configurator
          </h2>
          {/* X visibile solo su mobile */}
          <button
            type="button"
            onClick={onClose}
            aria-label="Chiudi pannello"
            className="sm:hidden -mr-1 p-1 rounded-lg text-ink-light hover:text-ink hover:bg-surface-subtle transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-ink-light mt-0.5">
          Disegna l&apos;AOI sulla mappa, scegli il formato e avvia l&apos;export.
        </p>
      </div>

      <div className="px-5 py-4 flex flex-col gap-5 flex-1">
        {/* ── AOI status ─────────────────────────────────────────── */}
        <div>
          <p className="text-xs font-semibold tracking-widest text-ink-light uppercase mb-2">
            Area of Interest
          </p>
          {!aoi && areaKm2 === 0 && (
            <div className="rounded-lg border border-dashed border-surface-border bg-white p-4 text-center">
              <p className="text-sm text-ink-muted">
                Usa lo strumento ▱ sulla mappa per disegnare un poligono.
              </p>
            </div>
          )}
          {areaKm2 > 0 && (
            <div
              className={clsx(
                'rounded-lg border p-3 text-sm',
                areaOver
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-green-200 bg-green-50 text-green-800',
              )}
            >
              <div className="flex items-center gap-2 font-medium">
                {areaOver ? (
                  <AlertTriangle className="w-4 h-4" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                {areaKm2.toFixed(1)} km²
                {areaOver && (
                  <span className="ml-auto text-xs font-normal">(max {MAX_KM2} km²)</span>
                )}
              </div>
              {areaOver && (
                <p className="text-xs mt-1">Ridisegna un&apos;area più piccola.</p>
              )}
              {/* Bounding box coords */}
              {aoi && !areaOver && (() => {
                const [w, s, e, n] = turf.bbox(aoi)
                return (
                  <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs text-green-700/80 font-mono">
                    <div><dt className="inline">W </dt><dd className="inline">{w.toFixed(4)}°</dd></div>
                    <div><dt className="inline">E </dt><dd className="inline">{e.toFixed(4)}°</dd></div>
                    <div><dt className="inline">S </dt><dd className="inline">{s.toFixed(4)}°</dd></div>
                    <div><dt className="inline">N </dt><dd className="inline">{n.toFixed(4)}°</dd></div>
                  </dl>
                )
              })()}
            </div>
          )}
        </div>

        {/* ── Format selector ────────────────────────────────────── */}
        <FormatSelector value={format} onChange={setFormat} />

        {/* ── Symbology toggle ───────────────────────────────────── */}
        <div>
          <p className="text-xs font-semibold tracking-widest text-ink-light uppercase mb-2">
            Simbologia QGIS
          </p>
          <label className="flex items-center gap-3 cursor-pointer group">
            <button
              type="button"
              role="switch"
              aria-checked={symbology}
              onClick={() => setSymbology((v) => !v)}
              className={clsx(
                'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                symbology ? 'bg-brand-500' : 'bg-surface-border',
              )}
            >
              <span
                className={clsx(
                  'inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform',
                  symbology ? 'translate-x-4' : 'translate-x-0.5',
                )}
              />
            </button>
            <div>
              <span className="text-sm font-medium text-ink">
                {symbology ? 'Includi file .qml' : 'Solo geodati'}
              </span>
              <p className="text-xs text-ink-light">
                {symbology ? 'ZIP con stili SwissMap-OSM per QGIS' : 'Nessun file di stile allegato'}
              </p>
            </div>
          </label>
        </div>

        {/* ── Submit ─────────────────────────────────────────────── */}
        <button
          type="button"
          disabled={!canExport}
          onClick={() => onSubmit(format, symbology)}
          className={clsx(
            'mt-auto w-full flex items-center justify-center gap-2 rounded-lg px-4 py-3 font-semibold text-sm transition-all',
            canExport
              ? 'bg-brand-500 hover:bg-brand-600 text-white shadow-sm'
              : 'bg-surface-subtle text-ink-light cursor-not-allowed',
          )}
        >
          {busy ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Elaborazione in corso…
            </>
          ) : (
            <>
              <Package className="w-4 h-4" />
              Avvia export
            </>
          )}
        </button>
      </div>

      {/* ── Job status / error ─────────────────────────────────────────── */}
      {(job || error) && (
        <div className="px-5 py-4 border-t border-surface-border bg-white">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              <div className="flex items-center gap-1.5 font-medium mb-0.5">
                <AlertTriangle className="w-4 h-4" />Errore
              </div>
              {error}
            </div>
          )}
          {job && <JobStatusCard job={job} onReset={onReset} />}
        </div>
      )}
    </aside>
  )
}

// ── Inline job card ────────────────────────────────────────────────────────
function JobStatusCard({ job, onReset }: { job: Job; onReset: () => void }) {
  const statusLabel: Record<Job['status'], string> = {
    idle:       'In attesa',
    pending:    'In coda…',
    processing: 'Conversione in corso…',
    ready:      'Pronto per il download',
    failed:     'Errore',
  }

  const statusColor: Record<Job['status'], string> = {
    idle:       'text-ink-light',
    pending:    'text-amber-600',
    processing: 'text-brand-600',
    ready:      'text-green-700',
    failed:     'text-red-600',
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-ink-light font-mono">
          #{job.id.slice(0, 8)}
        </span>
        <button
          type="button"
          onClick={onReset}
          className="text-ink-light hover:text-ink transition-colors"
          title="Nuovo export"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {typeof job.progress === 'number' && (
        <div className="h-1.5 w-full bg-surface-subtle rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      <p className={clsx('text-sm font-medium', statusColor[job.status])}>
        {job.status === 'processing' && <Loader2 className="w-3.5 h-3.5 inline animate-spin mr-1" />}
        {statusLabel[job.status]}
      </p>

      {job.status === 'ready' && job.downloadUrl && (
        <a
          href={downloadUrl(job.id)}
          download
          className="flex items-center justify-center gap-2 w-full rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-2.5 transition-colors"
        >
          <Download className="w-4 h-4" />
          Scarica ZIP ({job.areaKm2.toFixed(1)} km²)
        </a>
      )}

      {job.status === 'failed' && job.errorMessage && (
        <p className="text-xs text-red-600">{job.errorMessage}</p>
      )}
    </div>
  )
}
