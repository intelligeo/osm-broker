// ── Formati di output supportati ───────────────────────────────────────────
export type ExportFormat =
  | 'gpkg'       // GeoPackage
  | 'geojson'    // GeoJSON
  | 'fgdb'       // Esri File Geodatabase
  | 'duckdb'     // DuckDB / GeoParquet

export interface FormatOption {
  id: ExportFormat
  label: string
  description: string
  icon: string
  ext: string
}

// ── Area of Interest ────────────────────────────────────────────────────────
export interface AOIFeature {
  type: 'Feature'
  geometry: {
    type: 'Polygon' | 'MultiPolygon'
    coordinates: number[][][] | number[][][][]
  }
  properties: Record<string, unknown>
}

// ── Job lifecycle ────────────────────────────────────────────────────────────
export type JobStatus =
  | 'idle'
  | 'pending'
  | 'processing'
  | 'ready'
  | 'failed'

export interface Job {
  id: string
  status: JobStatus
  format: ExportFormat
  symbology: boolean
  areaKm2: number
  createdAt: string
  downloadUrl?: string
  errorMessage?: string
  progress?: number   // 0–100
}

// ── Submit payload ───────────────────────────────────────────────────────────
export interface ExportRequest {
  aoi: AOIFeature
  format: ExportFormat
  symbology: boolean
}

// ── Auth / User ────────────────────────────────────────────────────────────
export interface OsmUserPublic {
  osm_id: number
  display_name: string
  account_created: string
}

export interface ExchangeResponse {
  session_token: string
  user: OsmUserPublic
}
